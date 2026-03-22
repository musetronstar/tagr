#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$ROOT_DIR/tests"
TAGL_FILE="$TEST_DIR/bootstrap.tagl"
BIN="$ROOT_DIR/bin/tagr-rev-freq-tokens.sh"
OPTS="--file $TAGL_FILE"
INPUT="$TEST_DIR/simple-text.txt"
EXPECTED="$TEST_DIR/output-simple-text-rev-freqs.txt"
TMP_OUT="$(mktemp /tmp/tagr-rev-freqs-XXXXXX)"

cleanup() {
	rm -f "$TMP_OUT"
}
trap cleanup EXIT

"$BIN" $OPTS < "$INPUT" > "$TMP_OUT"

if ! diff -u "$EXPECTED" "$TMP_OUT"; then
	exit 1
fi
