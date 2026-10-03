import path from "node:path";

export interface WorkbookPatch {
  baseTemplate: string;
  outputPath: string;
  workingDir?: string;
  calculatedFields?: CalculatedFieldSpec[];
  worksheets?: WorksheetSpec[];
  dashboards?: DashboardSpec[];
}

export interface CalculatedFieldSpec {
  datasource?: string;
  caption: string;
  datatype: "string" | "integer" | "real" | "boolean" | "date" | "datetime";
  role: "measure" | "dimension";
  type?: "quantitative" | "ordinal" | "nominal";
  /** May contain newlines and `//` comments; they are encoded as &#13;&#10; in the TWB. */
  formula: string;
  defaultFormat?: string;
  /** Data pane folder name (e.g. "2_Stats"). Omitted = no folder. */
  folder?: string;
}

export interface WorksheetSpec {
  name: string;
  /** Complete `<worksheet name='...'>...</worksheet>` element. */
  rawXml: string;
}

export interface DashboardSpec {
  name: string;
  size: { width: number; height: number };
  sheets: string[];
}

export function resolveWorkingDir(patch: WorkbookPatch, repoRoot: string): string {
  if (patch.workingDir) {
    return path.isAbsolute(patch.workingDir) ? patch.workingDir : path.resolve(repoRoot, patch.workingDir);
  }
  const outAbs = path.isAbsolute(patch.outputPath) ? patch.outputPath : path.resolve(repoRoot, patch.outputPath);
  const outDir = path.dirname(outAbs);
  // outputs/{theme}/refine/YYYYWNN.twbx → refine/wb-build (shared with iterate.ts); legacy layouts keep tmp/wb-build.
  return path.basename(outDir) === "refine" ? path.join(outDir, "wb-build") : path.join(outDir, "tmp", "wb-build");
}
