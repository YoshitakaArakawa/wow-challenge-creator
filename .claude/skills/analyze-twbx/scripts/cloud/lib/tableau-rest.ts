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
  patName: string;
  patValue: string;
}

export interface Session {
  token: string;
  siteId: string;
  userId: string;
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
  const required = ["TABLEAU_SERVER_URL", "TABLEAU_PAT_NAME", "TABLEAU_PAT_VALUE"] as const;
  const missing = required.filter((k) => !process.env[k]);
  if (missing.length) {
    throw new Error(
      `Missing required env vars: ${missing.join(", ")}. Configure them in ${path.join(REPO_ROOT, ".env")}`,
    );
  }
  return {
    serverUrl: process.env.TABLEAU_SERVER_URL!.replace(/\/$/, ""),
    siteContentUrl: process.env.TABLEAU_SITE_ID ?? "",
    patName: process.env.TABLEAU_PAT_NAME!,
    patValue: process.env.TABLEAU_PAT_VALUE!,
  };
}

export async function signIn(env: TableauEnv): Promise<{ session: Session; client: AxiosInstance }> {
  const body = {
    credentials: {
      personalAccessTokenName: env.patName,
      personalAccessTokenSecret: env.patValue,
      site: { contentUrl: env.siteContentUrl },
    },
  };

  const url = `${env.serverUrl}/api/${API_VERSION}/auth/signin`;
  const res = await axios.post(url, body, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
  });

  const creds = res.data?.credentials;
  if (!creds?.token || !creds?.site?.id) {
    throw new Error(`signin response missing credentials: ${JSON.stringify(res.data)}`);
  }

  const session: Session = {
    token: creds.token,
    siteId: creds.site.id,
    userId: creds.user?.id ?? "",
  };

  const client = axios.create({
    baseURL: `${env.serverUrl}/api/${API_VERSION}/sites/${session.siteId}`,
    headers: {
      "X-Tableau-Auth": session.token,
      Accept: "application/json",
    },
  });

  return { session, client };
}

export async function signOut(env: TableauEnv, session: Session): Promise<void> {
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
