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
class SubRelation:
    """Internal model for a subordinate `subject sub object` relation."""

    subject: str
    sub: str
    obj: str


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


def parse_sub_relation(tokens: list[PosToken]) -> SubRelation:
    """Parse a narrow `subject AUX DET object` pattern into a sub relation."""
    lexical_tokens = [t for t in tokens if t.pos != "PUNCT"]

    if len(lexical_tokens) != 4:
        raise TranslationError("Unsupported input: expected a 4-token sub relation")

    subject, copula, determiner, obj = lexical_tokens

    if subject.pos not in {"NOUN", "PROPN", "PRON"}:
        raise TranslationError("Unsupported input: subject must be noun-like")

    if copula.pos != "AUX" or copula.text.lower() != "is":
        raise TranslationError("Unsupported input: only copula 'is' is supported")

    if determiner.pos != "DET" or determiner.text.lower() not in {"a", "an"}:
        raise TranslationError("Unsupported input: expected determiner 'a' or 'an'")

    if obj.pos not in {"NOUN", "PROPN"}:
        raise TranslationError("Unsupported input: object must be noun-like")

    return SubRelation(subject=subject.text.lower(), sub="_sub", obj=obj.text.lower())


def rule_sub_relation(relation: SubRelation) -> str:
    """Translate a sub relation into a TAGL put statement."""
    return f">> {relation.subject} {relation.sub} {relation.obj};"


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
    relation = parse_sub_relation(tokens)
    return rule_sub_relation(relation)


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
