import fs from "node:fs";
import path from "node:path";
import { unzip } from "./lib/zip-tools.js";
import { repoRootFrom, parsePatchArg, loadPatch } from "./lib/paths.js";

async function main() {
  const repoRoot = repoRootFrom(import.meta.url);
  const patchPath = parsePatchArg(process.argv.slice(2));
  const { patch, templateAbs, workingDir } = loadPatch(patchPath, repoRoot);

  if (!fs.existsSync(templateAbs)) {
    throw new Error(`Template not found: ${templateAbs}`);
  }

  if (fs.existsSync(workingDir)) {
    fs.rmSync(workingDir, { recursive: true, force: true });
  }
  fs.mkdirSync(workingDir, { recursive: true });

  const { mainTwb, files } = unzip(templateAbs, workingDir);

  if (!mainTwb) {
    throw new Error(`No .twb file found inside ${templateAbs}`);
  }

  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        template: templateAbs,
        workingDir,
        mainTwb,
        extractedFiles: files.length,
        baseTemplate: patch.baseTemplate,
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
