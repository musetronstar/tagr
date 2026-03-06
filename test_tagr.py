#!/usr/bin/env python3
"""
test_tagr.py

Unit tests for `tagr.py`
"""

from __future__ import annotations

import io

import pytest

import tagr
from tagr import PosToken, SubRelation, TranslationError, normalize, parse_sub_relation, rule_sub_relation, translate


def test_normalize_strips_outer_whitespace() -> None:
    assert normalize("  A dog is an animal. \n") == "A dog is an animal."


def test_normalize_empty_string() -> None:
    assert normalize("") == ""


def test_parse_sub_relation_recognizes_subject_aux_det_object() -> None:
    tokens = [
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
    ]

    assert parse_sub_relation(tokens) == SubRelation(subject="dog", sub="_sub", obj="mammal")


def test_parse_sub_relation_rejects_unsupported_shape() -> None:
    tokens = [
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="can", pos="AUX"),
        PosToken(text="bark", pos="VERB"),
    ]

    with pytest.raises(TranslationError):
        parse_sub_relation(tokens)


def test_rule_sub_relation_emits_tagl_statement() -> None:
    relation = SubRelation(subject="dog", sub="_sub", obj="mammal")
    assert rule_sub_relation(relation) == ">> dog _sub mammal;"


def test_translate_sub_sentence() -> None:
    fake_tokens = [
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="is", pos="AUX"),
        PosToken(text="a", pos="DET"),
        PosToken(text="mammal", pos="NOUN"),
    ]
    assert (
        translate("dog is a mammal", pos_tagger=lambda _text: fake_tokens)
        == ">> dog _sub mammal;"
    )


def test_translate_raises_for_unsupported_input() -> None:
    fake_tokens = [
        PosToken(text="dog", pos="NOUN"),
        PosToken(text="can", pos="AUX"),
        PosToken(text="bark", pos="VERB"),
    ]

    with pytest.raises(TranslationError):
        translate("dog can bark", pos_tagger=lambda _text: fake_tokens)


def test_main_writes_translated_output_with_newline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("dog is a mammal"))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    monkeypatch.setattr(
        tagr,
        "pos_tag",
        lambda _text: [
            PosToken(text="dog", pos="NOUN"),
            PosToken(text="is", pos="AUX"),
            PosToken(text="a", pos="DET"),
            PosToken(text="mammal", pos="NOUN"),
        ],
    )

    assert tagr.main() == 0
    assert out.getvalue() == ">> dog _sub mammal;\n"


def test_main_reports_errors_to_stderr_and_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("dog can bark"))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    err = io.StringIO()
    monkeypatch.setattr("sys.stderr", err)
    monkeypatch.setattr(
        tagr,
        "pos_tag",
        lambda _text: [
            PosToken(text="dog", pos="NOUN"),
            PosToken(text="can", pos="AUX"),
            PosToken(text="bark", pos="VERB"),
        ],
    )

    assert tagr.main() == 1
    assert "unsupported input" in err.getvalue().lower()
