import fs from "node:fs";
import path from "node:path";

/** State of the local XSD snapshot in references/schemas/ (a gitignored cache). */
export interface VersionFile {
  _comment?: string;
  repo: string;
  sha: string | null;
  tag: string | null;
  last_checked: string | null;
  last_updated: string | null;
  files: string[];
}

export const REPO_API = "https://api.github.com/repos/tableau/tableau-document-schemas";

export function versionFilePath(repoRoot: string): string {
  return path.join(repoRoot, ".claude", "skills", "create-workbook", "references", "schemas", ".version");
}

/** A fresh clone has no .version; it starts from the empty state. */
export function loadVersion(filePath: string): VersionFile {
  if (!fs.existsSync(filePath)) {
    return { repo: "tableau/tableau-document-schemas", sha: null, tag: null, last_checked: null, last_updated: null, files: [] };
  }
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as VersionFile;
}

export function saveVersion(filePath: string, data: VersionFile): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
}
