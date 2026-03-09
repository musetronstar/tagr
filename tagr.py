#!/usr/bin/env python3
"""
tagr.py

Command line tool and entry point for `tagr`.

`tagr` reads English text from STDIN, normalize and analyze it, translate
grammar patterns into TAGL, and write TAGL to STDOUT.
"""

from __future__ import annotations

import sys
from typing import Callable

from parser import (
    PosToken,
    TranslationError,
    normalize,
    parse_relations,
    pos_tag,
)
from taglizer import taglize_relations


def translate(
    text: str, alt_tagger: Callable[[str], list[PosToken]] | None = None
) -> str:
    """
    Translate normalized English text into TAGL.

    Args:
        text: Normalized English input.
        alt_tagger: Optional POS tagging function for tests or alternate adapters.

    Returns:
        TAGL output text.
    """
    tagger = alt_tagger or pos_tag
    tokens = tagger(text)
    relations = parse_relations(tokens)
    return taglize_relations(relations)


def main() -> int:
    """
    Read natural language from STDIN, normalize, translate,
    and write TAGL to STDOUT.

    Returns:
        Process exit status code.
    """
    raw_text = sys.stdin.read()

    if not raw_text.strip():
        return 0

    normalized = normalize(raw_text)

    try:
        output = translate(normalized)
    except TranslationError as exc:
        sys.stderr.write(f"Translation error: {exc}\n")
        return 1

    if output:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
