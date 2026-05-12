/**
 * String-based TWB XML editing helpers.
 *
 * TWB XML is hand-edited by Tableau Desktop and is sensitive to attribute order, whitespace,
 * and undocumented invariants. To minimise the risk of breaking it via parse/serialize round-trips,
 * we insert pre-rendered XML fragments at well-known anchor positions and leave the rest of the
 * file untouched.
 */

import fs from "node:fs";
import {
  CalculatedFieldSpec,
  DashboardSpec,
  ParameterSpec,
  WorksheetSpec,
} from "./patch-types.js";

export function escapeXml(value: string): string {
  return value
    .replace(/&(?!(?:amp|lt|gt|quot|apos);)/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function readTwb(twbPath: string): string {
  const buf = fs.readFileSync(twbPath);
  // Strip BOM if present.
  const start = buf.length >= 3 && buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf ? 3 : 0;
  return buf.toString("utf8", start);
}

export function writeTwb(twbPath: string, xml: string): void {
  fs.writeFileSync(twbPath, xml, "utf8");
}

/**
 * Find the name attribute of the primary (non-Parameters) datasource. Returns null if none found.
 */
export function findPrimaryDatasourceName(xml: string): { name: string; caption: string } | null {
  const re = /<datasource\b[^>]*?\bname=['"]([^'"]+)['"][^>]*>/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(xml))) {
    const segment = match[0];
    const name = match[1];
    if (name === "Parameters") continue;
    const captionMatch = /\bcaption=['"]([^'"]+)['"]/.exec(segment);
    return { name, caption: captionMatch?.[1] ?? name };
  }
  return null;
}

/**
 * Insert content immediately before the *first* closing tag matching `</tagName>` that follows
 * the supplied `anchorRegex` match. If `anchorRegex` is undefined the very first `</tagName>` is used.
 */
function insertBeforeClosingTag(
  xml: string,
  tagName: string,
  content: string,
  anchorRegex?: RegExp,
): string {
  const closeRe = new RegExp(`</${tagName}>`, "g");
  let startIndex = 0;
  if (anchorRegex) {
    const m = anchorRegex.exec(xml);
    if (!m) throw new Error(`Anchor not found for </${tagName}>: ${anchorRegex.source}`);
    startIndex = m.index + m[0].length;
  }
  closeRe.lastIndex = startIndex;
  const close = closeRe.exec(xml);
  if (!close) throw new Error(`Closing tag </${tagName}> not found from offset ${startIndex}`);
  return xml.slice(0, close.index) + content + xml.slice(close.index);
}

/**
 * Insert `<column>` calculated field elements into the named datasource block.
 */
export function insertCalculatedFields(
  xml: string,
  fields: CalculatedFieldSpec[],
  primaryDatasourceName: string,
  startingId = 1,
): { xml: string; idMap: Record<string, string> } {
  const idMap: Record<string, string> = {};
  let nextId = startingId;
  let mutated = xml;

  for (const field of fields) {
    const dsName = field.datasource ?? primaryDatasourceName;
    const calcId = `Calculation_${String(nextId++).padStart(3, "0")}`;
    idMap[field.caption] = `[${calcId}]`;

    const attrs = [
      `caption='${escapeXml(field.caption)}'`,
      `datatype='${field.datatype}'`,
      `name='[${calcId}]'`,
      `role='${field.role}'`,
      `type='${field.type ?? (field.role === "measure" ? "quantitative" : "nominal")}'`,
    ];
    if (field.defaultFormat) attrs.push(`default-format='${escapeXml(field.defaultFormat)}'`);

    const columnXml =
      `\n    <column ${attrs.join(" ")}>\n` +
      `      <calculation class='tableau' formula='${escapeXml(field.formula)}'/>\n` +
      `    </column>`;

    const anchor = new RegExp(`<datasource\\b[^>]*\\bname=['"]${dsName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}['"][^>]*>`);
    mutated = insertBeforeClosingTag(mutated, "datasource", columnXml, anchor);
  }

  return { xml: mutated, idMap };
}

/**
 * Build a `<column>` parameter element. Inserted into the Parameters datasource block.
 */
function buildParameterXml(p: ParameterSpec): string {
  const quotedValue = typeof p.current === "string" ? `&quot;${escapeXml(p.current)}&quot;` : String(p.current);
  const attrs = [
    `caption='${escapeXml(p.name)}'`,
    `datatype='${p.datatype}'`,
    `name='[Parameter ${escapeXml(p.name)}]'`,
    `param-domain-type='${p.domainType}'`,
    `role='measure'`,
    `type='${p.datatype === "integer" || p.datatype === "real" ? "quantitative" : "nominal"}'`,
    `value='${quotedValue}'`,
  ];

  let inner = "";
  if (p.domainType === "list" && p.values) {
    const members = p.values
      .map((v) => {
        const escaped = typeof v === "string" ? `&quot;${escapeXml(v)}&quot;` : String(v);
        const alias = typeof v === "string" ? escapeXml(v) : String(v);
        return `        <member alias='${alias}' value='${escaped}'/>`;
      })
      .join("\n");
    inner = `\n      <members>\n${members}\n      </members>`;
  } else if (p.domainType === "range" && p.range) {
    const step = p.range.step ?? 1;
    inner = `\n      <range granularity='${step}' min='${p.range.min}' max='${p.range.max}'/>`;
  }

  return `\n    <column ${attrs.join(" ")}>${inner}\n    </column>`;
}

export function insertParameters(xml: string, parameters: ParameterSpec[]): string {
  if (parameters.length === 0) return xml;
  const anchor = /<datasource\b[^>]*\bname=['"]Parameters['"][^>]*>/;
  let mutated = xml;
  for (const p of parameters) {
    mutated = insertBeforeClosingTag(mutated, "datasource", buildParameterXml(p), anchor);
  }
  return mutated;
}

/**
 * Insert worksheet XML blocks before `</worksheets>`. Creates the `<worksheets>` container if missing.
 */
export function insertWorksheets(xml: string, blocks: string[]): string {
  if (blocks.length === 0) return xml;
  const joined = "\n" + blocks.map((b) => b.replace(/^\n*/, "")).join("\n") + "\n";

  if (/<worksheets\b/.test(xml)) {
    return insertBeforeClosingTag(xml, "worksheets", joined);
  }
  return xml.replace("</datasources>", `</datasources>\n  <worksheets>${joined}</worksheets>`);
}

/**
 * Insert dashboard XML blocks before `</dashboards>`. Creates the container if missing.
 */
export function insertDashboards(xml: string, blocks: string[]): string {
  if (blocks.length === 0) return xml;
  const joined = "\n" + blocks.map((b) => b.replace(/^\n*/, "")).join("\n") + "\n";

  if (/<dashboards\b/.test(xml)) {
    return insertBeforeClosingTag(xml, "dashboards", joined);
  }
  // Place after worksheets (or after datasources if no worksheets).
  if (/<\/worksheets>/.test(xml)) {
    return xml.replace("</worksheets>", `</worksheets>\n  <dashboards>${joined}</dashboards>`);
  }
  return xml.replace("</datasources>", `</datasources>\n  <dashboards>${joined}</dashboards>`);
}

/**
 * Append `<window>` entries for new worksheets/dashboards. Tableau Desktop is more forgiving when
 * these are present even with empty `<cards/>`.
 */
export function insertWindows(
  xml: string,
  worksheetNames: string[],
  dashboardNames: string[],
): string {
  if (worksheetNames.length + dashboardNames.length === 0) return xml;
  const parts: string[] = [];
  for (const name of worksheetNames) {
    parts.push(`    <window class='worksheet' name='${escapeXml(name)}'><cards/></window>`);
  }
  for (const name of dashboardNames) {
    parts.push(`    <window class='dashboard' name='${escapeXml(name)}' maximized='true'><cards/></window>`);
  }
  const block = "\n" + parts.join("\n") + "\n";

  if (/<windows\b/.test(xml)) {
    return insertBeforeClosingTag(xml, "windows", block);
  }
  return xml.replace("</workbook>", `  <windows>${block}  </windows>\n</workbook>`);
}

/**
 * Render dashboard XML.
 */
export function renderDashboard(spec: DashboardSpec): string {
  const { name, size, sheets } = spec;
  const zonePerSheet = Math.floor(100000 / Math.max(1, sheets.length));
  const zones = sheets
    .map((sheetName, idx) => {
      const y = idx * zonePerSheet;
      const h = idx === sheets.length - 1 ? 100000 - y : zonePerSheet;
      return `      <zone h='${h}' id='${idx + 2}' name='${escapeXml(sheetName)}' w='100000' x='0' y='${y}'/>`;
    })
    .join("\n");

  return (
    `  <dashboard name='${escapeXml(name)}'>\n` +
    `    <style/>\n` +
    `    <size maxheight='${size.height}' maxwidth='${size.width}' minheight='${size.height}' minwidth='${size.width}'/>\n` +
    `    <zones>\n` +
    `      <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>\n` +
    zones +
    `\n      </zone>\n` +
    `    </zones>\n` +
    `    <devicelayouts/>\n` +
    `  </dashboard>`
  );
}

/**
 * Apply `{{KEY}}` placeholder substitution + derived helpers (FIELD_NAME stripped of brackets,
 * TITLE-cased aggregation) to a recipe template.
 */
export function renderRecipe(template: string, params: Record<string, string>): string {
  const expanded: Record<string, string> = { ...params };

  for (const [key, value] of Object.entries(params)) {
    // Derive [FieldName] → FieldName (strip brackets).
    if (key.startsWith("FIELD_") && !key.endsWith("_NAME") && !key.endsWith("_GRANULARITY") && !key.endsWith("_PREFIX")) {
      const stripped = value.replace(/^\[|\]$/g, "");
      expanded[`${key}_NAME`] = stripped;
    }
    // Title-case aggregator (sum → Sum) for derivation attribute.
    if (key.startsWith("AGG_") && !key.endsWith("_TITLE")) {
      expanded[`${key}_TITLE`] = titleCase(value);
    }
    if (key === "FIELD_X_GRANULARITY") {
      expanded["FIELD_X_GRANULARITY_TITLE"] = titleCase(value);
    }
  }

  return template.replace(/\{\{(\w+)\}\}/g, (_match, key: string) => {
    if (expanded[key] === undefined) {
      throw new Error(`Recipe placeholder {{${key}}} has no value`);
    }
    return expanded[key];
  });
}

function titleCase(value: string): string {
  if (!value) return value;
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

export function isolateWorksheetBlock(rendered: string): string {
  // Strip XML comment header from recipe files so the rendered string is pure worksheet XML.
  return rendered.replace(/^\s*<!--[\s\S]*?-->\s*/, "").trim();
}
