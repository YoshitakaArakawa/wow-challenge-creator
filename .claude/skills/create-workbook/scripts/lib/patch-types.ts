import path from "node:path";

export interface WorkbookPatch {
  baseTemplate: string;
  outputPath: string;
  workingDir?: string;
  dataSourceSwap?: DataSourceSwap | null;
  parameters?: ParameterSpec[];
  calculatedFields?: CalculatedFieldSpec[];
  worksheets?: WorksheetSpec[];
  dashboards?: DashboardSpec[];
}

export interface DataSourceSwap {
  from: string;
  to: string;
}

export interface ParameterSpec {
  name: string;
  datatype: "string" | "integer" | "real" | "boolean" | "date" | "datetime";
  domainType: "list" | "range" | "all";
  values?: (string | number)[];
  range?: { min: number; max: number; step?: number };
  current: string | number;
}

export interface CalculatedFieldSpec {
  datasource?: string;
  caption: string;
  datatype: "string" | "integer" | "real" | "boolean" | "date" | "datetime";
  role: "measure" | "dimension";
  type?: "quantitative" | "ordinal" | "nominal";
  formula: string;
  defaultFormat?: string;
}

export interface WorksheetSpec {
  name: string;
  recipe?: string;
  params?: Record<string, string>;
  rawXml?: string;
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
  return path.join(path.dirname(outAbs), "tmp", "wb-build");
}
