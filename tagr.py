#!/usr/bin/env python3
"""
tagr.py

Command line tool and entry point for `tagr`.

`tagr` reads English text from STDIN, normalize and analyze it, translate
grammar patterns into TAGL, and write TAGL to STDOUT.
"""

from __future__ import annotations

import argparse
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


@dataclass(frozen=True)
class HintMatch:
    """Matched hint span in the token stream."""

    tagd_pos: str
    value: str
    start: int
    end: int


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


def parse_hint_args(raw_hints: list[str]) -> dict[str, list[str]]:
    """Parse repeated `--hint <tagd_pos>=<value>` arguments."""
    parsed: dict[str, list[str]] = {}

    for raw_hint in raw_hints:
        tagd_pos, separator, value = raw_hint.partition("=")
        if separator != "=" or not tagd_pos.strip() or not value.strip():
            raise TranslationError("Invalid --hint: expected <tagd_pos>=<value>")
        parsed.setdefault(tagd_pos.strip(), []).append(value.strip())

    return parsed


def _hint_value_tokens(value: str) -> list[str]:
    """Normalize a hint value into lowercase token text."""
    return value.lower().split()


def _match_hint(tokens: list[PosToken], tagd_pos: str, value: str) -> HintMatch:
    """Find a contiguous token span matching a hint value."""
    target = _hint_value_tokens(value)
    token_texts = [token.text.lower() for token in tokens]

    if not target:
        raise TranslationError("Invalid --hint: value must not be empty")

    for start in range(0, len(token_texts) - len(target) + 1):
        if token_texts[start : start + len(target)] == target:
            return HintMatch(tagd_pos=tagd_pos, value=value, start=start, end=start + len(target))

    raise TranslationError(f"Hint value not found in input: {value}")


def match_hints(tokens: list[PosToken], hints: dict[str, list[str]] | None) -> dict[str, list[HintMatch]]:
    """Match all provided hints against the input token stream."""
    if not hints:
        return {}

    matched: dict[str, list[HintMatch]] = {}
    for tagd_pos, values in hints.items():
        matched[tagd_pos] = [_match_hint(tokens, tagd_pos, value) for value in values]
    return matched


def _remove_hint_span(tokens: list[PosToken], hint_match: HintMatch) -> list[PosToken]:
    """Return tokens with the matched hint span removed."""
    return tokens[: hint_match.start] + tokens[hint_match.end :]


def _parse_quantified_object_relation(subject: PosToken, tail_tokens: list[PosToken]) -> Relation | None:
    """Parse `subject has 4 legs and a tail`-like shape into a single relation."""
    if len(tail_tokens) < 6:
        return None

    relator, qty, quantified_obj, conjunction, *rest = tail_tokens
    if qty.pos != "NUM":
        return None
    if quantified_obj.pos not in _SUBJECT_POS:
        return None
    if conjunction.pos != "CCONJ":
        return None

    remainder = [token for token in rest if token.pos != "DET"]
    if len(remainder) != 1:
        return None
    trailing_obj = remainder[0]
    if trailing_obj.pos not in _SUBJECT_POS:
        return None

    return Relation(
        subject=subject.text.lower(),
        relator=_taglize([relator]),
        obj=f"{quantified_obj.text.lower()} = {qty.text.lower()}, {trailing_obj.text.lower()}",
    )


def parse_relation(tokens: list[PosToken], forced_subject: str | None = None) -> Relation:
    """Parse POS-tagged text into a `subject relator object` relation shape."""
    lexical_tokens = [token for token in tokens if token.pos != "PUNCT"]

    if lexical_tokens and lexical_tokens[0].pos == "DET":
        lexical_tokens = lexical_tokens[1:]

    if forced_subject is not None:
        if not lexical_tokens:
            raise TranslationError("Unsupported input: missing relation after hinted subject")

        fallback_object = _taglize(lexical_tokens)
        if not fallback_object:
            raise TranslationError("Unsupported input: invalid gloss fragment")

        if len(lexical_tokens) >= 2 and lexical_tokens[-1].pos in _OBJECT_POS:
            relator_tokens = lexical_tokens[:-1]
            relator = _taglize(relator_tokens)
            if relator:
                return Relation(subject=forced_subject, relator=relator, obj=lexical_tokens[-1].text.lower())

        return Relation(subject=forced_subject, relator="_rel", obj=fallback_object)

    if len(lexical_tokens) < 3:
        raise TranslationError("Unsupported input: expected at least subject, relator, and object")

    subject = lexical_tokens[0]
    relator_tokens = lexical_tokens[1:-1]
    obj = lexical_tokens[-1]

    if subject.pos not in _SUBJECT_POS:
        raise TranslationError("Unsupported input: subject must be noun-like")

    quantified_relation = _parse_quantified_object_relation(subject, lexical_tokens[1:])
    if quantified_relation is not None:
        return quantified_relation

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


def rule_relations(relations: list[Relation]) -> str:
    """Translate one or more parsed relations into TAGL output."""
    if not relations:
        raise TranslationError("Unsupported input: no relation to emit")

    if len(relations) == 1:
        return rule_relation(relations[0])

    subject = relations[0].subject
    lines = [f">> {subject} {relations[0].relator} {relations[0].obj}"]

    for relation in relations[1:]:
        if relation.subject == subject:
            lines.append(f"{relation.relator} {relation.obj}")
        else:
            lines.append(f">> {relation.subject} {relation.relator} {relation.obj}")

    lines[-1] = f"{lines[-1]};"
    return "\n".join(lines)


def _split_on_comma(tokens: list[PosToken]) -> list[list[PosToken]]:
    """Split token stream into segments using comma punctuation."""
    segments: list[list[PosToken]] = []
    current: list[PosToken] = []
    for token in tokens:
        if token.pos == "PUNCT" and token.text == ",":
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments or [tokens]


def _normalize_clause_tokens(tokens: list[PosToken]) -> list[PosToken]:
    """Drop punctuation and optional leading determiner from a clause."""
    lexical_tokens = [token for token in tokens if token.pos != "PUNCT"]
    if lexical_tokens and lexical_tokens[0].pos == "DET":
        lexical_tokens = lexical_tokens[1:]
    return lexical_tokens


def _parse_clause_relations(
    clause_tokens: list[PosToken], inherited_subject: PosToken | None = None
) -> list[Relation]:
    """Parse one clause into one or more relations, using subject inheritance if needed."""
    if not clause_tokens:
        return []

    tokens = clause_tokens
    if tokens[0].pos not in _SUBJECT_POS and inherited_subject is not None:
        tokens = [inherited_subject, *tokens]

    subject_token = tokens[0]
    if subject_token.pos in _SUBJECT_POS:
        quantified_relation = _parse_quantified_object_relation(subject_token, tokens[1:])
        if quantified_relation is not None:
            return [quantified_relation]

    conjunction_indexes = [
        idx
        for idx, token in enumerate(tokens)
        if token.pos == "CCONJ" and token.text.lower() == "and"
    ]
    if conjunction_indexes:
        split_idx = conjunction_indexes[0]
        left_clause = tokens[:split_idx]
        right_clause = tokens[split_idx + 1 :]
        if not left_clause or not right_clause:
            raise TranslationError("Unsupported input: invalid conjunction structure")

        left_relation = parse_relation(left_clause)
        if right_clause[0].pos in _SUBJECT_POS:
            right_relation = parse_relation(right_clause)
        else:
            right_relation = parse_relation([left_clause[0], *right_clause])
        return [left_relation, right_relation]

    for idx, token in enumerate(tokens[1:], start=1):
        if token.pos not in {"PRON", "SCONJ"}:
            continue
        left_clause = tokens[:idx]
        right_clause = tokens[idx + 1 :]
        if not right_clause:
            continue
        try:
            left_relation = parse_relation(left_clause)
            if right_clause[0].pos in _SUBJECT_POS:
                right_relation = parse_relation(right_clause)
            else:
                right_relation = parse_relation([left_clause[0], *right_clause])
            return [left_relation, right_relation]
        except TranslationError:
            continue

    return [parse_relation(tokens)]


def parse_relations(tokens: list[PosToken]) -> list[Relation]:
    """Parse one or more relation clauses, including subject inheritance across clauses."""
    clauses = _split_on_comma(tokens)

    if len(clauses) == 1:
        return _parse_clause_relations(_normalize_clause_tokens(clauses[0]))

    relations: list[Relation] = []
    subject_token: PosToken | None = None

    for clause in clauses:
        clause_tokens = _normalize_clause_tokens(clause)
        if not clause_tokens:
            continue

        clause_relations = _parse_clause_relations(
            clause_tokens, inherited_subject=subject_token
        )
        relations.extend(clause_relations)

        if clause_tokens[0].pos in _SUBJECT_POS:
            subject_token = clause_tokens[0]

    if not relations:
        raise TranslationError("Unsupported input: no relation to emit")

    return relations


def translate(
    text: str,
    hints: dict[str, list[str]] | None = None,
    alt_tagger: Callable[[str], list[PosToken]] | None = None,
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

    matched_hints = match_hints(tokens, hints)
    subject_hints = matched_hints.get("subject", [])
    if len(subject_hints) > 1:
        raise TranslationError("Unsupported input: only one subject hint is currently supported")
    if subject_hints:
        subject_hint = subject_hints[0]
        subject = "_".join(_hint_value_tokens(subject_hint.value))
        gloss_tokens = _remove_hint_span(tokens, subject_hint)
        return rule_relation(parse_relation(gloss_tokens, forced_subject=subject))

    relations = parse_relations(tokens)
    return rule_relations(relations)


def main() -> int:
    """
    Read natural language from STDIN, normalize, translate,
    and write TAGL to to STDOUT.

    Returns:
        Process exit status code.
    """
    parser = argparse.ArgumentParser(prog="tagr", add_help=True)
    parser.add_argument(
        "--hint",
        action="append",
        default=[],
        metavar="<tagd_pos>=<value>",
        help="Constrain translation with a text-grounded tagd POS hint.",
    )
    args = parser.parse_args()

    raw_text = sys.stdin.read()

    if not raw_text.strip():
        return 0

    normalized = normalize(raw_text)

    try:
        output = translate(normalized, hints=parse_hint_args(args.hint))
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
