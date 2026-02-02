/**
 * Unpack TWBX
 *
 * Extracts contents from a .twbx ZIP archive.
 * Usage: npx tsx unpack.ts <twbxFilePath>
 */

import AdmZip from "adm-zip";
import * as fs from "fs/promises";
import * as path from "path";
import {
  fileExists,
  getExtractionPath,
  listFilesRecursive,
  categorizeFile,
  formatFileSize,
  parseOutputDir,
} from "./lib/file-system";

async function main() {
  const twbxFilePath = process.argv[2];
  if (!twbxFilePath) {
    console.error("Usage: npx tsx unpack.ts <twbxFilePath>");
    process.exit(1);
  }

  const absPath = path.resolve(twbxFilePath);

  // Validate file
  if (!(await fileExists(absPath))) {
    console.log(JSON.stringify({ success: false, error: "File not found", filePath: absPath }));
    process.exit(1);
  }

  const ext = path.extname(absPath).toLowerCase();
  if (ext !== ".twbx") {
    console.log(
      JSON.stringify({ success: false, error: "Not a .twbx file", filePath: absPath, extension: ext })
    );
    process.exit(1);
  }

  // Extract
  console.error(`Extracting: ${absPath}`);
  const workbookName = path.basename(absPath, ".twbx");
  const outputDir = parseOutputDir(process.argv);
  const extractDir = getExtractionPath(workbookName, outputDir);
  await fs.mkdir(extractDir, { recursive: true });

  try {
    const zip = new AdmZip(absPath);
    zip.extractAllTo(extractDir, true);
  } catch (error) {
    console.log(
      JSON.stringify({
        success: false,
        error: "Failed to extract TWBX",
        detail: error instanceof Error ? error.message : String(error),
      })
    );
    process.exit(1);
  }

  // Inventory
  const files = await listFilesRecursive(extractDir);
  const fileList = files.filter((f) => !f.isDirectory);

  let mainTwbPath: string | null = null;
  const inventory = {
    twb: [] as string[],
    data: [] as string[],
    image: [] as string[],
    other: [] as string[],
  };

  let totalSize = 0;

  for (const file of fileList) {
    const fullPath = path.join(extractDir, file.path);
    const category = categorizeFile(file.path);
    totalSize += file.size;

    if (category === "twb") {
      inventory.twb.push(file.path);
      if (!mainTwbPath) mainTwbPath = fullPath;
    } else if (category === "data") {
      inventory.data.push(file.path);
    } else if (category === "image") {
      inventory.image.push(file.path);
    } else {
      inventory.other.push(file.path);
    }
  }

  const result = {
    success: true,
    extractionPath: extractDir,
    mainTwbPath,
    fileCount: fileList.length,
    totalSize: formatFileSize(totalSize),
    inventory,
    nextStep: "Use structure.ts, calculated-fields.ts etc. with mainTwbPath",
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
