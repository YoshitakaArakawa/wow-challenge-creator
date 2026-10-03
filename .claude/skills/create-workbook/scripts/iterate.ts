/**
 * One iteration of the edit → publish → look loop.
 *
 *   npx tsx iterate.ts --patch <workbook-patch.json> [--views "Dashboard,Sheet"] [--skip-validate]
 *
 * Takes the TWB currently in the patch's workingDir (edited by hand or by apply-edits.ts),
 * validates it, repacks the .twbx, publishes it to Tableau Cloud with --overwrite --render,
 * and prints where the rendered PNGs landed so the caller can Read them.
 */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { repoRootFrom, parsePatchArg, loadPatch } from "./lib/paths.js";

interface StepResult {
  step: string;
  ok: boolean;
  summary: string;
}

function run(cmd: string, args: string[], cwd: string): { ok: boolean; stdout: string; stderr: string } {
  // npx is a .cmd on Windows and needs a shell; a shell re-splits on spaces, so quote each arg.
  const useShell = process.platform === "win32" && cmd === "npx";
  const finalArgs = useShell ? args.map((a) => (/\s/.test(a) ? `"${a}"` : a)) : args;
  const res = spawnSync(cmd, finalArgs, { cwd, encoding: "utf8", shell: useShell });
  return { ok: res.status === 0, stdout: res.stdout ?? "", stderr: res.stderr ?? "" };
}

function main() {
  const argv = process.argv.slice(2);
  const repoRoot = repoRootFrom(import.meta.url);
  const patchPath = parsePatchArg(argv);
  const { patchAbs, workingDir, outputAbs } = loadPatch(patchPath, repoRoot);
  const scriptsDir = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1"));
  const publishPy = path.resolve(scriptsDir, "../../publish-to-cloud/scripts/publish.py");
  const themeDir = path.dirname(outputAbs);
  const viewsIdx = argv.indexOf("--views");
  const views = viewsIdx !== -1 ? argv[viewsIdx + 1] : undefined;
  const skipValidate = argv.includes("--skip-validate");

  if (!fs.existsSync(workingDir)) {
    throw new Error(`Working directory not found: ${workingDir}. Run unpack-template.ts + apply-edits.ts first.`);
  }

  const steps: StepResult[] = [];

  if (!skipValidate) {
    const v = run("npx", ["tsx", path.join(scriptsDir, "validate-twb.ts"), "--patch", patchAbs], repoRoot);
    let ok = v.ok;
    let summary = v.stdout.trim().split("\n").slice(-1)[0] ?? "";
    try {
      const parsed = JSON.parse(v.stdout);
      ok = parsed.ok !== false;
      const errors = (parsed.issues ?? []).filter((i: { level: string }) => i.level === "error");
      summary = errors.length ? errors.map((e: { message: string }) => e.message).join(" | ") : "no errors";
    } catch {
      summary = (v.stderr || summary).trim();
    }
    steps.push({ step: "validate", ok, summary });
    if (!ok) return finish(steps, null, 1);
  }

  const r = run("npx", ["tsx", path.join(scriptsDir, "repack-twbx.ts"), "--patch", patchAbs], repoRoot);
  steps.push({ step: "repack", ok: r.ok, summary: r.ok ? outputAbs : r.stderr.trim() });
  if (!r.ok) return finish(steps, null, 1);

  const pubArgs = [publishPy, "--twbx", outputAbs, "--output-dir", themeDir, "--overwrite", "--render"];
  if (views) pubArgs.push("--views", views);
  const p = run("python", pubArgs, repoRoot);
  let result: Record<string, unknown> | null = null;
  const resultPath = path.join(themeDir, "tmp", "publish-result.json");
  if (fs.existsSync(resultPath)) {
    result = JSON.parse(fs.readFileSync(resultPath, "utf8"));
  }
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
