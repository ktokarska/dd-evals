#!/usr/bin/env bash
# Style guard: long em dashes are banned in this repo.
# Bans U+2014 and its HTML entities (&mdash;, &#8212;). Use commas or restructure.
# En dashes (U+2013) and hyphens are allowed. Exit non-zero if any em dash is found.
set -euo pipefail

# Exclude this script and the CI workflow, which reference the banned tokens by name.
hits=$(git grep -nP '\x{2014}|&mdash;|&#8212;' -- . \
  ':!scripts/no-em-dash.sh' \
  ':!.github/workflows/ci.yml' 2>/dev/null || true)

if [ -n "$hits" ]; then
  echo "ERROR: long em dashes are banned. Replace them with commas (or restructure)."
  echo "$hits"
  exit 1
fi

echo "OK: no em dashes found."
