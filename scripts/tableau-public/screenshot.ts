/**
 * Tableau Public Screenshot
 *
 * Downloads a full-size PNG screenshot of a Tableau Public visualization.
 * Usage: npx tsx scripts/tableau-public/screenshot.ts <tableauPublicUrl>
 *
 * Example:
 *   npx tsx scripts/tableau-public/screenshot.ts https://public.tableau.com/app/profile/yoshitaka6076/viz/WOW2026W5/WOW2026W4
 *
 * The URL is parsed to extract workbookUrl and viewName automatically.
 * Output: JSON with the local file path of the saved screenshot.
 */

import axios from "axios";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";

const BASE_URL = "https://public.tableau.com";

function parseOutputDir(argv: string[]): string | undefined {
  const idx = argv.indexOf("--output-dir");
  if (idx !== -1 && idx + 1 < argv.length) {
    return argv[idx + 1];
  }
  return undefined;
}

function parseTableauUrl(url: string): { workbookUrl: string; viewName: string } {
  // Expected format:
  //   https://public.tableau.com/app/profile/{user}/viz/{workbook}/{view}
  //   or just: {workbook}/{view}
  const match = url.match(/\/viz\/([^/]+)\/([^/?#]+)/);
  if (match) {
    return { workbookUrl: match[1], viewName: match[2] };
  }

  // Fallback: treat as "workbook/view"
  const parts = url.split("/").filter(Boolean);
  if (parts.length >= 2) {
    return { workbookUrl: parts[parts.length - 2], viewName: parts[parts.length - 1] };
  }

  throw new Error(`Cannot parse Tableau Public URL: ${url}`);
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function main() {
  const input = process.argv[2];
  if (!input) {
    console.error(
      "Usage: npx tsx scripts/tableau-public/screenshot.ts <tableauPublicUrl>"
    );
    console.error(
      "Example: npx tsx scripts/tableau-public/screenshot.ts https://public.tableau.com/app/profile/yoshitaka6076/viz/WOW2026W5/WOW2026W4"
    );
    process.exit(1);
  }

  const { workbookUrl, viewName } = parseTableauUrl(input);

  const imageUrl = `${BASE_URL}/views/${workbookUrl}/${viewName}.png?:display_static_image=y&:showVizHome=n`;

  console.error(`Fetching screenshot: ${imageUrl}`);

  let imageBuffer: Buffer;
  try {
    const resp = await axios.get(imageUrl, {
      responseType: "arraybuffer",
      timeout: 30000,
    });
    imageBuffer = Buffer.from(resp.data);
  } catch (error: any) {
    const result = {
      success: false,
      error: "Failed to fetch screenshot",
      imageUrl,
      statusCode: error?.response?.status,
      suggestion:
        "Check that the workbook is published to Tableau Public and the view name is correct",
    };
    console.log(JSON.stringify(result, null, 2));
    process.exit(1);
    return;
  }

  // Save to output directory
  const outputDir = parseOutputDir(process.argv);
  const baseDir = outputDir
    ? path.join(path.resolve(outputDir), "tmp")
    : path.join(os.tmpdir(), "tableau-public-mcp");
  const screenshotDir = path.join(baseDir, "screenshots");
  await fs.mkdir(screenshotDir, { recursive: true });
  const filePath = path.join(screenshotDir, `${workbookUrl}_${viewName}.png`);
  await fs.writeFile(filePath, imageBuffer);

  console.error(`Saved to: ${filePath}`);

  const result = {
    success: true,
    filePath,
    imageUrl,
    workbookUrl,
    viewName,
    fileSize: formatFileSize(imageBuffer.length),
    nextStep: "Use the Read tool to view the screenshot image",
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
