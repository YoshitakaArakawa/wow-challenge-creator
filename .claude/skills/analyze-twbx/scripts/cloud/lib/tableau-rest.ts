import axios, { AxiosInstance } from "axios";
import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const REPO_ROOT = path.resolve(__dirname, "..", "..", "..", "..", "..", "..");
dotenv.config({ path: path.join(REPO_ROOT, ".env") });

const API_VERSION = "3.22";

export interface TableauEnv {
  serverUrl: string;
  siteContentUrl: string;
  /** Set only when PAT auth is configured; otherwise the cached OAuth session is used. */
  patName?: string;
  patValue?: string;
}

export interface Session {
  token: string;
  siteId: string;
  userId: string;
  /** true = PAT sign-in (sign out on exit); false = cached OAuth session (keep alive). */
  viaPat: boolean;
}

export interface WorkbookSummary {
  id: string;
  name: string;
  contentUrl: string;
  projectId: string;
  projectName?: string;
  ownerId?: string;
  updatedAt?: string;
  webpageUrl?: string;
}

export function loadEnv(): TableauEnv {
  if (!process.env.TABLEAU_SERVER_URL) {
    throw new Error(`Missing required env var TABLEAU_SERVER_URL. Configure it in ${path.join(REPO_ROOT, ".env")}`);
  }
  const patName = process.env.TABLEAU_PAT_NAME;
  const patValue = process.env.TABLEAU_PAT_VALUE;
  return {
    serverUrl: process.env.TABLEAU_SERVER_URL.replace(/\/$/, ""),
    siteContentUrl: process.env.TABLEAU_SITE_ID ?? "",
    patName: patName && patValue ? patName : undefined,
    patValue: patName && patValue ? patValue : undefined,
  };
}

// Written by publish-to-cloud/scripts/tableau_auth.py after the OAuth browser sign-in.
const AUTH_CACHE_PATH = path.join(REPO_ROOT, ".auth-cache", "session.json");
const LOGIN_HINT = "Run `python .claude/skills/publish-to-cloud/scripts/tableau_auth.py login` to sign in through the browser.";

interface CachedSession {
  server_url: string;
  site_name: string;
  access_token: string;
}

function readCachedSession(env: TableauEnv): CachedSession {
  if (!fs.existsSync(AUTH_CACHE_PATH)) {
    throw new Error(`No cached Tableau Cloud session at ${AUTH_CACHE_PATH}. ${LOGIN_HINT}`);
  }
  const cache = JSON.parse(fs.readFileSync(AUTH_CACHE_PATH, "utf8")) as CachedSession;
  if (cache.server_url !== env.serverUrl || cache.site_name !== env.siteContentUrl || !cache.access_token) {
    throw new Error(`Cached session does not match .env (server/site). ${LOGIN_HINT}`);
  }
  return cache;
}

function makeClient(env: TableauEnv, session: Session): AxiosInstance {
  return axios.create({
    baseURL: `${env.serverUrl}/api/${API_VERSION}/sites/${session.siteId}`,
    headers: { "X-Tableau-Auth": session.token, Accept: "application/json" },
  });
}

export async function signIn(env: TableauEnv): Promise<{ session: Session; client: AxiosInstance }> {
  if (env.patName && env.patValue) {
    const body = {
      credentials: {
        personalAccessTokenName: env.patName,
        personalAccessTokenSecret: env.patValue,
        site: { contentUrl: env.siteContentUrl },
      },
    };
    const res = await axios.post(`${env.serverUrl}/api/${API_VERSION}/auth/signin`, body, {
      headers: { "Content-Type": "application/json", Accept: "application/json" },
    });
    const creds = res.data?.credentials;
    if (!creds?.token || !creds?.site?.id) {
      throw new Error(`signin response missing credentials: ${JSON.stringify(res.data)}`);
    }
    const session: Session = { token: creds.token, siteId: creds.site.id, userId: creds.user?.id ?? "", viaPat: true };
    return { session, client: makeClient(env, session) };
  }

  // OAuth path: reuse the token cached by tableau_auth.py. The access_token is `id1|id2|site-luid`.
  const cache = readCachedSession(env);
  const parts = cache.access_token.split("|");
  if (parts.length !== 3) {
    throw new Error(`Cached access_token has an unexpected shape. ${LOGIN_HINT}`);
  }
  let current;
  try {
    current = await axios.get(`${env.serverUrl}/api/${API_VERSION}/sessions/current`, {
      headers: { "X-Tableau-Auth": cache.access_token, Accept: "application/json" },
    });
  } catch {
    throw new Error(`Cached Tableau Cloud session expired. ${LOGIN_HINT}`);
  }
  const session: Session = {
    token: cache.access_token,
    siteId: parts[2],
    userId: current.data?.session?.user?.id ?? "",
    viaPat: false,
  };
  return { session, client: makeClient(env, session) };
}

export async function signOut(env: TableauEnv, session: Session): Promise<void> {
  // An OAuth session is shared through the cache; signing out would invalidate it for the next script.
  if (!session.viaPat) return;
  await axios.post(`${env.serverUrl}/api/${API_VERSION}/auth/signout`, undefined, {
    headers: { "X-Tableau-Auth": session.token },
  });
}

export async function listWorkbooks(client: AxiosInstance, projectName?: string): Promise<WorkbookSummary[]> {
  const out: WorkbookSummary[] = [];
  let pageNumber = 1;
  const pageSize = 100;

  while (true) {
    const res = await client.get(`/workbooks`, {
      params: { pageSize, pageNumber },
    });

    const workbooks = res.data?.workbooks?.workbook ?? [];
    for (const wb of workbooks) {
      const summary: WorkbookSummary = {
        id: wb.id,
        name: wb.name,
        contentUrl: wb.contentUrl,
        projectId: wb.project?.id ?? "",
        projectName: wb.project?.name,
        ownerId: wb.owner?.id,
        updatedAt: wb.updatedAt,
        webpageUrl: wb.webpageUrl,
      };
      if (!projectName || summary.projectName === projectName) {
        out.push(summary);
      }
    }

    const total = Number(res.data?.pagination?.totalAvailable ?? 0);
    if (out.length >= total || workbooks.length < pageSize) break;
    pageNumber += 1;
  }

  return out;
}

export async function findWorkbookByName(
  client: AxiosInstance,
  name: string,
  projectName?: string,
): Promise<WorkbookSummary | null> {
  const all = await listWorkbooks(client, projectName);
  return all.find((wb) => wb.name === name) ?? null;
}

export async function downloadWorkbook(
  client: AxiosInstance,
  workbookId: string,
  destinationPath: string,
): Promise<void> {
  fs.mkdirSync(path.dirname(destinationPath), { recursive: true });

  const res = await client.get(`/workbooks/${workbookId}/content`, {
    responseType: "arraybuffer",
    headers: { Accept: "*/*" },
  });

  fs.writeFileSync(destinationPath, Buffer.from(res.data));
}
