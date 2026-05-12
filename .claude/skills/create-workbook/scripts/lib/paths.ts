import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import { WorkbookPatch, resolveWorkingDir } from "./patch-types.js";

export function repoRootFrom(metaUrl: string): string {
  const dir = path.dirname(fileURLToPath(metaUrl));
  // From either scripts/ or scripts/lib/, walk up to repo root.
  // scripts/lib/ → 5 levels up; scripts/ → 4 levels up. Detect by presence of .git or CLAUDE.md.
  let candidate = dir;
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(candidate, "CLAUDE.md")) || fs.existsSync(path.join(candidate, ".git"))) {
      return candidate;
    }
    candidate = path.dirname(candidate);
  }
  throw new Error(`Repository root not found from ${dir}`);
}

export function parsePatchArg(argv: string[]): string {
  const i = argv.indexOf("--patch");
  if (i === -1 || !argv[i + 1]) {
    throw new Error("Missing --patch <path-to-workbook-patch.json>");
  }
  return argv[i + 1];
}

export function loadPatch(patchPath: string, repoRoot: string): {
  patch: WorkbookPatch;
  patchAbs: string;
  templateAbs: string;
  workingDir: string;
  outputAbs: string;
} {
  const patchAbs = path.isAbsolute(patchPath) ? patchPath : path.resolve(repoRoot, patchPath);
  const patch = JSON.parse(fs.readFileSync(patchAbs, "utf8")) as WorkbookPatch;

  const templateAbs = path.isAbsolute(patch.baseTemplate)
    ? patch.baseTemplate
    : path.resolve(repoRoot, patch.baseTemplate);
  const outputAbs = path.isAbsolute(patch.outputPath)
    ? patch.outputPath
    : path.resolve(repoRoot, patch.outputPath);
  const workingDir = resolveWorkingDir(patch, repoRoot);

  return { patch, patchAbs, templateAbs, workingDir, outputAbs };
}
