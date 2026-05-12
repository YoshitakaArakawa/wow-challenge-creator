import fs from "node:fs";
import path from "node:path";
import axios from "axios";
import { repoRootFrom } from "./lib/paths.js";

interface VersionFile {
  _comment?: string;
  repo: string;
  sha: string | null;
  tag: string | null;
  last_checked: string | null;
  last_updated: string | null;
  files: string[];
}

const CACHE_HOURS = 24;
const REPO_API = "https://api.github.com/repos/tableau/tableau-document-schemas";

function versionFilePath(repoRoot: string): string {
  return path.join(
    repoRoot,
    ".claude",
    "skills",
    "create-workbook",
    "references",
    "schemas",
    ".version",
  );
}

function loadVersion(filePath: string): VersionFile {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as VersionFile;
}

function saveVersion(filePath: string, data: VersionFile): void {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + "\n");
}

function isCacheFresh(lastChecked: string | null): boolean {
  if (!lastChecked) return false;
  const lastMs = Date.parse(lastChecked);
  if (Number.isNaN(lastMs)) return false;
  return Date.now() - lastMs < CACHE_HOURS * 3600 * 1000;
}

async function fetchLatestRelease(): Promise<{ tag: string | null; sha: string; notes: string } | null> {
  try {
    const releaseRes = await axios.get(`${REPO_API}/releases/latest`, {
      headers: { Accept: "application/vnd.github+json" },
      validateStatus: (s) => s < 500,
    });
    if (releaseRes.status === 200) {
      const tag = releaseRes.data?.tag_name ?? null;
      const notes = releaseRes.data?.body ?? "";
      const tagRes = await axios.get(`${REPO_API}/git/refs/tags/${tag}`, {
        headers: { Accept: "application/vnd.github+json" },
        validateStatus: () => true,
      });
      let sha = tagRes.data?.object?.sha ?? null;
      if (sha && tagRes.data?.object?.type === "tag") {
        const tagDetail = await axios.get(`${REPO_API}/git/tags/${sha}`, {
          headers: { Accept: "application/vnd.github+json" },
          validateStatus: () => true,
        });
        sha = tagDetail.data?.object?.sha ?? sha;
      }
      if (sha) return { tag, sha, notes };
    }
  } catch {
    // fall through to commits
  }
  // Fallback to latest commit on default branch.
  const commitRes = await axios.get(`${REPO_API}/commits?per_page=1`, {
    headers: { Accept: "application/vnd.github+json" },
  });
  const head = commitRes.data?.[0];
  if (!head) return null;
  return {
    tag: null,
    sha: head.sha,
    notes: head.commit?.message ?? "",
  };
}

async function main() {
  const force = process.argv.includes("--force");
  const repoRoot = repoRootFrom(import.meta.url);
  const filePath = versionFilePath(repoRoot);
  const current = loadVersion(filePath);

  if (!force && isCacheFresh(current.last_checked)) {
    process.stdout.write(
      JSON.stringify(
        {
          ok: true,
          cacheHit: true,
          message: `Cache fresh (${CACHE_HOURS}h). Last checked: ${current.last_checked}`,
          current,
        },
        null,
        2,
      ) + "\n",
    );
    return;
  }

  const latest = await fetchLatestRelease();
  current.last_checked = new Date().toISOString();
  saveVersion(filePath, current);

  if (!latest) {
    process.stdout.write(
      JSON.stringify({ ok: true, cacheHit: false, message: "Could not fetch latest release/commit.", current }, null, 2) +
        "\n",
    );
    return;
  }

  const hasUpdate = !current.sha || current.sha !== latest.sha;
  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        cacheHit: false,
        hasUpdate,
        localSha: current.sha,
        latestSha: latest.sha,
        latestTag: latest.tag,
        releaseNotesPreview: hasUpdate ? latest.notes.slice(0, 2000) : "(up to date)",
        nextStep: hasUpdate
          ? `Run: npx tsx update-schemas.ts --sha ${latest.sha}`
          : "No action needed.",
      },
      null,
      2,
    ) + "\n",
  );
}

main().catch((err) => {
  console.error(err?.response?.data ?? err);
  process.exit(1);
});
