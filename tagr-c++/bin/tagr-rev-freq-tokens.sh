#!/bin/bash
set -euo pipefail

# Usage:
#   cat raw-input.txt | bin/tagr-rev-freq-tokens.sh
#
#   Options:
#       [--file <path/to/file.tagl> ...]
#           chain of one or more TAGL files passed to `tagr`
#       -f
#           short option for --file
#       [--db <path/to/tagspace.db> ...]
#           chain of one or more tagspace databases passed to `tagr`
#
# Reads raw input from STDIN, runs `tagr`, then prints a reverse frequency table
# of the selected columns from the lookup log TSV rows.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAGR_BIN="$ROOT_DIR/bin/tagr"

# TODO: By default, count the full lookup log row using all columns.
# TODO: Add `--columns '1'` for token values, `--columns '2'` for token types,
# TODO: `--columns '1 2'` for both, etc. Select columns in the order provided.

TMP_IN="$(mktemp /tmp/tagr-rev-freq-in-XXXXXX)"

cleanup() {
	rm -f "$TMP_IN"
}
trap cleanup EXIT

cat > "$TMP_IN"

"$TAGR_BIN" "$@" -n < "$TMP_IN" 2>&1 \
	| sort | uniq -c | sort -nr
