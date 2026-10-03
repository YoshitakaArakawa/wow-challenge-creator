/**
 * Field usage table for structure.ts --usage.
 *
 * Works on the raw TWB text: worksheet shelves, encodings, filters, label / tooltip
 * text and reference lines are spread over many element types, and the parsed object
 * loses the CDATA runs that carry field references in formatted text.
 */

export interface FieldPlace {
  sheet: string;
  places: string[];
}

export interface FieldUsage {
  field: string;
  internalName: string;
  kind: "calculation" | "parameter" | "sheet-local";
  formula?: string;
  references: string[];
  referencedBy: string[];
  usedIn: FieldPlace[];
  unused: boolean;
}

export interface UsageReport {
  fieldUsage: FieldUsage[];
  sheetsNotOnDashboard: string[];
}

const PARAMETERS_DS = "Parameters";

function attr(tag: string, name: string): string | null {
  const m = tag.match(new RegExp(`\\s${name}=(["'])(.*?)\\1`));
  return m ? m[2] : null;
}

function decode(text: string): string {
  return text
    .replace(/&#13;&#10;/g, "\n")
    .replace(/&#10;/g, "\n")
    .replace(/&#13;/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, "&");
}

/** "[ds].[none:Calculation_014:nk]" or "[Parameters].[Parameter 1]" -> "Calculation_014" / "Parameter 1" */
function fieldKeysIn(text: string): string[] {
  const keys = new Set<string>();
  const pattern = /\[([^\]]+)\]\.\[([^\]]+)\]/g;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(text))) {
    const parts = m[2].split(":");
    // Column instances are "derivation:name:type"; bare names have no colon
    keys.add(parts.length >= 3 ? parts.slice(1, -1).join(":") : m[2]);
  }
  return [...keys];
}

/** Bare references inside a formula: "[Calculation_003]", "[Parameters].[Parameter 1]" */
function formulaKeys(formula: string): string[] {
  const keys = new Set<string>();
  for (const k of fieldKeysIn(formula)) keys.add(k);
  const pattern = /\[([^\]]+)\]/g;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(formula))) {
    if (m[1] !== PARAMETERS_DS) keys.add(m[1]);
  }
  return [...keys];
}

interface ColumnDef {
  key: string;
  caption: string;
  formula?: string;
  /** A list parameter's source field ("Add values from") */
  sourceField?: string;
  isParameter: boolean;
}

/** <column ...>...</column> or self-closing <column .../> definitions in a text block */
function columnDefs(block: string, isParameter: boolean): ColumnDef[] {
  const defs: ColumnDef[] = [];
  const pattern = /<column\s[^>]*?(\/>|>[\s\S]*?<\/column>)/g;
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(block))) {
    const open = m[0].match(/^<column\s[^>]*>/)![0];
    const name = attr(open, "name");
    if (!name) continue;
    const calc = m[0].match(/<calculation\s[^>]*>/);
    const formula = calc ? attr(calc[0], "formula") : null;
    if (!isParameter && formula === null) continue;
    defs.push({
      key: name.replace(/^\[|\]$/g, ""),
      caption: attr(open, "caption") || name.replace(/^\[|\]$/g, ""),
      formula: formula !== null ? decode(formula) : undefined,
      sourceField: attr(open, "source-field") ?? undefined,
      isParameter,
    });
  }
  return defs;
}

function blocks(xml: string, tag: string): Array<{ name: string; body: string }> {
  const out: Array<{ name: string; body: string }> = [];
  const pattern = new RegExp(`<${tag}\\s[^>]*>[\\s\\S]*?<\\/${tag}>`, "g");
  let m: RegExpExecArray | null;
  while ((m = pattern.exec(xml))) {
    const open = m[0].match(new RegExp(`^<${tag}\\s[^>]*>`))![0];
    out.push({ name: decode(attr(open, "name") || ""), body: m[0] });
  }
  return out;
}

/** Where each field appears on one worksheet, keyed by field key */
function sheetPlaces(body: string): Map<string, Set<string>> {
  const places = new Map<string, Set<string>>();
  const add = (text: string | null, place: string) => {
    if (!text) return;
    for (const k of fieldKeysIn(decode(text))) {
      if (!places.has(k)) places.set(k, new Set());
      places.get(k)!.add(place);
    }
  };
  // Dependency lists only declare fields; they are not usage
  const view = body.replace(/<datasource-dependencies[\s\S]*?<\/datasource-dependencies>/g, "");

  for (const shelf of ["rows", "cols"]) {
    const m = view.match(new RegExp(`<${shelf}>([\\s\\S]*?)<\\/${shelf}>`));
    if (m) add(m[1], shelf);
  }
  for (const enc of view.match(/<encodings>[\s\S]*?<\/encodings>/g) || []) {
    for (const t of enc.match(/<[a-z-]+\s[^>]*column=(["']).*?\1[^>]*>/g) || []) {
      add(attr(t, "column"), t.match(/^<([a-z-]+)/)![1]);
    }
  }
  for (const t of view.match(/<filter\s[^>]*>/g) || []) add(attr(t, "column"), "filter");
  for (const t of view.match(/<reference-line\s[^>]*>/g) || []) {
    add(attr(t, "value-column"), "reference-line");
  }
  for (const t of view.match(/<(?:sort|computed-sort|manual-sort)\s[^>]*>/g) || []) {
    add(attr(t, "column"), "sort");
  }
  const texts: Array<[RegExp, string]> = [
    [/<customized-label>[\s\S]*?<\/customized-label>/g, "label-text"],
    [/<customized-tooltip>[\s\S]*?<\/customized-tooltip>/g, "tooltip-text"],
    [/<title>[\s\S]*?<\/title>/g, "title"],
  ];
  for (const [pattern, place] of texts) {
    for (const t of view.match(pattern) || []) add(t, place);
  }
  return places;
}

export function buildUsageReport(xml: string): UsageReport {
  const defs = new Map<string, ColumnDef & { kind: FieldUsage["kind"] }>();

  // Data-source level definitions (the <datasources> block, not worksheet dependencies)
  const dsSection = xml.match(/<datasources>[\s\S]*?<\/datasources>/)?.[0] || "";
  for (const ds of blocks(dsSection, "datasource")) {
    const isParam = ds.name === PARAMETERS_DS;
    for (const d of columnDefs(ds.body, isParam)) {
      if (!defs.has(d.key)) defs.set(d.key, { ...d, kind: isParam ? "parameter" : "calculation" });
    }
  }

  const worksheets = blocks(xml, "worksheet");
  // Calculations that exist only inside a worksheet's dependency list
  for (const ws of worksheets) {
    for (const dep of ws.body.match(/<datasource-dependencies[\s\S]*?<\/datasource-dependencies>/g) || []) {
      for (const d of columnDefs(dep, false)) {
        if (!defs.has(d.key)) defs.set(d.key, { ...d, kind: "sheet-local" });
      }
    }
  }

  const caption = (key: string) => defs.get(key)?.caption ?? key;

  const references = new Map<string, string[]>();
  const referencedBy = new Map<string, Set<string>>();
  for (const [key, d] of defs) {
    const text = [d.formula, d.sourceField].filter(Boolean).join(" ");
    const refs = formulaKeys(text).filter((k) => defs.has(k) && k !== key);
    references.set(key, refs);
    for (const r of refs) {
      if (!referencedBy.has(r)) referencedBy.set(r, new Set());
      referencedBy.get(r)!.add(key);
    }
  }

  const usedIn = new Map<string, FieldPlace[]>();
  for (const ws of worksheets) {
    for (const [key, set] of sheetPlaces(ws.body)) {
      if (!defs.has(key)) continue;
      if (!usedIn.has(key)) usedIn.set(key, []);
      usedIn.get(key)!.push({ sheet: ws.name, places: [...set] });
    }
  }

  // Dashboards: worksheet zones carry the sheet name; parameter controls carry param=
  const onDashboard = new Set<string>();
  for (const db of blocks(xml, "dashboard")) {
    for (const z of db.body.match(/<zone\s[^>]*>/g) || []) {
      const name = attr(z, "name");
      if (name) onDashboard.add(decode(name));
      const param = attr(z, "param");
      if (param && param.includes("[Parameters]")) {
        for (const k of fieldKeysIn(decode(param))) {
          if (!usedIn.has(k)) usedIn.set(k, []);
          usedIn.get(k)!.push({ sheet: db.name, places: ["dashboard-control"] });
        }
      }
    }
  }

  const fieldUsage: FieldUsage[] = [...defs.entries()].map(([key, d]) => {
    const places = usedIn.get(key) || [];
    const by = [...(referencedBy.get(key) || [])];
    return {
      field: d.caption,
      internalName: key,
      kind: d.kind,
      formula: d.formula,
      references: (references.get(key) || []).map(caption),
      referencedBy: by.map(caption),
      usedIn: places,
      unused: places.length === 0 && by.length === 0,
    };
  });

  return {
    fieldUsage,
    sheetsNotOnDashboard: worksheets.map((w) => w.name).filter((n) => !onDashboard.has(n)),
  };
}
