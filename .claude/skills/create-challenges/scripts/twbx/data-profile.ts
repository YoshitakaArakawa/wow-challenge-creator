/**
 * Get TWBX Data Profile
 *
 * Profiles data files in an extracted TWBX package.
 * Extracts column names from CSV, Excel, JSON and inventories images.
 * Usage: npx tsx data-profile.ts <extractionPath> [--no-images]
 */

import * as fs from "fs/promises";
import * as path from "path";
import { fileExists, listFilesRecursive, categorizeFile, formatFileSize } from "./lib/file-system";

interface CsvProfile {
  fileName: string;
  filePath: string;
  columns: string[];
  rowCount: number;
  fileSize: string;
}

interface ExcelProfile {
  fileName: string;
  filePath: string;
  sheets: { name: string; columns: string[] }[];
  fileSize: string;
}

interface JsonProfile {
  fileName: string;
  filePath: string;
  topLevelKeys: string[];
  isArray: boolean;
  itemCount?: number;
  fileSize: string;
}

interface ImageInfo {
  fileName: string;
  filePath: string;
  extension: string;
  fileSize: string;
}

interface UnsupportedFile {
  fileName: string;
  filePath: string;
  format: string;
  reason: string;
}

async function profileCsv(filePath: string): Promise<CsvProfile> {
  const content = await fs.readFile(filePath, "utf-8");
  const lines = content.split(/\r?\n/).filter((l) => l.trim());
  const firstLine = lines[0] || "";

  // Simple CSV header parsing (handles quoted fields)
  const columns: string[] = [];
  let current = "";
  let inQuotes = false;
  for (const char of firstLine) {
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      columns.push(current.trim().replace(/^"|"$/g, ""));
      current = "";
    } else {
      current += char;
    }
  }
  if (current) columns.push(current.trim().replace(/^"|"$/g, ""));

  const stats = await fs.stat(filePath);

  return {
    fileName: path.basename(filePath),
    filePath,
    columns,
    rowCount: Math.max(0, lines.length - 1),
    fileSize: formatFileSize(stats.size),
  };
}

async function profileExcel(filePath: string): Promise<ExcelProfile> {
  // Dynamic import to handle optional dependency
  let XLSX: any;
  try {
    XLSX = await import("xlsx");
  } catch {
    const stats = await fs.stat(filePath);
    return {
      fileName: path.basename(filePath),
      filePath,
      sheets: [{ name: "(xlsx module not installed)", columns: [] }],
      fileSize: formatFileSize(stats.size),
    };
  }

  const workbook = XLSX.readFile(filePath, { sheetRows: 2 });
  const sheets: { name: string; columns: string[] }[] = [];

  for (const sheetName of workbook.SheetNames) {
    const sheet = workbook.Sheets[sheetName];
    const data = XLSX.utils.sheet_to_json(sheet, { header: 1 }) as string[][];
    const headers = data[0] || [];
    sheets.push({ name: sheetName, columns: headers.map(String) });
  }

  const stats = await fs.stat(filePath);
  return {
    fileName: path.basename(filePath),
    filePath,
    sheets,
    fileSize: formatFileSize(stats.size),
  };
}

async function profileJson(filePath: string): Promise<JsonProfile> {
  const content = await fs.readFile(filePath, "utf-8");
  const stats = await fs.stat(filePath);
  let parsed: unknown;

  try {
    parsed = JSON.parse(content);
  } catch {
    return {
      fileName: path.basename(filePath),
      filePath,
      topLevelKeys: ["(invalid JSON)"],
      isArray: false,
      fileSize: formatFileSize(stats.size),
    };
  }

  if (Array.isArray(parsed)) {
    const first = parsed[0];
    return {
      fileName: path.basename(filePath),
      filePath,
      topLevelKeys: first && typeof first === "object" ? Object.keys(first) : [],
      isArray: true,
      itemCount: parsed.length,
      fileSize: formatFileSize(stats.size),
    };
  }

  return {
    fileName: path.basename(filePath),
    filePath,
    topLevelKeys: typeof parsed === "object" && parsed !== null ? Object.keys(parsed) : [],
    isArray: false,
    fileSize: formatFileSize(stats.size),
  };
}

async function main() {
  const extractionPath = process.argv[2];
  const includeImages = !process.argv.includes("--no-images");

  if (!extractionPath) {
    console.error("Usage: npx tsx data-profile.ts <extractionPath> [--no-images]");
    process.exit(1);
  }

  const absPath = path.resolve(extractionPath);
  if (!(await fileExists(absPath))) {
    console.log(JSON.stringify({ success: false, error: "Extraction path not found" }));
    process.exit(1);
  }

  const stats = await fs.stat(absPath);
  if (!stats.isDirectory()) {
    console.log(JSON.stringify({ success: false, error: "Path is not a directory" }));
    process.exit(1);
  }

  const files = await listFilesRecursive(absPath);
  const fileList = files.filter((f) => !f.isDirectory);

  const csvFiles: string[] = [];
  const excelFiles: string[] = [];
  const jsonFiles: string[] = [];
  const imageFiles: string[] = [];
  const unsupportedFiles: UnsupportedFile[] = [];

  for (const file of fileList) {
    const fullPath = path.join(absPath, file.path);
    const ext = path.extname(file.path).toLowerCase();

    if (ext === ".csv") csvFiles.push(fullPath);
    else if (ext === ".xlsx" || ext === ".xls") excelFiles.push(fullPath);
    else if (ext === ".json") jsonFiles.push(fullPath);
    else if (ext === ".hyper") {
      unsupportedFiles.push({
        fileName: path.basename(file.path),
        filePath: fullPath,
        format: "hyper",
        reason: "Hyper files require the Tableau Hyper API to read",
      });
    } else if (ext === ".tde") {
      unsupportedFiles.push({
        fileName: path.basename(file.path),
        filePath: fullPath,
        format: "tde",
        reason: "TDE files require the Tableau SDK to read",
      });
    } else if (categorizeFile(file.path) === "image") {
      imageFiles.push(fullPath);
    }
  }

  console.error(
    `Found: ${csvFiles.length} CSV, ${excelFiles.length} Excel, ${jsonFiles.length} JSON, ${imageFiles.length} images, ${unsupportedFiles.length} unsupported`
  );

  const csvProfiles = await Promise.all(csvFiles.map(profileCsv));
  const excelProfiles = await Promise.all(excelFiles.map(profileExcel));
  const jsonProfiles = await Promise.all(jsonFiles.map(profileJson));

  let imageInventory: ImageInfo[] | undefined;
  if (includeImages && imageFiles.length > 0) {
    imageInventory = await Promise.all(
      imageFiles.map(async (f) => {
        const s = await fs.stat(f);
        return {
          fileName: path.basename(f),
          filePath: f,
          extension: path.extname(f).toLowerCase(),
          fileSize: formatFileSize(s.size),
        };
      })
    );
  }

  const result = {
    success: true,
    extractionPath: absPath,
    summary: {
      dataFileCount: csvFiles.length + excelFiles.length + jsonFiles.length + unsupportedFiles.length,
      imageFileCount: imageFiles.length,
      csvCount: csvProfiles.length,
      excelCount: excelProfiles.length,
      jsonCount: jsonProfiles.length,
      unsupportedCount: unsupportedFiles.length,
    },
    dataFiles: {
      csv: csvProfiles,
      excel: excelProfiles,
      json: jsonProfiles,
      unsupported: unsupportedFiles,
    },
    imageInventory,
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
