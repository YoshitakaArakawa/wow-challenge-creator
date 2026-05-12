import path from "node:path";
import {
  loadEnv,
  signIn,
  signOut,
  findWorkbookByName,
  downloadWorkbook,
} from "./lib/tableau-rest.js";

interface Args {
  name?: string;
  id?: string;
  project?: string;
  outputDir?: string;
  fileName?: string;
}

function parseArgs(argv: string[]): Args {
  const out: Args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--name") out.name = argv[++i];
    else if (a === "--id") out.id = argv[++i];
    else if (a === "--project") out.project = argv[++i];
    else if (a === "--output-dir") out.outputDir = argv[++i];
    else if (a === "--file-name") out.fileName = argv[++i];
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (!args.name && !args.id) {
    throw new Error("Provide --name <workbookName> or --id <workbookId>");
  }
  if (!args.outputDir) {
    throw new Error("Provide --output-dir <outputs/{theme}>");
  }

  const env = loadEnv();
  const projectFilter = args.project ?? process.env.TABLEAU_PROJECT_NAME ?? undefined;

  const { session, client } = await signIn(env);
  try {
    let workbookId = args.id;
    let resolvedName = args.name;

    if (!workbookId && args.name) {
      const wb = await findWorkbookByName(client, args.name, projectFilter);
      if (!wb) {
        throw new Error(
          `Workbook "${args.name}" not found in project "${projectFilter ?? "(any)"}"`,
        );
      }
      workbookId = wb.id;
      resolvedName = wb.name;
    }

    const fileName = args.fileName ?? "cloud-pulled.twbx";
    const destinationPath = path.resolve(args.outputDir, "tmp", fileName);
    await downloadWorkbook(client, workbookId!, destinationPath);

    process.stdout.write(
      JSON.stringify(
        {
          workbookId,
          resolvedName: resolvedName ?? null,
          downloadedTo: destinationPath,
        },
        null,
        2,
      ) + "\n",
    );
  } finally {
    await signOut(env, session);
  }
}

main().catch((err) => {
  console.error(err?.response?.data ?? err);
  process.exit(1);
});
