/**
 * Download Workbook TWBX
 *
 * Downloads a Tableau Public workbook as a .twbx file.
 * Usage: npx tsx download.ts <workbookName>
 *
 * Example: npx tsx download.ts RacialBiasinFootballCommentary
 */

import axios from "axios";
import * as fs from "fs/promises";
import { ensureTempSubdir, getDownloadPath, formatFileSize, parseOutputDir } from "./lib/file-system";

const BASE_URL = "https://public.tableau.com";

interface WorkbookDetails {
  allowDataAccess?: boolean;
  title?: string;
  authorDisplayName?: string;
  viewCount?: number;
  defaultViewRepoUrl?: string;
}

async function main() {
  const workbookName = process.argv[2];
  if (!workbookName) {
    console.error("Usage: npx tsx download.ts <workbookName>");
    console.error("Example: npx tsx download.ts RacialBiasinFootballCommentary");
    process.exit(1);
  }

  // Step 1: Check data access permission
  console.error(`Checking data access permission for: ${workbookName}`);

  let details: WorkbookDetails;
  try {
    const resp = await axios.get<WorkbookDetails>(
      `${BASE_URL}/profile/api/single_workbook/${workbookName}`,
      { timeout: 30000 }
    );
    details = resp.data;
  } catch (error) {
    const result = {
      success: false,
      error: "Failed to fetch workbook details",
      workbookName,
      suggestion: "Check that the workbook name matches the URL path on Tableau Public",
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
    return; // unreachable but helps TS
  }

  if (!details.allowDataAccess) {
    const result = {
      success: false,
      error: "Data download not allowed for this workbook",
      workbookName,
      allowDataAccess: false,
      reason: "The workbook author has disabled data downloads",
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
    return;
  }

  // Step 2: Download the .twbx file
  console.error(`Downloading TWBX...`);

  const downloadUrl = `${BASE_URL}/workbooks/${workbookName}.twb`;
  let twbxBuffer: Buffer;
  try {
    const resp = await axios.get(downloadUrl, {
      responseType: "arraybuffer",
      timeout: 120000,
      headers: { Accept: "*/*" },
    });
    twbxBuffer = Buffer.from(resp.data);
  } catch (error) {
    const result = {
      success: false,
      error: "Failed to download TWBX file",
      workbookName,
      downloadUrl,
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
    return;
  }

  console.error(`Downloaded ${formatFileSize(twbxBuffer.length)}`);

  // Step 3: Save to output directory
  const outputDir = parseOutputDir(process.argv);
  await ensureTempSubdir("downloads", outputDir);
  const filePath = getDownloadPath(workbookName, outputDir);
  await fs.writeFile(filePath, twbxBuffer);

  console.error(`Saved to: ${filePath}`);

  const result = {
    success: true,
    filePath,
    workbookName,
    fileSize: twbxBuffer.length,
    fileSizeFormatted: formatFileSize(twbxBuffer.length),
    downloadedAt: new Date().toISOString(),
    metadata: {
      title: details.title || workbookName,
      author: details.authorDisplayName || "Unknown",
      viewCount: details.viewCount || 0,
    },
    nextStep: "Use unpack.ts with this filePath to extract contents",
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
