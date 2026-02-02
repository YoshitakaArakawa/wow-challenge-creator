/**
 * Get TWBX Workbook Structure
 *
 * Extracts complete workbook architecture from a .twb file.
 * Usage: npx tsx structure.ts <twbFilePath> [--fields]
 */

import * as fs from "fs/promises";
import * as path from "path";
import { fileExists } from "./lib/file-system";
import {
  parseTwbContent,
  ensureArray,
  extractWorkbookMetadata,
  extractMarkType,
  parseShelfContent,
  parseEncodings,
  containsLodExpression,
  EncodingInfo,
} from "./lib/twb-parser";

function parseDataSources(datasources: unknown) {
  const dataSources: any[] = [];
  const parameters: any[] = [];
  let calculatedFieldCount = 0;
  let hasLodCalculations = false;

  for (const ds of ensureArray(datasources)) {
    if (!ds || typeof ds !== "object") continue;
    const dsObj = ds as Record<string, unknown>;
    const dsName = (dsObj["@_name"] as string) || "";
    const dsCaption = (dsObj["@_caption"] as string) || dsName;

    if (dsName === "Parameters") {
      for (const col of ensureArray(dsObj["column"])) {
        if (!col || typeof col !== "object") continue;
        const c = col as Record<string, unknown>;
        parameters.push({
          name: (c["@_caption"] as string) || (c["@_name"] as string) || "",
          datatype: (c["@_datatype"] as string) || "unknown",
          domainType: (c["@_param-domain-type"] as string) || "all",
          currentValue: (c["@_value"] as string) || "",
        });
      }
      continue;
    }

    const connection = dsObj["connection"] as Record<string, unknown> | undefined;
    const connectionType = (connection?.["@_class"] as string) || "unknown";

    const tables: string[] = [];
    let customSqlCount = 0;
    let joinCount = 0;

    const parseRelations = (rel: unknown): void => {
      if (!rel || typeof rel !== "object") return;
      const r = rel as Record<string, unknown>;
      const relType = r["@_type"] as string;
      const relName = r["@_name"] as string;
      if (relType === "table" && relName) tables.push(relName);
      else if (relType === "text") customSqlCount++;
      else if (relType === "join") {
        joinCount++;
        for (const nested of ensureArray(r["relation"])) parseRelations(nested);
      }
    };

    if (connection) {
      for (const rel of ensureArray(connection["relation"])) parseRelations(rel);
    }

    let fieldCount = 0;
    for (const col of ensureArray(dsObj["column"])) {
      if (!col || typeof col !== "object") continue;
      fieldCount++;
      const calc = (col as Record<string, unknown>)["calculation"] as Record<string, unknown> | undefined;
      if (calc) {
        const formula = (calc["@_formula"] as string) || "";
        if (formula) {
          calculatedFieldCount++;
          if (containsLodExpression(formula)) hasLodCalculations = true;
        }
      }
    }

    dataSources.push({
      name: dsName,
      caption: dsCaption,
      connectionType,
      tables,
      hasCustomSql: customSqlCount > 0,
      joinCount,
      fieldCount,
    });
  }

  return { dataSources, parameters, calculatedFieldCount, hasLodCalculations };
}

function parseWorksheets(worksheets: unknown, includeFieldDetails: boolean) {
  const result: any[] = [];
  for (const ws of ensureArray(worksheets)) {
    if (!ws || typeof ws !== "object") continue;
    const wsObj = ws as Record<string, unknown>;
    const wsName = (wsObj["@_name"] as string) || "";
    const table = wsObj["table"] as Record<string, unknown> | undefined;
    const view = table?.["view"] as Record<string, unknown> | undefined;

    const chartType = extractMarkType(table) || "Automatic";

    const dataSources: string[] = [];
    if (view) {
      const viewDs = view["datasources"] as Record<string, unknown> | undefined;
      if (viewDs) {
        for (const d of ensureArray(viewDs["datasource"])) {
          if (d && typeof d === "object") {
            const name = (d as Record<string, unknown>)["@_name"] as string;
            if (name) dataSources.push(name);
          }
        }
      }
    }

    const rowShelf = view ? parseShelfContent(view["rows"] as string | undefined) : [];
    const colShelf = view ? parseShelfContent(view["cols"] as string | undefined) : [];
    const encodings: EncodingInfo = view
      ? parseEncodings(view["encodings"])
      : { color: null, size: null, detail: [], tooltip: [], shape: null, text: null };

    const filters: string[] = [];
    if (view) {
      for (const f of ensureArray(view["filter"])) {
        if (f && typeof f === "object") {
          const col = (f as Record<string, unknown>)["@_column"] as string;
          if (col) {
            const match = col.match(/\.\[([^\]]+)\]$/);
            filters.push(match ? match[1] : col);
          }
        }
      }
    }

    result.push({
      name: wsName,
      chartType,
      dataSource: dataSources[0] || "unknown",
      rowShelf: includeFieldDetails ? rowShelf : rowShelf.slice(0, 3),
      colShelf: includeFieldDetails ? colShelf : colShelf.slice(0, 3),
      colorBy: encodings.color,
      sizeBy: encodings.size,
      detailFields: includeFieldDetails ? encodings.detail : encodings.detail.slice(0, 3),
      filterCount: filters.length,
      filtersApplied: includeFieldDetails ? filters : filters.slice(0, 5),
    });
  }
  return result;
}

function parseDashboards(dashboards: unknown) {
  const result: any[] = [];
  for (const db of ensureArray(dashboards)) {
    if (!db || typeof db !== "object") continue;
    const dbObj = db as Record<string, unknown>;
    const dbName = (dbObj["@_name"] as string) || "";

    const sizeEl = dbObj["size"] as Record<string, unknown> | undefined;
    const size = sizeEl
      ? {
          width: parseInt((sizeEl["@_maxwidth"] as string) || (sizeEl["@_width"] as string) || "0", 10),
          height: parseInt((sizeEl["@_maxheight"] as string) || (sizeEl["@_height"] as string) || "0", 10),
        }
      : null;

    const worksheets: string[] = [];
    let textCount = 0;
    let imageCount = 0;
    let filterCount = 0;

    const countZones = (zones: unknown): void => {
      for (const zone of ensureArray(zones)) {
        if (!zone || typeof zone !== "object") continue;
        const z = zone as Record<string, unknown>;
        const zType = z["@_type"] as string;
        const zName = z["@_name"] as string;
        if (zType === "worksheet" && zName) worksheets.push(zName);
        else if (zType === "text") textCount++;
        else if (zType === "bitmap" || zType === "image") imageCount++;
        else if (zType === "filter" || z["@_is-filter"] === "true") filterCount++;
        if (z["zone"]) countZones(z["zone"]);
      }
    };

    const zones = dbObj["zones"] as Record<string, unknown> | undefined;
    if (zones) countZones(zones["zone"]);

    result.push({
      name: dbName,
      size,
      worksheetsIncluded: worksheets,
      textElementCount: textCount,
      imageCount,
      filterCount,
    });
  }
  return result;
}

async function main() {
  const twbFilePath = process.argv[2];
  const includeFieldDetails = process.argv.includes("--fields");

  if (!twbFilePath) {
    console.error("Usage: npx tsx structure.ts <twbFilePath> [--fields]");
    process.exit(1);
  }

  const absPath = path.resolve(twbFilePath);

  if (!(await fileExists(absPath))) {
    console.log(JSON.stringify({ success: false, error: "TWB file not found", twbFilePath: absPath }));
    process.exit(1);
  }

  if (path.extname(absPath).toLowerCase() !== ".twb") {
    console.log(JSON.stringify({ success: false, error: "Not a .twb file", twbFilePath: absPath }));
    process.exit(1);
  }

  const content = await fs.readFile(absPath, "utf-8");
  const parseResult = parseTwbContent(content);

  if (!parseResult.success) {
    console.log(JSON.stringify({ success: false, error: "Failed to parse TWB XML", detail: parseResult.error }));
    process.exit(1);
  }

  const workbook = (parseResult.data as any)?.workbook;
  if (!workbook) {
    console.log(JSON.stringify({ success: false, error: "Invalid TWB file structure" }));
    process.exit(1);
  }

  const metadata = extractWorkbookMetadata(workbook);
  const { dataSources, parameters, calculatedFieldCount, hasLodCalculations } = parseDataSources(
    workbook.datasources?.datasource
  );
  const worksheets = parseWorksheets(workbook.worksheets?.worksheet, includeFieldDetails);
  const dashboards = parseDashboards(workbook.dashboards?.dashboard);

  const chartTypeCounts: Record<string, number> = {};
  for (const ws of worksheets) {
    chartTypeCounts[ws.chartType] = (chartTypeCounts[ws.chartType] || 0) + 1;
  }

  const result = {
    success: true,
    sourceFile: absPath,
    metadata: {
      version: metadata.version,
      platform: metadata.sourcePlatform,
      build: metadata.sourceBuild,
      locale: metadata.locale,
    },
    summary: {
      dataSourceCount: dataSources.length,
      worksheetCount: worksheets.length,
      dashboardCount: dashboards.length,
      parameterCount: parameters.length,
      calculatedFieldCount,
      totalFieldCount: dataSources.reduce((sum: number, ds: any) => sum + ds.fieldCount, 0),
    },
    dataSources,
    worksheets,
    dashboards,
    parameters,
    insights: {
      chartTypeDistribution: chartTypeCounts,
      hasLodCalculations,
      hasParameters: parameters.length > 0,
      hasMultipleDataSources: dataSources.length > 1,
    },
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
