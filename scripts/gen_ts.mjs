#!/usr/bin/env node
// Compile one bundle so shared $defs produce one declaration each.
import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { compile } from 'json-schema-to-typescript';

// json-schema-to-typescript prioritizes oneOf over sibling properties. Distribute
// the common object shape into each branch so required envelope fields survive.
// JSON Schema remains unchanged; this projection also encodes not-required as never.
function forTypes(node) {
  if (Array.isArray(node)) return node.map(forTypes);
  if (!node || typeof node !== 'object') return node;
  const normalized = Object.fromEntries(
    Object.entries(node).map(([key, value]) => [key, forTypes(value)]),
  );
  // Runtime conditional validations have no direct declaration-file equivalent.
  if (normalized.allOf) {
    normalized.allOf = normalized.allOf.filter(part => !part.if);
    if (!normalized.allOf.length) delete normalized.allOf;
  }
  const union = normalized.oneOf ?? normalized.anyOf;
  if (!normalized.properties || !union) return normalized;
  const base = {...normalized};
  delete base.oneOf;
  delete base.anyOf;
  delete base.title;
  delete base.description;
  const branches = union.map(branch => {
    const merged = {...base, ...branch,
      properties: {...base.properties, ...branch.properties},
      required: [...new Set([...(base.required ?? []), ...(branch.required ?? [])])],
    };
    const forbidden = branch.not?.required ??
      branch.not?.anyOf?.flatMap(part => part.required ?? []) ?? [];
    for (const field of forbidden) merged.properties[field] = {tsType: 'never'};
    delete merged.not;
    return merged;
  });
  return {title: normalized.title, description: normalized.description, oneOf: branches};
}

const root = new URL('../', import.meta.url);
const schemaDir = new URL('contracts/schemas/', root);
const definitions = {};
const properties = {};
const files = (await readdir(schemaDir)).filter(f => f.endsWith('.json')).sort();
if (!files.length) throw new Error('No JSON schemas found; run export_schemas.py first');
for (const file of files) {
  const schema = JSON.parse(await readFile(new URL(file, schemaDir), 'utf8'));
  for (const [key, value] of Object.entries(schema.$defs ?? {})) {
    if (definitions[key] && JSON.stringify(definitions[key]) !== JSON.stringify(value)) {
      throw new Error(`Conflicting definition: ${key}`);
    }
    definitions[key] = value;
  }
  delete schema.$defs;
  delete schema.$id;
  delete schema.$schema;
  const key = schema.title;
  definitions[key] = schema;
  properties[key] = { $ref: `#/$defs/${key}` };
}
const bundle = {
  title: 'GoldGraftContracts', type: 'object', additionalProperties: false,
  properties, required: Object.keys(properties), $defs: definitions,
};
const output = await compile(forTypes(bundle), 'GoldGraftContracts', {
  bannerComment: '/* Generated from Python contracts. Do not edit. */',
  unreachableDefinitions: true, additionalProperties: false,
  format: true, cwd: fileURLToPath(root),
  // Do not emit enormous fixed-size tuples for numerical constraints.
  maxItems: -1,
});
await mkdir(new URL('contracts/ts/', root), { recursive: true });
await writeFile(new URL('contracts/ts/goldgraft-contracts.d.ts', root), output);
console.log(`Generated TypeScript for ${Object.keys(properties).length} schemas`);
