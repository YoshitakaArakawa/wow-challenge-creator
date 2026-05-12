import fs from "node:fs";
import path from "node:path";
import { XMLParser, XMLValidator } from "fast-xml-parser";
import { repoRootFrom, parsePatchArg, loadPatch } from "./lib/paths.js";

interface Issue {
  level: "error" | "warning";
  message: string;
}

function findMainTwb(workingDir: string): string {
  const stack = [workingDir];
  while (stack.length) {
    const dir = stack.pop()!;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else if (entry.name.toLowerCase().endsWith(".twb")) return full;
    }
  }
  throw new Error(`No .twb under ${workingDir}`);
}

async function main() {
  const repoRoot = repoRootFrom(import.meta.url);
  const patchPath = parsePatchArg(process.argv.slice(2));
  const { patch, workingDir } = loadPatch(patchPath, repoRoot);

  const mainTwb = findMainTwb(workingDir);
  const xml = fs.readFileSync(mainTwb, "utf8");

  const issues: Issue[] = [];

  // 1. XML well-formed?
  const validation = XMLValidator.validate(xml, { allowBooleanAttributes: true });
  if (validation !== true) {
    issues.push({
      level: "error",
      message: `XML not well-formed: ${validation.err.code} at line ${validation.err.line}: ${validation.err.msg}`,
    });
  }

  // 2. Required root tags present?
  for (const tag of ["workbook", "datasources"]) {
    if (!new RegExp(`<${tag}\\b`).test(xml)) {
      issues.push({ level: "error", message: `Missing required element: <${tag}>` });
    }
  }

  // 3. Each declared worksheet/dashboard has a corresponding <window>?
  for (const ws of patch.worksheets ?? []) {
    const re = new RegExp(`<window\\b[^>]*class=['"]worksheet['"][^>]*name=['"]${escapeRe(ws.name)}['"]`);
    if (!re.test(xml)) {
      issues.push({ level: "warning", message: `<window> not found for worksheet "${ws.name}"` });
    }
  }
  for (const db of patch.dashboards ?? []) {
    const re = new RegExp(`<window\\b[^>]*class=['"]dashboard['"][^>]*name=['"]${escapeRe(db.name)}['"]`);
    if (!re.test(xml)) {
      issues.push({ level: "warning", message: `<window> not found for dashboard "${db.name}"` });
    }
  }

  // 4. Parse → tree (round-trip sanity)
  try {
    const parser = new XMLParser({ ignoreAttributes: false, attributeNamePrefix: "@_" });
    parser.parse(xml);
  } catch (err) {
    issues.push({ level: "error", message: `Parser failed: ${(err as Error).message}` });
  }

  // 5. Calculated field caption uniqueness within a datasource (best-effort).
  if (patch.calculatedFields) {
    const seen = new Set<string>();
    for (const f of patch.calculatedFields) {
      const k = `${f.datasource ?? "<primary>"}|${f.caption}`;
      if (seen.has(k)) issues.push({ level: "warning", message: `Duplicate calc caption: ${k}` });
      seen.add(k);
    }
  }

  const errors = issues.filter((i) => i.level === "error");
  const warnings = issues.filter((i) => i.level === "warning");

  process.stdout.write(
    JSON.stringify(
      {
        ok: errors.length === 0,
        mainTwb,
        errors,
        warnings,
      },
      null,
      2,
    ) + "\n",
  );

  if (errors.length > 0) process.exit(2);
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
