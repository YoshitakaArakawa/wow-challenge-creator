/**
 * Get TWBX Calculated Fields
 *
 * Extracts calculated fields, parameters, and field definitions from a .twb file.
 * Usage: npx tsx calculated-fields.ts <twbFilePath> [--no-hidden] [--no-deps]
 */

import * as fs from "fs/promises";
import * as path from "path";
import { fileExists } from "./lib/file-system";
import {
  parseTwbContent,
  ensureArray,
  decodeHtmlEntities,
  extractFieldReferences,
} from "./lib/twb-parser";

interface CalculatedField {
  name: string;
  caption: string;
  formula: string;
  datatype: string;
  role: string;
  type: string;
  hidden: boolean;
  datasource: string;
  dependencies: string[];
}

interface Parameter {
  name: string;
  caption: string;
  datatype: string;
  currentValue: string;
  allowedValues: string[];
}

interface SourceField {
  name: string;
  caption: string;
  datatype: string;
  role: string;
  datasource: string;
}

function parseColumns(
  columns: unknown,
  datasourceName: string,
  includeHidden: boolean
): { calculatedFields: CalculatedField[]; sourceFields: SourceField[] } {
  const calculatedFields: CalculatedField[] = [];
  const sourceFields: SourceField[] = [];

  for (const col of ensureArray(columns)) {
    if (!col || typeof col !== "object") continue;
    const c = col as Record<string, unknown>;

    const name = (c["@_name"] as string) || "";
    const caption = (c["@_caption"] as string) || name;
    const datatype = (c["@_datatype"] as string) || "unknown";
    const role = (c["@_role"] as string) || "unknown";
    const type = (c["@_type"] as string) || "unknown";
    const hidden = c["@_hidden"] === "true";

    if (hidden && !includeHidden) continue;

    const calculation = c["calculation"] as Record<string, unknown> | undefined;
    if (calculation) {
      const formula = (calculation["@_formula"] as string) || "";
      if (formula) {
        calculatedFields.push({
          name: name.replace(/[\[\]]/g, ""),
          caption,
          formula: decodeHtmlEntities(formula),
          datatype,
          role,
          type,
          hidden,
          datasource: datasourceName,
          dependencies: extractFieldReferences(formula),
        });
      }
    } else {
      sourceFields.push({
        name: name.replace(/[\[\]]/g, ""),
        caption,
        datatype,
        role,
        datasource: datasourceName,
      });
    }
  }

  return { calculatedFields, sourceFields };
}

function parseParameters(columns: unknown): Parameter[] {
  const parameters: Parameter[] = [];
  for (const col of ensureArray(columns)) {
    if (!col || typeof col !== "object") continue;
    const c = col as Record<string, unknown>;

    const name = (c["@_name"] as string) || "";
    const caption = (c["@_caption"] as string) || name;
    const datatype = (c["@_datatype"] as string) || "unknown";
    const value = (c["@_value"] as string) || "";

    const allowedValues: string[] = [];
    const membersContainer = c["members"] as Record<string, unknown> | undefined;
    if (membersContainer?.["member"]) {
      for (const member of ensureArray(membersContainer["member"])) {
        if (!member || typeof member !== "object") continue;
        const m = member as Record<string, unknown>;
        const alias = (m["@_alias"] as string) || (m["@_value"] as string) || "";
        if (alias && !allowedValues.includes(alias)) allowedValues.push(alias);
      }
    }

    parameters.push({
      name: name.replace(/[\[\]]/g, ""),
      caption,
      datatype,
      currentValue: decodeHtmlEntities(value),
      allowedValues,
    });
  }
  return parameters;
}

async function main() {
  const twbFilePath = process.argv[2];
  const includeHidden = !process.argv.includes("--no-hidden");
  const includeDependencies = !process.argv.includes("--no-deps");

  if (!twbFilePath) {
    console.error("Usage: npx tsx calculated-fields.ts <twbFilePath> [--no-hidden] [--no-deps]");
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

  const allCalculatedFields: CalculatedField[] = [];
  const allSourceFields: SourceField[] = [];
  const allParameters: Parameter[] = [];

  const datasources = workbook.datasources?.datasource;
  if (datasources) {
    for (const ds of ensureArray(datasources)) {
      if (!ds || typeof ds !== "object") continue;
      const dsName = (ds as any)["@_name"] || (ds as any)["@_caption"] || "Unknown";
      const columns = (ds as any).column;

      if (dsName === "Parameters") {
        allParameters.push(...parseParameters(columns));
      } else {
        const { calculatedFields, sourceFields } = parseColumns(columns, dsName, includeHidden);
        allCalculatedFields.push(...calculatedFields);
        allSourceFields.push(...sourceFields);
      }
    }
  }

  // Build dependency analysis
  let dependencyAnalysis: any = undefined;
  if (includeDependencies && allCalculatedFields.length > 0) {
    const calcFieldNames = new Set(allCalculatedFields.map((f) => f.name));
    const fieldDependencies: Record<string, string[]> = {};

    for (const field of allCalculatedFields) {
      const calcDeps = field.dependencies.filter((dep) => calcFieldNames.has(dep) || dep.includes("."));
      if (calcDeps.length > 0) {
        fieldDependencies[field.caption || field.name] = calcDeps;
      }
    }

    const rootFields = allCalculatedFields
      .filter((f) => f.dependencies.every((dep) => !calcFieldNames.has(dep)))
      .map((f) => f.caption || f.name);

    const usedFields = new Set(allCalculatedFields.flatMap((f) => f.dependencies));
    const leafFields = allCalculatedFields
      .filter((f) => !usedFields.has(f.name))
      .map((f) => f.caption || f.name);

    dependencyAnalysis = {
      fieldDependencies,
      rootFields: rootFields.slice(0, 20),
      leafFields: leafFields.slice(0, 20),
      totalDependencyChains: Object.keys(fieldDependencies).length,
    };
  }

  const result = {
    success: true,
    sourceFile: absPath,
    summary: {
      calculatedFieldCount: allCalculatedFields.length,
      parameterCount: allParameters.length,
      sourceFieldCount: allSourceFields.length,
      hiddenFieldCount: allCalculatedFields.filter((f) => f.hidden).length,
    },
    parameters: allParameters.map((p) => ({
      caption: p.caption,
      datatype: p.datatype,
      currentValue: p.currentValue,
      allowedValues: p.allowedValues.length > 0 ? p.allowedValues : undefined,
    })),
    calculatedFields: allCalculatedFields.map((f) => ({
      caption: f.caption,
      formula: f.formula,
      datatype: f.datatype,
      role: f.role,
      hidden: f.hidden || undefined,
      datasource: f.datasource,
      dependencies: includeDependencies && f.dependencies.length > 0 ? f.dependencies : undefined,
    })),
    sourceFields: allSourceFields.slice(0, 50).map((f) => ({
      caption: f.caption,
      datatype: f.datatype,
      role: f.role,
      datasource: f.datasource,
    })),
    dependencyAnalysis,
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
