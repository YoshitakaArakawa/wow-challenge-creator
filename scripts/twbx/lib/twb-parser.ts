/**
 * TWB XML Parsing Utilities
 *
 * Shared helpers for parsing Tableau workbook (.twb) XML files.
 * Ported from tableau-public-mcp (https://github.com/wjsutton/tableau-public-mcp)
 */

import { XMLParser } from "fast-xml-parser";

// ============================================
// INTERFACES
// ============================================

export interface WorkbookMetadata {
  version: string;
  sourcePlatform: string;
  sourceBuild: string;
  locale: string;
}

export interface FilterInfo {
  column: string;
  filterClass: string;
  datasource: string;
}

export interface EncodingInfo {
  color: string | null;
  size: string | null;
  detail: string[];
  tooltip: string[];
  shape: string | null;
  text: string | null;
}

// ============================================
// PARSER CONFIGURATION
// ============================================

const TWB_PARSER_OPTIONS = {
  ignoreAttributes: false,
  attributeNamePrefix: "@_",
  allowBooleanAttributes: true,
  parseAttributeValue: false,
  trimValues: true,
  ignoreDeclaration: true,
  processEntities: false,
};

export function createTwbParser(): XMLParser {
  return new XMLParser(TWB_PARSER_OPTIONS);
}

function stripBom(content: string): string {
  if (content.charCodeAt(0) === 0xfeff) {
    return content.slice(1);
  }
  return content;
}

export type ParseTwbResult =
  | { success: true; data: Record<string, unknown> }
  | { success: false; error: string; preview: string };

export function parseTwbContent(content: string): ParseTwbResult {
  try {
    const cleaned = stripBom(content);
    const parser = createTwbParser();
    const parsed = parser.parse(cleaned) as Record<string, unknown>;
    return { success: true, data: parsed };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
      preview: content.substring(0, 200).replace(/\n/g, "\\n"),
    };
  }
}

// ============================================
// HELPER FUNCTIONS
// ============================================

export function decodeHtmlEntities(text: string): string {
  return text
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&")
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&#10;/g, "\n")
    .replace(/&#13;/g, "\r");
}

export function extractFieldReferences(formula: string): string[] {
  const references: string[] = [];
  const fieldPattern = /\[([^\]]+)\]/g;
  let match;
  while ((match = fieldPattern.exec(formula)) !== null) {
    const ref = match[1];
    if (ref !== "Parameters" && !references.includes(ref)) {
      references.push(ref);
    }
  }
  return references;
}

export function parseFieldReference(reference: string): {
  datasource: string | null;
  prefix: string | null;
  fieldName: string;
  suffix: string | null;
} {
  const cleaned = reference.replace(/^\[|\]$/g, "");
  const dsMatch = cleaned.match(/^\[?([^\]]+)\]?\.\[?([^\]]+)\]?$/);
  if (dsMatch) {
    const [, datasource, fieldPart] = dsMatch;
    const parts = fieldPart.split(":");
    if (parts.length === 3) {
      return { datasource, prefix: parts[0] || null, fieldName: parts[1], suffix: parts[2] || null };
    }
    return { datasource, prefix: null, fieldName: fieldPart, suffix: null };
  }
  return { datasource: null, prefix: null, fieldName: cleaned, suffix: null };
}

export function extractFieldName(reference: string): string {
  return parseFieldReference(reference).fieldName;
}

export function ensureArray<T>(value: T | T[] | undefined | null): T[] {
  if (value === undefined || value === null) return [];
  return Array.isArray(value) ? value : [value];
}

export function extractMarkType(table: unknown): string | null {
  if (!table || typeof table !== "object") return null;
  const tableObj = table as Record<string, unknown>;

  const panes = tableObj["panes"];
  if (panes && typeof panes === "object") {
    const panesObj = panes as Record<string, unknown>;
    const paneArray = ensureArray(panesObj["pane"]);
    for (const pane of paneArray) {
      if (pane && typeof pane === "object") {
        const paneObj = pane as Record<string, unknown>;
        const mark = paneObj["mark"];
        if (mark && typeof mark === "object") {
          const markClass = (mark as Record<string, unknown>)["@_class"] as string;
          if (markClass) return markClass;
        }
      }
    }
  }

  const style = tableObj["style"];
  if (style && typeof style === "object") {
    const styleRules = ensureArray((style as Record<string, unknown>)["style-rule"]);
    for (const rule of styleRules) {
      if (rule && typeof rule === "object") {
        const ruleObj = rule as Record<string, unknown>;
        if (ruleObj["@_element"] === "mark") {
          const format = ruleObj["format"];
          if (format && typeof format === "object") {
            const markType = (format as Record<string, unknown>)["@_attr"];
            if (markType === "mark") {
              return ((format as Record<string, unknown>)["@_value"] as string) || null;
            }
          }
        }
      }
    }
  }

  return null;
}

// ============================================
// LOD EXPRESSION HELPERS
// ============================================

export const LOD_PATTERN = /\{(FIXED|INCLUDE|EXCLUDE)\s*([^:]*):([^}]+)\}/gi;

export function containsLodExpression(formula: string): boolean {
  LOD_PATTERN.lastIndex = 0;
  return LOD_PATTERN.test(formula);
}

export function parseLodExpressions(
  formula: string
): Array<{
  lodType: "FIXED" | "INCLUDE" | "EXCLUDE";
  dimensions: string[];
  aggregation: string | null;
  aggregatedExpression: string;
  hasNestedLod: boolean;
}> {
  const results: Array<{
    lodType: "FIXED" | "INCLUDE" | "EXCLUDE";
    dimensions: string[];
    aggregation: string | null;
    aggregatedExpression: string;
    hasNestedLod: boolean;
  }> = [];

  LOD_PATTERN.lastIndex = 0;
  let match;

  while ((match = LOD_PATTERN.exec(formula)) !== null) {
    const [, lodType, dimensionsPart, expression] = match;
    const dimensions: string[] = [];
    const dimPattern = /\[([^\]]+)\]/g;
    let dimMatch;
    while ((dimMatch = dimPattern.exec(dimensionsPart)) !== null) {
      dimensions.push(dimMatch[1]);
    }

    const aggMatch = expression
      .trim()
      .match(/^(SUM|AVG|COUNT|COUNTD|MIN|MAX|MEDIAN|ATTR|STDEV|STDEVP|VAR|VARP)\s*\(/i);

    const innerLodPattern = /\{(FIXED|INCLUDE|EXCLUDE)/i;
    const hasNestedLod = innerLodPattern.test(expression);

    results.push({
      lodType: lodType.toUpperCase() as "FIXED" | "INCLUDE" | "EXCLUDE",
      dimensions,
      aggregation: aggMatch ? aggMatch[1].toUpperCase() : null,
      aggregatedExpression: expression.trim(),
      hasNestedLod,
    });
  }

  return results;
}

export function generateLodExplanation(
  lodType: string,
  dimensions: string[],
  aggregation: string | null,
  expression: string
): { brief: string; detailed: string; useCase: string } {
  const dimList = dimensions.length > 0 ? dimensions.join(", ") : "no dimensions";
  const aggExpr = aggregation
    ? `${aggregation}(...)`
    : expression.substring(0, 50) + (expression.length > 50 ? "..." : "");

  switch (lodType.toUpperCase()) {
    case "FIXED":
      if (dimensions.length === 0) {
        return {
          brief: `Table-level calculation: ${aggExpr}`,
          detailed: `Calculates at entire table level, ignoring ALL dimensions in the view.`,
          useCase: "Percent of total, grand totals, table-level benchmarks",
        };
      }
      if (dimensions.some((d) => /customer|user|client|account|member/i.test(d))) {
        return {
          brief: `Customer-level ${aggregation || "calculation"} by ${dimList}`,
          detailed: `Calculates at the ${dimList} level, regardless of other dimensions in the view.`,
          useCase: "Customer lifetime value, first purchase date, customer cohort analysis",
        };
      }
      return {
        brief: `Fixed calculation at ${dimList} level`,
        detailed: `Calculates fixed at the level of ${dimList}. Result stays constant for each unique combination.`,
        useCase: "Calculations that need to stay at a specific granularity",
      };

    case "INCLUDE":
      return {
        brief: `Include ${dimList} in calculation`,
        detailed: `Calculates INCLUDING ${dimList} in addition to view dimensions. Adds granularity.`,
        useCase: "Getting detailed values before aggregating up (e.g., average of daily totals)",
      };

    case "EXCLUDE":
      return {
        brief: `Exclude ${dimList} from calculation`,
        detailed: `Calculates EXCLUDING ${dimList} from the view's level of detail. Removes granularity.`,
        useCase: "Subtotals, group-level averages, removing a dimension's effect",
      };

    default:
      return {
        brief: `LOD calculation: ${lodType}`,
        detailed: `LOD expression with type ${lodType}`,
        useCase: "Custom level of detail calculation",
      };
  }
}

export function categorizeLodPattern(
  lodType: string,
  dimensions: string[],
  aggregation: string | null
): string {
  const upperType = lodType.toUpperCase();
  const upperAgg = aggregation?.toUpperCase();

  if (upperType === "FIXED" && dimensions.length === 0) return "percentOfTotal";

  if (
    upperType === "FIXED" &&
    dimensions.some((d) => /customer|user|client|account|member/i.test(d)) &&
    (upperAgg === "MIN" || upperAgg === "MAX")
  ) {
    return "customerCohort";
  }

  if (
    upperType === "FIXED" &&
    upperAgg === "SUM" &&
    dimensions.some((d) => /date|month|year|quarter|week|day/i.test(d))
  ) {
    return "runningTotal";
  }

  return "other";
}

// ============================================
// WORKBOOK PARSING HELPERS
// ============================================

export function extractWorkbookMetadata(workbook: Record<string, unknown>): WorkbookMetadata {
  return {
    version: (workbook["@_version"] as string) || "unknown",
    sourcePlatform: (workbook["@_source-platform"] as string) || "unknown",
    sourceBuild: (workbook["@_source-build"] as string) || "unknown",
    locale: (workbook["@_locale"] as string) || "unknown",
  };
}

export function parseShelfContent(shelfContent: string | undefined): string[] {
  if (!shelfContent || typeof shelfContent !== "string") return [];
  const fields: string[] = [];
  const pattern = /\[([^\]]+)\]\.\[([^\]]+)\]/g;
  let match;
  while ((match = pattern.exec(shelfContent)) !== null) {
    const fieldPart = match[2];
    const parts = fieldPart.split(":");
    const fieldName = parts.length === 3 ? parts[1] : fieldPart;
    if (!fields.includes(fieldName)) fields.push(fieldName);
  }
  return fields;
}

export function parseEncodings(encodings: unknown): EncodingInfo {
  const result: EncodingInfo = {
    color: null,
    size: null,
    detail: [],
    tooltip: [],
    shape: null,
    text: null,
  };

  if (!encodings || typeof encodings !== "object") return result;
  const enc = encodings as Record<string, unknown>;

  const color = enc["color"];
  if (color && typeof color === "object") {
    const colorCol = (color as Record<string, unknown>)["@_column"] as string;
    if (colorCol) result.color = extractFieldName(colorCol);
  }

  const size = enc["size"];
  if (size && typeof size === "object") {
    const sizeCol = (size as Record<string, unknown>)["@_column"] as string;
    if (sizeCol) result.size = extractFieldName(sizeCol);
  }

  const lod = ensureArray(enc["lod"]);
  for (const item of lod) {
    if (item && typeof item === "object") {
      const col = (item as Record<string, unknown>)["@_column"] as string;
      if (col) result.detail.push(extractFieldName(col));
    }
  }

  const tooltip = ensureArray(enc["tooltip"]);
  for (const item of tooltip) {
    if (item && typeof item === "object") {
      const col = (item as Record<string, unknown>)["@_column"] as string;
      if (col) result.tooltip.push(extractFieldName(col));
    }
  }

  const shape = enc["shape"];
  if (shape && typeof shape === "object") {
    const shapeCol = (shape as Record<string, unknown>)["@_column"] as string;
    if (shapeCol) result.shape = extractFieldName(shapeCol);
  }

  const text = enc["text"];
  if (text && typeof text === "object") {
    const textCol = (text as Record<string, unknown>)["@_column"] as string;
    if (textCol) result.text = extractFieldName(textCol);
  }

  return result;
}
