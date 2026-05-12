/**
 * File system utilities for TWBX operations
 *
 * Ported from tableau-public-mcp (https://github.com/wjsutton/tableau-public-mcp)
 */

import * as os from "os";
import * as path from "path";
import * as fs from "fs/promises";

const DEFAULT_TEMP_DIR = path.join(os.tmpdir(), "tableau-public-mcp");

/** @deprecated Use getBaseDir() instead */
export const TABLEAU_TEMP_DIR = DEFAULT_TEMP_DIR;

export type FileCategory = "twb" | "data" | "image" | "other";

export interface FileInfo {
  path: string;
  size: number;
  extension: string;
  category: FileCategory;
  isDirectory: boolean;
}

/**
 * Resolve the base directory for intermediate files.
 * If outputDir is provided, uses `{outputDir}/tmp/`.
 * Otherwise falls back to os.tmpdir()/tableau-public-mcp/.
 */
export function getBaseDir(outputDir?: string): string {
  if (outputDir) {
    return path.join(path.resolve(outputDir), "tmp");
  }
  return DEFAULT_TEMP_DIR;
}

export async function ensureTempDir(outputDir?: string): Promise<string> {
  const baseDir = getBaseDir(outputDir);
  await fs.mkdir(baseDir, { recursive: true });
  return baseDir;
}

export async function ensureTempSubdir(subdir: string, outputDir?: string): Promise<string> {
  const baseDir = getBaseDir(outputDir);
  const fullPath = path.join(baseDir, subdir);
  await fs.mkdir(fullPath, { recursive: true });
  return fullPath;
}

export function getExtractionPath(workbookName: string, outputDir?: string): string {
  const baseDir = getBaseDir(outputDir);
  const timestamp = Date.now();
  const safeName = workbookName.replace(/[^a-zA-Z0-9_-]/g, "_");
  return path.join(baseDir, "extracted", `${safeName}_${timestamp}`);
}

export function getDownloadPath(workbookName: string, outputDir?: string): string {
  const baseDir = getBaseDir(outputDir);
  const safeName = workbookName.replace(/[^a-zA-Z0-9_-]/g, "_");
  return path.join(baseDir, "downloads", `${safeName}.twbx`);
}

/**
 * Parse --output-dir from process.argv.
 * Returns the value if found, undefined otherwise.
 */
export function parseOutputDir(argv: string[]): string | undefined {
  const idx = argv.indexOf("--output-dir");
  if (idx !== -1 && idx + 1 < argv.length) {
    return argv[idx + 1];
  }
  return undefined;
}

export function categorizeFile(filePath: string): FileCategory {
  const ext = path.extname(filePath).toLowerCase();
  const normalizedPath = filePath.replace(/\\/g, "/").toLowerCase();

  if (ext === ".twb") return "twb";

  const dataExtensions = [".hyper", ".tde", ".csv", ".xlsx", ".xls", ".json"];
  if (dataExtensions.includes(ext) || normalizedPath.includes("/data/")) return "data";

  const imageExtensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp", ".ico"];
  if (imageExtensions.includes(ext) || normalizedPath.includes("/image/")) return "image";

  return "other";
}

export async function listFilesRecursive(dir: string, baseDir?: string): Promise<FileInfo[]> {
  const base = baseDir || dir;
  const results: FileInfo[] = [];

  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(base, fullPath);

      if (entry.isDirectory()) {
        results.push({ path: relativePath, size: 0, extension: "", category: "other", isDirectory: true });
        const subFiles = await listFilesRecursive(fullPath, base);
        results.push(...subFiles);
      } else {
        const stats = await fs.stat(fullPath);
        const ext = path.extname(entry.name).toLowerCase();
        results.push({
          path: relativePath,
          size: stats.size,
          extension: ext,
          category: categorizeFile(relativePath),
          isDirectory: false,
        });
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dir}:`, error);
  }

  return results;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  const size = bytes / Math.pow(k, i);
  return `${size.toFixed(i > 0 ? 1 : 0)} ${units[i]}`;
}

export async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath, fs.constants.R_OK);
    return true;
  } catch {
    return false;
  }
}
