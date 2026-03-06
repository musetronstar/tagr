#!/usr/bin/env bash
# Creates and goes into venv
# Install or Update pip module dependencies

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/deps/pip-modules.txt"
SPACY_MODEL="en_core_web_sm"

if [[ ! -f "$REQ_FILE" ]]; then
    echo "error: requirements file not found: $REQ_FILE" >&2
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
else
    echo "Using existing virtual environment at $VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Upgrading pip"
python -m pip install --upgrade pip

echo "Installing/updating Python dependencies"
python -m pip install --upgrade -r "$REQ_FILE"

echo "Checking spaCy model: $SPACY_MODEL"
if ! python -m spacy info "$SPACY_MODEL" >/dev/null 2>&1; then
    echo "Installing spaCy model: $SPACY_MODEL"
    python -m spacy download "$SPACY_MODEL"
else
    echo "spaCy model already installed: $SPACY_MODEL"
fi

echo "Done"
