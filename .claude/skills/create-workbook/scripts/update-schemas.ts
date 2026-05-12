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

function schemasDir(repoRoot: string): string {
  return path.dirname(versionFilePath(repoRoot));
}

function parseArgs(argv: string[]): { sha?: string; tag?: string } {
  const out: { sha?: string; tag?: string } = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--sha") out.sha = argv[++i];
    else if (argv[i] === "--tag") out.tag = argv[++i];
  }
  return out;
}

async function resolveLatestSha(): Promise<{ sha: string; tag: string | null }> {
  const release = await axios.get(`${REPO_API}/releases/latest`, {
    headers: { Accept: "application/vnd.github+json" },
    validateStatus: (s) => s < 500,
  });
  if (release.status === 200 && release.data?.tag_name) {
    const tag = release.data.tag_name as string;
    const tagRef = await axios.get(`${REPO_API}/git/refs/tags/${tag}`, {
      headers: { Accept: "application/vnd.github+json" },
    });
    let sha = tagRef.data?.object?.sha as string;
    if (tagRef.data?.object?.type === "tag") {
      const tagDetail = await axios.get(`${REPO_API}/git/tags/${sha}`, {
        headers: { Accept: "application/vnd.github+json" },
      });
      sha = tagDetail.data?.object?.sha ?? sha;
    }
    return { sha, tag };
  }
  const commit = await axios.get(`${REPO_API}/commits?per_page=1`, {
    headers: { Accept: "application/vnd.github+json" },
  });
  return { sha: commit.data?.[0]?.sha as string, tag: null };
}

interface TreeEntry {
  path: string;
  type: "blob" | "tree";
  sha: string;
}

async function listXsdFilesAtSha(sha: string): Promise<TreeEntry[]> {
  const res = await axios.get(`${REPO_API}/git/trees/${sha}?recursive=1`, {
    headers: { Accept: "application/vnd.github+json" },
  });
  const tree: TreeEntry[] = res.data?.tree ?? [];
  return tree.filter((e) => e.type === "blob" && e.path.toLowerCase().endsWith(".xsd"));
}

async function downloadFile(sha: string, repoPath: string, destPath: string): Promise<void> {
  const url = `https://raw.githubusercontent.com/tableau/tableau-document-schemas/${sha}/${repoPath}`;
  const res = await axios.get(url, { responseType: "arraybuffer" });
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  fs.writeFileSync(destPath, Buffer.from(res.data));
}

async function main() {
  const repoRoot = repoRootFrom(import.meta.url);
  const dir = schemasDir(repoRoot);
  const versionPath = versionFilePath(repoRoot);
  const current = JSON.parse(fs.readFileSync(versionPath, "utf8")) as VersionFile;

  const args = parseArgs(process.argv.slice(2));
  const target = args.sha ? { sha: args.sha, tag: args.tag ?? null } : await resolveLatestSha();
  if (!target.sha) throw new Error("Could not resolve target SHA");

  const xsdEntries = await listXsdFilesAtSha(target.sha);
  if (xsdEntries.length === 0) {
    throw new Error(`No .xsd files found at SHA ${target.sha}`);
  }

  // Wipe previously fetched XSDs (keep .version)
  for (const entry of fs.readdirSync(dir)) {
    if (entry === ".version") continue;
    const full = path.join(dir, entry);
    fs.rmSync(full, { recursive: true, force: true });
  }

  const written: string[] = [];
  for (const entry of xsdEntries) {
    const dest = path.join(dir, entry.path);
    await downloadFile(target.sha, entry.path, dest);
    written.push(entry.path);
  }

  current.sha = target.sha;
  current.tag = target.tag;
  current.last_updated = new Date().toISOString();
  current.last_checked = current.last_updated;
  current.files = written;
  fs.writeFileSync(versionPath, JSON.stringify(current, null, 2) + "\n");

  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        sha: target.sha,
        tag: target.tag,
        filesWritten: written.length,
        firstFew: written.slice(0, 10),
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
