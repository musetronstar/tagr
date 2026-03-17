# Corpus-Driven Test Strategy

This document records the next-step design for adding corpus-driven regression
tests alongside the existing unit-test workflow in `tagr`.

The goal is to keep `tagr` test-driven while also building a larger,
example-driven corpus of real translation inputs, including sparse gloss
fragments, hinted inputs, and known failures discovered during development.

## Why Add Corpus Tests

Unit tests are still the primary tool for:

- parser behavior
- hint parsing
- relation formatting
- small pure rule functions

Corpus tests add a second layer:

- end-to-end translation checks
- regression coverage across many real examples
- permanent capture of previously failing or problematic inputs

This is especially useful for short gloss fragments and hint-driven
translation, where behavior evolves through repeated contact with real data.

## Core Idea

Store translation cases in data files and run them through a generic pytest
runner.

Each corpus case should describe:

- the input text
- any hints
- the expected output, or the expected error
- a short note about why the case exists

When a real-world input fails or produces weak output, add it to the corpus
first, then improve the implementation and keep the case as a regression test.

## Proposed Case Schema

YAML is a reasonable format because it is easy to edit by hand.

Example:

```yaml
- id: simple-taxonomy
  input: "A dog is an animal."
  hints: []
  expected: ">> dog is_an animal;"
  notes: "simple taxonomy"

- id: hinted-gloss-against
  input: "against opposed to"
  hints:
    - "subject=against"
  expected: ">> against _rel opposed_to;"
  notes: "gloss fragment with subject hint"

- id: unsupported-fragment
  input: "very quickly and silently"
  hints: []
  error: "Unsupported input"
  notes: "no deterministic relation shape"
```

Recommended fields:

- `id`: stable identifier for the case
- `input`: source text passed to `tagr`
- `hints`: optional list of `--hint <tagd_pos>=<value>` values
- `expected`: exact expected TAGL output for a successful translation
- `error`: expected error substring for unsupported input
- `notes`: short explanation of the case

Rules:

- each case should use `expected` or `error`, but not both
- exact output matching is preferred for now because formatting is part of the
  current contract
- hint values should remain text-grounded and present in `input`

## Suggested Layout

Start simple, then split by category as the corpus grows.

Initial option:

```text
tagr/
  corpus/
    cases.yaml
```

Later split if needed:

```text
tagr/
  corpus/
    sentences.yaml
    glosses.yaml
    hints.yaml
    failures.yaml
```

## Test Runner Shape

Add a pytest module, for example:

```text
test_corpus.py
```

The runner should:

1. load YAML cases
2. convert `hints` into the internal `dict[str, list[str]]` shape
3. call `translate(input, hints=...)`
4. assert exact `expected` output, or assert the expected error substring

The runner should stay thin. The corpus file is the main artifact.

## Relationship to TDD

Corpus-driven development does not replace TDD.

Recommended workflow:

1. discover a failing or weak real input
2. add it to the corpus as a regression case
3. add or refine focused unit tests for the underlying rule
4. implement the fix
5. keep both the unit test and the corpus case

This gives:

- local confidence from unit tests
- broader regression confidence from corpus tests

## Near-Term Next Steps

1. add `corpus/cases.yaml`
2. add `test_corpus.py`
3. seed the corpus with:
   - simple sentence cases already supported
   - hint-driven gloss cases
   - expected-failure cases
4. add newly discovered problematic inputs as development continues
