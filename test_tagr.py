#!/usr/bin/env python3
"""
test_tagr.py

Unit tests for `tagr.py`
"""

from __future__ import annotations

import io

import pytest

import tagr
from tagr import (
    PosToken,
    Relation,
    TranslationError,
    normalize,
    parse_hint_args,
    parse_relation,
    rule_relation,
    translate,
)


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


def test_translate_subordinate() -> None:
    fake_tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
    ]

    assert (
        translate("A dog is a mammal.", alt_tagger=lambda _text: fake_tokens)
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
        translate("A dog can bark.", alt_tagger=lambda _text: fake_tokens)
        == ">> dog can bark;"
    )


def test_translate_predicate_with_modifier_quantifier() -> None:
    fake_tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="has", pos="VERB"),
        PosToken(text="4", pos="NUM"),
        PosToken(text="legs", pos="NOUN"),
        PosToken(text="and", pos="CCONJ"),
        PosToken(text="a", pos="DET"),
        PosToken(text="tail", pos="NOUN"),
        PosToken(text=".", pos="PUNCT"),
    ]

    assert (
        translate(
            "A dog has 4 legs and a tail.",
            alt_tagger=lambda _text: fake_tokens,
        )
        == ">> dog has legs = 4, tail;"
    )


def test_translate_subordinate_with_predicate() -> None:
    fake_tokens = [
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
        PosToken(text="and", pos="CCONJ"),
        PosToken(text="can", pos="AUX"),
        PosToken(text="bark", pos="VERB"),
    ]

    assert (
        translate(
            "dog is a mammal and can bark",
            alt_tagger=lambda _text: fake_tokens,
        )
        == ">> dog is_a mammal\ncan bark;"
    )


def test_translate_subordinate_with_predicate_and_modifier_quantifier() -> None:
    fake_tokens = [
        PosToken(text="A", pos="DET"),
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
        PosToken(text="that", pos="PRON"),
        PosToken(text="can", pos="AUX"),
        PosToken(text="bark", pos="VERB"),
        PosToken(text=",", pos="PUNCT"),
        PosToken(text="has", pos="VERB"),
        PosToken(text="4", pos="NUM"),
        PosToken(text="legs", pos="NOUN"),
        PosToken(text="and", pos="CCONJ"),
        PosToken(text="a", pos="DET"),
        PosToken(text="tail", pos="NOUN"),
        PosToken(text=".", pos="PUNCT"),
    ]

    assert (
        translate(
            "A dog is a mammal that can bark, has 4 legs and a tail.",
            alt_tagger=lambda _text: fake_tokens,
        )
        == ">> dog is_a mammal\ncan bark\nhas legs = 4, tail;"
    )


def test_parse_hint_args_collects_repeated_hints() -> None:
    assert parse_hint_args(["subject=age", "object=person", "object=thing"]) == {
        "subject": ["age"],
        "object": ["person", "thing"],
    }


def test_translate_uses_hinted_subject_for_gloss_fragment() -> None:
    fake_tokens = [
        PosToken(text="against", pos="ADP"),
        PosToken(text="opposed", pos="ADJ"),
        PosToken(text="to", pos="ADP"),
    ]

    assert (
        translate(
            "against opposed to",
            hints={"subject": ["against"]},
            alt_tagger=lambda _text: fake_tokens,
        )
        == ">> against _rel opposed_to;"
    )


def test_translate_errors_when_hint_value_not_present_in_input() -> None:
    fake_tokens = [
        PosToken(text="opposed", pos="ADJ"),
        PosToken(text="to", pos="ADP"),
    ]

    with pytest.raises(TranslationError, match="Hint value not found"):
        translate(
            "opposed to",
            hints={"subject": ["against"]},
            alt_tagger=lambda _text: fake_tokens,
        )


def test_main_writes_translated_output_with_newline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("A dog can bark."))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.argv", ["tagr.py"])
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
    monkeypatch.setattr("sys.argv", ["tagr.py"])
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


def test_main_accepts_subject_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("against opposed to"))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr("sys.stderr", io.StringIO())
    monkeypatch.setattr("sys.argv", ["tagr.py", "--hint", "subject=against"])
    monkeypatch.setattr(
        tagr,
        "pos_tag",
        lambda _text: [
            PosToken(text="against", pos="ADP"),
            PosToken(text="opposed", pos="ADJ"),
            PosToken(text="to", pos="ADP"),
        ],
    )

    assert tagr.main() == 0
    assert out.getvalue() == ">> against _rel opposed_to;\n"
