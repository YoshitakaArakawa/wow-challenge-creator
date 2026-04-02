/**
 * Get TWBX Calculation Dependencies
 *
 * Builds a dependency graph of calculated fields.
 * Usage: npx tsx dependencies.ts <twbFilePath> [--source-fields]
 */

import * as fs from "fs/promises";
import * as path from "path";
import { fileExists } from "./lib/file-system";
import { parseTwbContent, ensureArray, decodeHtmlEntities, extractFieldReferences } from "./lib/twb-parser";

interface CalcNode {
  name: string;
  caption: string;
  formula: string;
  datasource: string;
  allReferences: string[];
  dependsOnCalcs: string[];
  dependsOnSource: string[];
  dependsOnParams: string[];
  usedBy: string[];
  depth: number;
  isCircular: boolean;
}

function extractCalculations(workbook: Record<string, unknown>) {
  const calculations = new Map<string, CalcNode>();
  const parameters = new Set<string>();
  const sourceFields = new Set<string>();

  const dsContainer = workbook.datasources as Record<string, unknown> | undefined;
  for (const ds of ensureArray(dsContainer?.datasource)) {
    if (!ds || typeof ds !== "object") continue;
    const dsObj = ds as Record<string, unknown>;
    const dsName = (dsObj["@_name"] as string) || "";
    const columns = ensureArray(dsObj["column"]);

    if (dsName === "Parameters") {
      for (const col of columns) {
        if (!col || typeof col !== "object") continue;
        const c = col as Record<string, unknown>;
        const paramName = (c["@_caption"] as string) || (c["@_name"] as string) || "";
        if (paramName) parameters.add(paramName);
        const internalName = (c["@_name"] as string) || "";
        if (internalName) parameters.add(internalName.replace(/[\[\]]/g, ""));
      }
      continue;
    }

    for (const col of columns) {
      if (!col || typeof col !== "object") continue;
      const c = col as Record<string, unknown>;
      const name = ((c["@_name"] as string) || "").replace(/[\[\]]/g, "");
      const caption = (c["@_caption"] as string) || name;
      const calc = c["calculation"] as Record<string, unknown> | undefined;

      if (calc && calc["@_formula"]) {
        const formula = decodeHtmlEntities((calc["@_formula"] as string) || "");
        calculations.set(caption, {
          name,
          caption,
          formula,
          datasource: dsName,
          allReferences: extractFieldReferences(formula),
          dependsOnCalcs: [],
          dependsOnSource: [],
          dependsOnParams: [],
          usedBy: [],
          depth: -1,
          isCircular: false,
        });
      } else {
        sourceFields.add(caption);
        sourceFields.add(name);
      }
    }
  }

  return { calculations, parameters, sourceFields };
}

function resolveDependencies(
  calculations: Map<string, CalcNode>,
  parameters: Set<string>
) {
  for (const [, node] of calculations) {
    for (const ref of node.allReferences) {
      if (parameters.has(ref)) {
        if (!node.dependsOnParams.includes(ref)) node.dependsOnParams.push(ref);
        continue;
      }
      let isCalc = false;
      for (const [caption, calcNode] of calculations) {
        if (ref === caption || ref === calcNode.name) {
          if (!node.dependsOnCalcs.includes(caption)) node.dependsOnCalcs.push(caption);
          isCalc = true;
          break;
        }
      }
      if (!isCalc && !node.dependsOnSource.includes(ref)) {
        node.dependsOnSource.push(ref);
      }
    }
  }
}

function buildReverseDependencies(calculations: Map<string, CalcNode>) {
  for (const [caption, node] of calculations) {
    for (const depCaption of node.dependsOnCalcs) {
      const depNode = calculations.get(depCaption);
      if (depNode && !depNode.usedBy.includes(caption)) depNode.usedBy.push(caption);
    }
  }
}

function calculateDepths(calculations: Map<string, CalcNode>) {
  const circularDeps: { cycle: string[]; explanation: string }[] = [];
  const visited = new Set<string>();
  const inStack = new Set<string>();

  function visit(caption: string, pathArr: string[]): number {
    if (inStack.has(caption)) {
      const cycleStart = pathArr.indexOf(caption);
      const cycle = [...pathArr.slice(cycleStart), caption];
      for (const name of cycle) {
        const node = calculations.get(name);
        if (node) node.isCircular = true;
      }
      circularDeps.push({ cycle, explanation: `Circular: ${cycle.join(" -> ")}` });
      return 0;
    }
    if (visited.has(caption)) return calculations.get(caption)?.depth ?? 0;

    const node = calculations.get(caption);
    if (!node) return 0;

    inStack.add(caption);
    let maxChildDepth = -1;
    for (const dep of node.dependsOnCalcs) {
      maxChildDepth = Math.max(maxChildDepth, visit(dep, [...pathArr, caption]));
    }
    inStack.delete(caption);
    visited.add(caption);
    node.depth = maxChildDepth + 1;
    return node.depth;
  }

  for (const caption of calculations.keys()) {
    if (!visited.has(caption)) visit(caption, []);
  }

  return circularDeps;
}

function generateDependencyTree(calculations: Map<string, CalcNode>): string {
  const lines: string[] = [];
  const leaves = Array.from(calculations.values())
    .filter((n) => n.usedBy.length === 0 && !n.isCircular)
    .sort((a, b) => b.depth - a.depth);

  if (leaves.length === 0) return "No leaf calculations found";

  const printed = new Set<string>();

  function printNode(caption: string, indent: string, isLast: boolean, visited: Set<string>) {
    if (visited.has(caption)) {
      lines.push(`${indent}${isLast ? "└── " : "├── "}${caption} (circular ref)`);
      return;
    }
    const node = calculations.get(caption);
    if (!node) return;

    lines.push(`${indent}${isLast ? "└── " : "├── "}${caption} [depth: ${node.depth}]`);
    printed.add(caption);
    visited.add(caption);

    const childIndent = indent + (isLast ? "    " : "│   ");
    const deps = node.dependsOnCalcs;
    for (let i = 0; i < deps.length; i++) {
      printNode(deps[i], childIndent, i === deps.length - 1, new Set(visited));
    }

    if (node.dependsOnSource.length > 0) {
      const label = node.dependsOnSource.slice(0, 3).join(", ");
      const suffix = node.dependsOnSource.length > 3 ? ` (+${node.dependsOnSource.length - 3} more)` : "";
      lines.push(`${childIndent}└── [source: ${label}${suffix}]`);
    }
  }

  for (let i = 0; i < Math.min(leaves.length, 10); i++) {
    const leaf = leaves[i];
    if (!printed.has(leaf.caption)) {
      lines.push(`\n${leaf.caption} (leaf calculation)`);
      const deps = leaf.dependsOnCalcs;
      for (let j = 0; j < deps.length; j++) {
        printNode(deps[j], "", j === deps.length - 1, new Set([leaf.caption]));
      }
      if (leaf.dependsOnSource.length > 0) {
        lines.push(`└── [source: ${leaf.dependsOnSource.slice(0, 3).join(", ")}]`);
      }
    }
  }

  return lines.join("\n");
}

async function main() {
  const twbFilePath = process.argv[2];
  const includeSourceFields = process.argv.includes("--source-fields");

  if (!twbFilePath) {
    console.error("Usage: npx tsx dependencies.ts <twbFilePath> [--source-fields]");
    process.exit(1);
  }

  const absPath = path.resolve(twbFilePath);
  if (!(await fileExists(absPath))) {
    console.log(JSON.stringify({ success: false, error: "TWB file not found" }));
    process.exit(1);
  }
  if (path.extname(absPath).toLowerCase() !== ".twb") {
    console.log(JSON.stringify({ success: false, error: "Not a .twb file" }));
    process.exit(1);
  }

  const content = await fs.readFile(absPath, "utf-8");
  const parseResult = parseTwbContent(content);
  if (!parseResult.success) {
    console.log(JSON.stringify({ success: false, error: parseResult.error }));
    process.exit(1);
  }

  const workbook = (parseResult.data as any)?.workbook;
  if (!workbook) {
    console.log(JSON.stringify({ success: false, error: "Invalid TWB file structure" }));
    process.exit(1);
  }

  const { calculations, parameters, sourceFields } = extractCalculations(workbook);

  if (calculations.size === 0) {
    console.log(
      JSON.stringify({
        success: true,
        message: "No calculated fields found",
        summary: { totalCalculations: 0, parameterCount: parameters.size, sourceFieldCount: sourceFields.size },
      })
    );
    return;
  }

  resolveDependencies(calculations, parameters);
  buildReverseDependencies(calculations);
  const circularDeps = calculateDepths(calculations);

  let maxDepth = 0;
  const outputs: any[] = [];

  for (const [caption, node] of calculations) {
    const output = {
      name: node.name,
      caption,
      formula: node.formula,
      datasource: node.datasource,
      depth: node.depth,
      dependsOn: {
        calculations: node.dependsOnCalcs,
        sourceFields: includeSourceFields ? node.dependsOnSource : node.dependsOnSource.slice(0, 5),
        parameters: node.dependsOnParams,
      },
      usedBy: node.usedBy,
      isRoot: node.dependsOnCalcs.length === 0,
      isLeaf: node.usedBy.length === 0,
      isCircular: node.isCircular,
    };
    outputs.push(output);
    if (!node.isCircular && node.depth > maxDepth) maxDepth = node.depth;
  }

  outputs.sort((a, b) => a.depth - b.depth);

  const result = {
    success: true,
    sourceFile: absPath,
    summary: {
      totalCalculations: calculations.size,
      maxDependencyDepth: maxDepth,
      rootCalculations: outputs.filter((c) => c.isRoot && !c.isCircular).length,
      leafCalculations: outputs.filter((c) => c.isLeaf && !c.isCircular).length,
      intermediateCalculations: outputs.filter((c) => !c.isRoot && !c.isLeaf && !c.isCircular).length,
      circularDependencies: circularDeps.length,
      parameterCount: parameters.size,
    },
    calculations: outputs.slice(0, 50),
    circularDependencies: circularDeps.length > 0 ? circularDeps : undefined,
    dependencyTree: generateDependencyTree(calculations),
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
