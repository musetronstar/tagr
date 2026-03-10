from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


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
