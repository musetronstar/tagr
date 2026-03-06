#!/usr/bin/env python3
"""
test_tagr.py

Unit tests for `tagr.py`
"""

from __future__ import annotations

import io

import pytest

import tagr
from tagr import IsARelation, TranslationError, normalize, parse_is_a, rule_is_a, translate


def test_normalize_strips_outer_whitespace() -> None:
    assert normalize("  A dog is an animal. \n") == "A dog is an animal."


def test_normalize_empty_string() -> None:
    assert normalize("") == ""


def test_parse_is_a_recognizes_simple_pattern() -> None:
    assert parse_is_a("dog is a mammal") == IsARelation(subject="dog", obj="mammal")


def test_parse_is_a_recognizes_an_article() -> None:
    assert parse_is_a("dog is an animal") == IsARelation(subject="dog", obj="animal")


def test_rule_is_a_emits_tagl_statement() -> None:
    relation = IsARelation(subject="dog", obj="mammal")
    assert rule_is_a(relation) == ">> dog is_a mammal;"


def test_translate_is_a_sentence() -> None:
    assert translate("dog is a mammal") == ">> dog is_a mammal;"


def test_translate_raises_for_unsupported_input() -> None:
    with pytest.raises(TranslationError):
        translate("dog can bark")


def test_main_writes_translated_output_with_newline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("dog is a mammal"))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)

    assert tagr.main() == 0
    assert out.getvalue() == ">> dog is_a mammal;\n"


def test_main_reports_errors_to_stderr_and_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("dog can bark"))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    err = io.StringIO()
    monkeypatch.setattr("sys.stderr", err)

    assert tagr.main() == 1
    assert "unsupported input" in err.getvalue().lower()
