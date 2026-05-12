import AdmZip from "adm-zip";
import fs from "node:fs";
import path from "node:path";

export function unzip(zipPath: string, destDir: string): { mainTwb: string | null; files: string[] } {
  if (!fs.existsSync(zipPath)) {
    throw new Error(`Zip not found: ${zipPath}`);
  }
  fs.mkdirSync(destDir, { recursive: true });

  const zip = new AdmZip(zipPath);
  zip.extractAllTo(destDir, true);

  const files: string[] = [];
  let mainTwb: string | null = null;

  const walk = (dir: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(full);
      else {
        files.push(full);
        if (entry.name.toLowerCase().endsWith(".twb")) {
          if (!mainTwb) mainTwb = full;
        }
      }
    }
  };
  walk(destDir);

  return { mainTwb, files };
}

export function zipDirectory(srcDir: string, destZip: string): void {
  fs.mkdirSync(path.dirname(destZip), { recursive: true });
  const zip = new AdmZip();
  const addDir = (dir: string, base: string) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      const rel = path.relative(base, full).split(path.sep).join("/");
      if (entry.isDirectory()) {
        addDir(full, base);
      } else {
        zip.addLocalFile(full, path.dirname(rel) === "." ? "" : path.dirname(rel));
      }
    }
  };
  addDir(srcDir, srcDir);
  zip.writeZip(destZip);
}
