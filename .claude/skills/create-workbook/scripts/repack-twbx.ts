import fs from "node:fs";
import path from "node:path";
import { zipDirectory } from "./lib/zip-tools.js";
import { repoRootFrom, parsePatchArg, loadPatch } from "./lib/paths.js";

async function main() {
  const repoRoot = repoRootFrom(import.meta.url);
  const patchPath = parsePatchArg(process.argv.slice(2));
  const { workingDir, outputAbs } = loadPatch(patchPath, repoRoot);

  if (!fs.existsSync(workingDir)) {
    throw new Error(`Working directory not found: ${workingDir}`);
  }

  fs.mkdirSync(path.dirname(outputAbs), { recursive: true });
  zipDirectory(workingDir, outputAbs);

  const stat = fs.statSync(outputAbs);
  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        outputPath: outputAbs,
        sizeBytes: stat.size,
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
