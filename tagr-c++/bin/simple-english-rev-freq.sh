#!/bin/bash
set -euo pipefail

# Reads definitions ($1=word + $3=gloss) from VOA word book TSV file dictionary
# and prints their TAGL Simple English tag POS types 

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT_DIR/data"
TAGR_BIN="$ROOT_DIR/bin/tagr"
TSV_FILE="${HOME}/projects/tagd-simple-english/word-list-defs.tsv"
TAGL_FILE="${HOME}/projects/tagd-simple-english/simple-english.tagl"

awk -F'\t' 'NR>1 {printf "%s %s\n", $1, $3}' $TSV_FILE \
	| $TAGR_BIN -f $TAGL_FILE -n 2>&1 \
		| sort | uniq -c | sort -nr
