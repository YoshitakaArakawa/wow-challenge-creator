import fs from "node:fs";
import path from "node:path";
import { unzip } from "./lib/zip-tools.js";
import {
  readTwb,
  writeTwb,
  findPrimaryDatasourceName,
  insertCalculatedFields,
  insertParameters,
  insertWorksheets,
  insertDashboards,
  insertWindows,
  renderRecipe,
  isolateWorksheetBlock,
  renderDashboard,
} from "./lib/twb-edit.js";
import { repoRootFrom, parsePatchArg, loadPatch } from "./lib/paths.js";
import { WorksheetSpec } from "./lib/patch-types.js";

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
  throw new Error(`No .twb under ${workingDir}. Run unpack-template.ts first.`);
}

function loadRecipe(recipeName: string, repoRoot: string): string {
  const recipePath = path.join(
    repoRoot,
    ".claude",
    "skills",
    "create-workbook",
    "references",
    "chart-recipes",
    `${recipeName}.xml`,
  );
  if (!fs.existsSync(recipePath)) {
    throw new Error(`Recipe not found: ${recipePath}`);
  }
  return fs.readFileSync(recipePath, "utf8");
}

function buildWorksheetXml(spec: WorksheetSpec, repoRoot: string, primaryDsName: string): string {
  if (spec.rawXml) {
    return spec.rawXml;
  }
  if (!spec.recipe) {
    throw new Error(`Worksheet "${spec.name}" has neither recipe nor rawXml`);
  }
  const template = loadRecipe(spec.recipe, repoRoot);
  const params = {
    SHEET_NAME: spec.name,
    DATASOURCE_NAME: primaryDsName,
    ...(spec.params ?? {}),
  };
  if (!params["DATASOURCE_NAME"]) {
    throw new Error(`Worksheet "${spec.name}" missing DATASOURCE_NAME`);
  }
  const rendered = renderRecipe(template, params);
  return isolateWorksheetBlock(rendered);
}

async function main() {
  const repoRoot = repoRootFrom(import.meta.url);
  const patchPath = parsePatchArg(process.argv.slice(2));
  const { patch, workingDir } = loadPatch(patchPath, repoRoot);

  if (!fs.existsSync(workingDir)) {
    throw new Error(`Working directory not found: ${workingDir}. Run unpack-template.ts first.`);
  }

  const mainTwb = findMainTwb(workingDir);
  let xml = readTwb(mainTwb);

  const primary = findPrimaryDatasourceName(xml);
  if (!primary) {
    throw new Error("Could not detect a primary datasource in the template TWB.");
  }

  let calcIdMap: Record<string, string> = {};
  if (patch.calculatedFields?.length) {
    const result = insertCalculatedFields(xml, patch.calculatedFields, primary.name);
    xml = result.xml;
    calcIdMap = result.idMap;
  }

  if (patch.parameters?.length) {
    xml = insertParameters(xml, patch.parameters);
  }

  const worksheetBlocks: string[] = [];
  for (const ws of patch.worksheets ?? []) {
    worksheetBlocks.push(buildWorksheetXml(ws, repoRoot, primary.name));
  }
  if (worksheetBlocks.length) xml = insertWorksheets(xml, worksheetBlocks);

  const dashboardBlocks: string[] = [];
  for (const db of patch.dashboards ?? []) {
    dashboardBlocks.push(renderDashboard(db));
  }
  if (dashboardBlocks.length) xml = insertDashboards(xml, dashboardBlocks);

  const wsNames = (patch.worksheets ?? []).map((w) => w.name);
  const dbNames = (patch.dashboards ?? []).map((d) => d.name);
  if (wsNames.length + dbNames.length > 0) {
    xml = insertWindows(xml, wsNames, dbNames);
  }

  writeTwb(mainTwb, xml);

  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        mainTwb,
        primaryDatasource: primary,
        calculatedFieldsAdded: Object.keys(calcIdMap).length,
        calcIdMap,
        parametersAdded: patch.parameters?.length ?? 0,
        worksheetsAdded: worksheetBlocks.length,
        dashboardsAdded: dashboardBlocks.length,
      },
      null,
      2,
    ) + "\n",
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
