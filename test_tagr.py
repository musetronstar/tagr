#!/usr/bin/env python3
"""
test_tagr.py

Unit tests for `tagr.py` 
"""

from __future__ import annotations

from tagr import normalize, translate

def test_normalize_strips_outer_whitespace() -> None:
    assert normalize("  A dog is an animal. \n") == "A dog is an animal."


def test_normalize_empty_string() -> None:
    assert normalize("") == ""

# TODO this goes away when we have TAGL to test
def test_translate_stub_returns_input_unchanged() -> None:
    assert translate("A dog is an animal.") == "A dog is an animal."