#!/usr/bin/env python3
"""
test_tagr.py

Unit tests for `tagr.py`
"""

from __future__ import annotations

import io

import pytest

import tagr
from tagr import PosToken, Relation, TranslationError, normalize, parse_relation, rule_relation, translate


def test_normalize_strips_outer_whitespace() -> None:
    assert normalize("  A dog is a mammal. \n") == "A dog is a mammal."


def test_normalize_empty_string() -> None:
    assert normalize("") == ""


def test_parse_relation_subordinate_shape() -> None:
    tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
        PosToken(text=".", pos="PUNCT"),
    ]

    assert parse_relation(tokens) == Relation(subject="dog", relator="is_a", obj="mammal")


def test_parse_relation_predicate_shape() -> None:
    tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="can", pos="AUX"),
        PosToken(text="bark", pos="VERB"),
        PosToken(text=".", pos="PUNCT"),
    ]

    assert parse_relation(tokens) == Relation(subject="dog", relator="can", obj="bark")


def test_parse_relation_rejects_invalid_shape() -> None:
    tokens = [
        PosToken(text="quickly", pos="ADV"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="bark", pos="VERB"),
    ]

    with pytest.raises(TranslationError):
        parse_relation(tokens)


def test_rule_relation_emits_tagl_statement() -> None:
    relation = Relation(subject="dog", relator="is_a", obj="mammal")
    assert rule_relation(relation) == ">> dog is_a mammal;"


def test_translate_subordinate_example() -> None:
    fake_tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
    ]

    assert (
        translate("A dog is a mammal.", pos_tagger=lambda _text: fake_tokens)
        == ">> dog is_a mammal;"
    )


def test_translate_predicate_example() -> None:
    fake_tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="can", pos="AUX"),
        PosToken(text="bark", pos="VERB"),
    ]

    assert (
        translate("A dog can bark.", pos_tagger=lambda _text: fake_tokens)
        == ">> dog can bark;"
    )


def test_main_writes_translated_output_with_newline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("A dog can bark."))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr(
        tagr,
        "pos_tag",
        lambda _text: [
            PosToken(text="A", pos="DET"),
            PosToken(text="dog", pos="NOUN"),
            PosToken(text="can", pos="AUX"),
            PosToken(text="bark", pos="VERB"),
        ],
    )

    assert tagr.main() == 0
    assert out.getvalue() == ">> dog can bark;\n"


def test_main_reports_errors_to_stderr_and_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("quickly dog bark"))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    err = io.StringIO()
    monkeypatch.setattr("sys.stderr", err)
    monkeypatch.setattr(
        tagr,
        "pos_tag",
        lambda _text: [
            PosToken(text="quickly", pos="ADV"),
            PosToken(text="dog", pos="NOUN"),
            PosToken(text="bark", pos="VERB"),
        ],
    )

    assert tagr.main() == 1
    assert "unsupported input" in err.getvalue().lower()
