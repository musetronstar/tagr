#!/usr/bin/env python3
"""
tagr.py

Command line tool and entry point for `tagr`.

`tagr` reads English text from STDIN, normalize and analyze it, translate
grammar patterns into TAGL, and write TAGL to STDOUT.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import sys
from typing import Callable


class TranslationError(ValueError):
    """Raised when input cannot be translated by supported rules."""


@dataclass(frozen=True)
class PosToken:
    """Internal NLP token representation to avoid leaking spaCy objects."""

    text: str
    pos: str


@dataclass(frozen=True)
class Relation:
    """Internal model for a `subject relator object` TAGL relation shape."""

    subject: str
    relator: str
    obj: str


_SUBJECT_POS = {"NOUN", "PROPN", "PRON"}
_OBJECT_POS = _SUBJECT_POS | {"VERB", "ADJ"}


@lru_cache(maxsize=1)
def _get_spacy_model() -> object:
    """Lazily load the spaCy model once for POS tagging."""
    try:
        import spacy
    except ModuleNotFoundError as exc:
        raise TranslationError("spaCy is required for POS tagging but is not installed") from exc

    try:
        return spacy.load("en_core_web_sm")
    except OSError as exc:
        raise TranslationError(
            "spaCy model 'en_core_web_sm' is required but not installed"
        ) from exc


def normalize(text: str) -> str:
    """
    Clean and normalize natural language input text.

    Args:
        text: Raw natural language input.

    Returns:
        Normalized text.
    """
    return text.strip()


def pos_tag(text: str) -> list[PosToken]:
    """Convert spaCy token data into internal POS-token models."""
    nlp = _get_spacy_model()
    doc = nlp(text)
    return [PosToken(text=token.text, pos=token.pos_) for token in doc if not token.is_space]


def _taglize(tokens: list[PosToken]) -> str:
    """Convert relation-token text to TAGL id form (`x y` -> `x_y`)."""
    return "_".join(token.text.lower() for token in tokens)


def parse_relation(tokens: list[PosToken]) -> Relation:
    """Parse POS-tagged text into a `subject relator object` relation shape."""
    lexical_tokens = [token for token in tokens if token.pos != "PUNCT"]

    if lexical_tokens and lexical_tokens[0].pos == "DET":
        lexical_tokens = lexical_tokens[1:]

    if len(lexical_tokens) < 3:
        raise TranslationError("Unsupported input: expected at least subject, relator, and object")

    subject = lexical_tokens[0]
    relator_tokens = lexical_tokens[1:-1]
    obj = lexical_tokens[-1]

    if subject.pos not in _SUBJECT_POS:
        raise TranslationError("Unsupported input: subject must be noun-like")

    if not relator_tokens:
        raise TranslationError("Unsupported input: missing relator")

    if obj.pos not in _OBJECT_POS:
        raise TranslationError("Unsupported input: object must be noun-like, verb, or adjective")

    relator = _taglize(relator_tokens)
    if not relator:
        raise TranslationError("Unsupported input: invalid relator")

    return Relation(subject=subject.text.lower(), relator=relator, obj=obj.text.lower())


def rule_relation(relation: Relation) -> str:
    """Translate a parsed relation into a TAGL put statement."""
    return f">> {relation.subject} {relation.relator} {relation.obj};"


def translate(text: str, pos_tagger: Callable[[str], list[PosToken]] | None = None) -> str:
    """
    Translate normalized English text into TAGL.

    Args:
        text: Normalized English input.
        pos_tagger: Optional POS tagging function for tests or alternate adapters.

    Returns:
        TAGL output text.
    """
    tagger = pos_tagger or pos_tag
    tokens = tagger(text)
    relation = parse_relation(tokens)
    return rule_relation(relation)


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
