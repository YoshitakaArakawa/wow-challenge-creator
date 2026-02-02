/**
 * Get TWBX LOD Expressions
 *
 * Extracts and explains Level of Detail expressions from a .twb file.
 * Usage: npx tsx lod-expressions.ts <twbFilePath> [--no-usage]
 */

import * as fs from "fs/promises";
import * as path from "path";
import { fileExists } from "./lib/file-system";
import {
  parseTwbContent,
  ensureArray,
  decodeHtmlEntities,
  parseLodExpressions,
  generateLodExplanation,
  categorizeLodPattern,
} from "./lib/twb-parser";

interface LodExpressionOutput {
  name: string;
  caption: string;
  fullFormula: string;
  datasource: string;
  hidden: boolean;
  lodDetails: {
    type: "FIXED" | "INCLUDE" | "EXCLUDE";
    dimensions: string[];
    aggregation: string | null;
    aggregatedExpression: string;
  };
  explanation: { brief: string; detailed: string; useCase: string };
  hasNestedLod: boolean;
  nestedLods?: { type: string; dimensions: string[]; expression: string }[];
  usageContext?: { usedInCalculations: string[]; isHidden: boolean };
}

function extractLodExpressions(workbook: Record<string, unknown>, includeUsageContext: boolean) {
  const lodExpressions: LodExpressionOutput[] = [];
  const allCalculations = new Map<string, { formula: string; caption: string }>();

  const dsContainer = workbook.datasources as Record<string, unknown> | undefined;
  for (const ds of ensureArray(dsContainer?.datasource)) {
    if (!ds || typeof ds !== "object") continue;
    const dsObj = ds as Record<string, unknown>;
    const dsName = (dsObj["@_name"] as string) || "";
    if (dsName === "Parameters") continue;

    for (const col of ensureArray(dsObj["column"])) {
      if (!col || typeof col !== "object") continue;
      const c = col as Record<string, unknown>;
      const name = ((c["@_name"] as string) || "").replace(/[\[\]]/g, "");
      const caption = (c["@_caption"] as string) || name;
      const hidden = c["@_hidden"] === "true";
      const calc = c["calculation"] as Record<string, unknown> | undefined;
      if (!calc || !calc["@_formula"]) continue;

      const formula = decodeHtmlEntities((calc["@_formula"] as string) || "");
      allCalculations.set(caption, { formula, caption });

      const lodMatches = parseLodExpressions(formula);
      for (const match of lodMatches) {
        const explanation = generateLodExplanation(
          match.lodType,
          match.dimensions,
          match.aggregation,
          match.aggregatedExpression
        );

        let nestedLods: LodExpressionOutput["nestedLods"];
        if (match.hasNestedLod) {
          const nested = parseLodExpressions(match.aggregatedExpression);
          if (nested.length > 0) {
            nestedLods = nested.map((n) => ({
              type: n.lodType,
              dimensions: n.dimensions,
              expression: n.aggregatedExpression,
            }));
          }
        }

        lodExpressions.push({
          name,
          caption,
          fullFormula: formula,
          datasource: dsName,
          hidden,
          lodDetails: {
            type: match.lodType,
            dimensions: match.dimensions,
            aggregation: match.aggregation,
            aggregatedExpression: match.aggregatedExpression,
          },
          explanation,
          hasNestedLod: match.hasNestedLod,
          nestedLods,
          usageContext: includeUsageContext ? { usedInCalculations: [], isHidden: hidden } : undefined,
        });
      }
    }
  }

  return { lodExpressions, allCalculations };
}

function findUsageContext(
  lodExpressions: LodExpressionOutput[],
  allCalculations: Map<string, { formula: string; caption: string }>
) {
  for (const lod of lodExpressions) {
    if (!lod.usageContext) continue;
    const usedIn: string[] = [];
    for (const [calcCaption, calc] of allCalculations) {
      if (calcCaption === lod.caption) continue;
      if (calc.formula.includes(`[${lod.caption}]`) || calc.formula.includes(`[${lod.name}]`)) {
        usedIn.push(calcCaption);
      }
    }
    lod.usageContext.usedInCalculations = usedIn;
  }
}

async function main() {
  const twbFilePath = process.argv[2];
  const includeUsageContext = !process.argv.includes("--no-usage");

  if (!twbFilePath) {
    console.error("Usage: npx tsx lod-expressions.ts <twbFilePath> [--no-usage]");
    process.exit(1);
  }

  const absPath = path.resolve(twbFilePath);
  if (!(await fileExists(absPath))) {
    console.log(JSON.stringify({ success: false, error: "TWB file not found" }));
    process.exit(1);
  }
  if (path.extname(absPath).toLowerCase() !== ".twb") {
    console.log(JSON.stringify({ success: false, error: "Not a .twb file" }));
    process.exit(1);
  }

  const content = await fs.readFile(absPath, "utf-8");
  const parseResult = parseTwbContent(content);
  if (!parseResult.success) {
    console.log(JSON.stringify({ success: false, error: parseResult.error }));
    process.exit(1);
  }

  const workbook = (parseResult.data as any)?.workbook;
  if (!workbook) {
    console.log(JSON.stringify({ success: false, error: "Invalid TWB file structure" }));
    process.exit(1);
  }

  const { lodExpressions, allCalculations } = extractLodExpressions(workbook, includeUsageContext);
  if (includeUsageContext) findUsageContext(lodExpressions, allCalculations);

  if (lodExpressions.length === 0) {
    console.log(
      JSON.stringify({
        success: true,
        message: "No LOD expressions found in this workbook",
        summary: { totalLodExpressions: 0, totalCalculations: allCalculations.size },
      })
    );
    return;
  }

  const patterns = {
    percentOfTotal: [] as string[],
    customerCohort: [] as string[],
    runningTotal: [] as string[],
    other: [] as string[],
  };
  for (const lod of lodExpressions) {
    const cat = categorizeLodPattern(lod.lodDetails.type, lod.lodDetails.dimensions, lod.lodDetails.aggregation);
    if (cat === "percentOfTotal") patterns.percentOfTotal.push(lod.caption);
    else if (cat === "customerCohort") patterns.customerCohort.push(lod.caption);
    else if (cat === "runningTotal") patterns.runningTotal.push(lod.caption);
    else patterns.other.push(lod.caption);
  }

  const byType = {
    fixed: lodExpressions.filter((l) => l.lodDetails.type === "FIXED").length,
    include: lodExpressions.filter((l) => l.lodDetails.type === "INCLUDE").length,
    exclude: lodExpressions.filter((l) => l.lodDetails.type === "EXCLUDE").length,
  };

  const result = {
    success: true,
    sourceFile: absPath,
    summary: {
      totalLodExpressions: lodExpressions.length,
      byType,
      nestedLodCount: lodExpressions.filter((l) => l.hasNestedLod).length,
      tableScopedFixedCount: lodExpressions.filter(
        (l) => l.lodDetails.type === "FIXED" && l.lodDetails.dimensions.length === 0
      ).length,
      hiddenCount: lodExpressions.filter((l) => l.hidden).length,
    },
    lodExpressions: lodExpressions.map((lod) => ({
      caption: lod.caption,
      fullFormula: lod.fullFormula,
      datasource: lod.datasource,
      lodDetails: lod.lodDetails,
      explanation: lod.explanation,
      hasNestedLod: lod.hasNestedLod,
      nestedLods: lod.nestedLods,
      usageContext: lod.usageContext,
    })),
    patterns: {
      percentOfTotal: patterns.percentOfTotal.length > 0 ? patterns.percentOfTotal : undefined,
      customerCohort: patterns.customerCohort.length > 0 ? patterns.customerCohort : undefined,
      runningTotal: patterns.runningTotal.length > 0 ? patterns.runningTotal : undefined,
      other: patterns.other.length > 0 ? patterns.other : undefined,
    },
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
