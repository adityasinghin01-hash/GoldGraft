#!/bin/sh
# Compare bytes as well as git's tracked diff: works before the initial commit.
set -eu
cd "$(dirname "$0")/.."
work=$(mktemp -d "${TMPDIR:-/tmp}/goldgraft-generated.XXXXXX")
trap 'rm -rf "$work"' EXIT HUP INT TERM
mkdir -p "$work/before/schemas" "$work/before/ts" "$work/after"
if [ -d contracts/schemas ]; then cp -R contracts/schemas/. "$work/before/schemas/"; fi
if [ -d contracts/ts ]; then cp -R contracts/ts/. "$work/before/ts/"; fi
uv run python scripts/export_schemas.py
node scripts/gen_ts.mjs
cp -R contracts/schemas "$work/after/schemas"
cp -R contracts/ts "$work/after/ts"
git diff --no-index --exit-code "$work/before" "$work/after"
git diff --exit-code -- contracts/schemas contracts/ts
printf '%s\n' 'Generated outputs are current'
