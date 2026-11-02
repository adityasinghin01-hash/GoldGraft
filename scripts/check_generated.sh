#!/bin/sh
# Compare bytes as well as git's tracked diff: works before the initial commit.
set -eu
cd "$(dirname "$0")/.."
work=$(mktemp -d "${TMPDIR:-/tmp}/goldgraft-generated.XXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
mkdir -p "$work/before/schemas" "$work/before/ts" "$work/before/api" "$work/after"
if [ -d contracts/schemas ]; then cp -R contracts/schemas/. "$work/before/schemas/"; fi
if [ -d contracts/ts ]; then cp -R contracts/ts/. "$work/before/ts/"; fi
if [ -d contracts/api ]; then cp -R contracts/api/. "$work/before/api/"; fi
uv run python scripts/export_schemas.py
node scripts/gen_ts.mjs
uv run python scripts/export_openapi.py
npx --no-install openapi-typescript contracts/api/openapi.json -o contracts/ts/goldgraft-api.d.ts --silent
cp -R contracts/schemas "$work/after/schemas"
cp -R contracts/ts "$work/after/ts"
cp -R contracts/api "$work/after/api"
git diff --no-index --exit-code "$work/before" "$work/after"
git diff --exit-code -- contracts/schemas contracts/ts contracts/api
printf '%s\n' 'Generated outputs are current'
