/**
 * One round of the refine loop: edit TWB → publish to Tableau Cloud → look at the render.
 *
 *   npx tsx iterate.ts --twbx outputs/{theme}/refine/YYYYWNN.twbx [--views "Dashboard"] [--patch <workbook-patch.json>]
 *
 * Works on outputs/{theme}/refine/:
 *   wb-build/            unpacked workbook being edited (created from --twbx on first run)
 *   YYYYWNN.twbx         repacked from wb-build/ every round, then published with --overwrite --render
 *   render/*.png, publish-result.json, backup/   written by publish-to-cloud/scripts/publish.py
 *   compare.html         copied from ../assets/compare.html when missing
 *
 * --patch additionally runs validate-twb.ts (field-reference checks against the generation patch).
 */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { XMLValidator } from "fast-xml-parser";
import { unzip, zipDirectory } from "./lib/zip-tools.js";
import { repoRootFrom } from "./lib/paths.js";

const REFINE_DIR_NAME = "refine";

interface StepResult {
  step: string;
  ok: boolean;
  summary: string;
}

function arg(argv: string[], name: string): string | undefined {
  const i = argv.indexOf(name);
  return i !== -1 ? argv[i + 1] : undefined;
}

function run(cmd: string, args: string[], cwd: string): { ok: boolean; stdout: string; stderr: string } {
  // npx is a .cmd on Windows and needs a shell; a shell re-splits on spaces, so quote each arg.
  const useShell = process.platform === "win32" && cmd === "npx";
  const finalArgs = useShell ? args.map((a) => (/\s/.test(a) ? `"${a}"` : a)) : args;
  const res = spawnSync(cmd, finalArgs, { cwd, encoding: "utf8", shell: useShell });
  return { ok: res.status === 0, stdout: res.stdout ?? "", stderr: res.stderr ?? "" };
}

function findTwb(dir: string): string | null {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const found = findTwb(full);
      if (found) return found;
    } else if (entry.name.toLowerCase().endsWith(".twb")) {
      return full;
    }
  }
  return null;
}

function main() {
  const argv = process.argv.slice(2);
  const repoRoot = repoRootFrom(import.meta.url);
  const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
  const publishPy = path.resolve(scriptsDir, "../../publish-to-cloud/scripts/publish.py");
  const compareTemplate = path.resolve(scriptsDir, "../assets/compare.html");

  const twbxArg = arg(argv, "--twbx");
  if (!twbxArg) throw new Error("Missing --twbx outputs/{theme}/refine/YYYYWNN.twbx");
  const twbxAbs = path.isAbsolute(twbxArg) ? twbxArg : path.resolve(repoRoot, twbxArg);
  const refineDir = path.dirname(twbxAbs);
  if (path.basename(refineDir) !== REFINE_DIR_NAME) {
    throw new Error(`--twbx must live in outputs/{theme}/${REFINE_DIR_NAME}/ (got ${twbxAbs})`);
  }
  const themeDir = path.dirname(refineDir);
  const buildDir = path.join(refineDir, "wb-build");
  const views = arg(argv, "--views");
  const patchArg = arg(argv, "--patch");

  const steps: StepResult[] = [];

  if (!fs.existsSync(path.join(refineDir, "compare.html")) && fs.existsSync(compareTemplate)) {
    fs.copyFileSync(compareTemplate, path.join(refineDir, "compare.html"));
  }

  if (!fs.existsSync(buildDir)) {
    if (!fs.existsSync(twbxAbs)) throw new Error(`Neither ${buildDir} nor ${twbxAbs} exists.`);
    unzip(twbxAbs, buildDir);
    steps.push({ step: "unpack", ok: true, summary: `${twbxAbs} -> ${buildDir}` });
  }

  const twb = findTwb(buildDir);
  if (!twb) {
    steps.push({ step: "validate", ok: false, summary: `No .twb under ${buildDir}` });
    return finish(steps, null, 1);
  }
  const wellFormed = XMLValidator.validate(fs.readFileSync(twb, "utf8"), { allowBooleanAttributes: true });
  if (wellFormed !== true) {
    const e = wellFormed.err;
    steps.push({ step: "validate", ok: false, summary: `XML not well-formed: line ${e.line}: ${e.msg}` });
    return finish(steps, null, 1);
  }
  let validateSummary = "well-formed";
  if (patchArg) {
    const v = run("npx", ["tsx", path.join(scriptsDir, "validate-twb.ts"), "--patch", patchArg], repoRoot);
    let ok = v.ok;
    try {
      const parsed = JSON.parse(v.stdout);
      ok = parsed.ok !== false;
      const errors = (parsed.issues ?? []).filter((i: { level: string }) => i.level === "error");
      validateSummary = errors.length ? errors.map((e: { message: string }) => e.message).join(" | ") : "no errors";
    } catch {
      validateSummary = (v.stderr || v.stdout).trim();
    }
    if (!ok) {
      steps.push({ step: "validate", ok: false, summary: validateSummary });
      return finish(steps, null, 1);
    }
  }
  steps.push({ step: "validate", ok: true, summary: validateSummary });

  zipDirectory(buildDir, twbxAbs);
  steps.push({ step: "repack", ok: true, summary: twbxAbs });

  const pubArgs = [publishPy, "--twbx", twbxAbs, "--output-dir", themeDir, "--overwrite", "--render"];
  if (views) pubArgs.push("--views", views);
  const p = run("python", pubArgs, repoRoot);
  const resultPath = path.join(refineDir, "publish-result.json");
  const result = fs.existsSync(resultPath) ? JSON.parse(fs.readFileSync(resultPath, "utf8")) : null;
  const pubOk = p.ok && result?.ok === true;
  steps.push({
    step: "publish+render",
    ok: pubOk,
    summary: pubOk ? String(result?.webpageUrl ?? "") : String(result?.error ?? p.stderr.trim()),
  });
  return finish(steps, result, pubOk ? 0 : 1);
}

function finish(steps: StepResult[], result: Record<string, unknown> | null, code: number): void {
  const renders = (result?.renders as Array<{ viewName: string; filePath: string }> | null) ?? [];
  process.stdout.write(
    JSON.stringify(
      {
        ok: code === 0,
        steps,
        webpageUrl: result?.webpageUrl ?? null,
        renders: renders.map((r) => ({ view: r.viewName, png: r.filePath })),
      },
      null,
      2,
    ) + "\n",
  );
  process.exit(code);
}

main();
