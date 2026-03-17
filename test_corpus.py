# test_corpus.py
"""
Generic corpus runner — discovers test_*.py in corpus/ and collects their cases().
"""

import pytest
from pathlib import Path
import importlib.util


def discover_cases():
    corpus_dir = Path(__file__).parent / "corpus"
    for py_file in sorted(corpus_dir.glob("*/test.py")):
        module_name = py_file.stem
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "cases"):
            for case in module.cases():
                yield pytest.param(
                    case,
                    id=f"{module_name}::{case.get('notes', case['input'][:30])}"
                )


@pytest.mark.parametrize("case", list(discover_cases()))
def test_corpus_case(case):
    from tagr import translate, parse_hint_args, TranslationError

    text = case["input"]
    hints_raw = case.get("hints", [])
    hints = parse_hint_args(hints_raw) if hints_raw else {}

    try:
        result = translate(text, hints=hints).strip()
        if "expected" in case:
            assert result == case["expected"].strip()
        else:
            pytest.fail("Expected error but got output")
    except TranslationError as e:
        if "error" in case:
            assert case["error"].lower() in str(e).lower()
        else:
            raise
