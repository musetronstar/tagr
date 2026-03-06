#!/usr/bin/env python3
"""
tagr.py

Command line tool and entry point for `tagr`.

`tagr` reads English text from STDIN, normalize and analyze it, translate
grammar patterns into TAGL, and write TAGL to STDOUT.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys


class TranslationError(ValueError):
    """Raised when input cannot be translated by supported rules."""


@dataclass(frozen=True)
class IsARelation:
    """Internal model for a subordinate `subject is a/an object` relation."""

    subject: str
    obj: str


_IS_A_PATTERN = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s+is\s+(?:a|an)\s+([A-Za-z][A-Za-z0-9_-]*)\s*\.?\s*$",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    """
    Clean and normalize natural language input text.

    Args:
        text: Raw natural language input.

    Returns:
        Normalized text.
    """
    return text.strip()


def parse_is_a(text: str) -> IsARelation:
    """Parse the supported `subject is a/an object` sentence shape."""
    match = _IS_A_PATTERN.match(text)
    if not match:
        raise TranslationError(f"Unsupported input: {text!r}")

    subject, obj = match.groups()
    return IsARelation(subject=subject.lower(), obj=obj.lower())


def rule_is_a(relation: IsARelation) -> str:
    """Translate an `is a` relation into TAGL syntax."""
    return f">> {relation.subject} is_a {relation.obj};"


def translate(text: str) -> str:
    """
    Translate normalized English text into TAGL.

    Args:
        text: Normalized English input.

    Returns:
        TAGL output text.
    """
    relation = parse_is_a(text)
    return rule_is_a(relation)


def main() -> int:
    """
    Read natural language from STDIN, normalize, translate,
    and write TAGL to to STDOUT.

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
