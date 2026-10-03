import fs from "node:fs";
import path from "node:path";
import { findTwb } from "./lib/zip-tools.js";
import {
  readTwb,
  writeTwb,
  findPrimaryDatasourceName,
  insertCalculatedFields,
  insertFolders,
  insertWorksheets,
  insertDashboards,
  insertWindows,
  renderDashboard,
} from "./lib/twb-edit.js";
import { repoRootFrom, parsePatchArg, loadPatch } from "./lib/paths.js";

async function main() {
  const repoRoot = repoRootFrom(import.meta.url);
  const patchPath = parsePatchArg(process.argv.slice(2));
  const { patch, workingDir } = loadPatch(patchPath, repoRoot);

  if (!fs.existsSync(workingDir)) {
    throw new Error(`Working directory not found: ${workingDir}. Run unpack-template.ts first.`);
  }

  const mainTwb = findTwb(workingDir);
  if (!mainTwb) throw new Error(`No .twb under ${workingDir}. Run unpack-template.ts first.`);
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

    const folders: Record<string, string[]> = {};
    for (const f of patch.calculatedFields) {
      if (!f.folder) continue;
      (folders[f.folder] ??= []).push(calcIdMap[f.caption]);
    }
    xml = insertFolders(xml, primary.name, folders);
  }

  const worksheetBlocks: string[] = [];
  for (const ws of patch.worksheets ?? []) {
    if (!ws.rawXml) throw new Error(`Worksheet "${ws.name}" has no rawXml`);
    worksheetBlocks.push(ws.rawXml);
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
