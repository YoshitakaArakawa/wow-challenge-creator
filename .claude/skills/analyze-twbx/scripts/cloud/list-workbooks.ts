import { loadEnv, signIn, signOut, listWorkbooks } from "./lib/tableau-rest.js";

function parseArgs(argv: string[]): { project?: string } {
  const out: { project?: string } = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--project") {
      out.project = argv[++i];
    }
  }
  return out;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const env = loadEnv();
  const projectFilter = args.project ?? process.env.TABLEAU_PROJECT_NAME ?? undefined;

  const { session, client } = await signIn(env);
  try {
    const workbooks = await listWorkbooks(client, projectFilter);
    process.stdout.write(
      JSON.stringify(
        {
          siteContentUrl: env.siteContentUrl,
          projectFilter: projectFilter ?? null,
          count: workbooks.length,
          workbooks,
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
