
# Using a Repository of Tests for `tagr`

For a translator like **tagr**, one of the most valuable long‑term assets is a
**corpus of input → expected output examples**.

This corpus effectively becomes:

- the **specification**
- the **regression test suite**
- a **grammar discovery tool**

Over time, the corpus often becomes **more important than the code** itself.

---

# 1. Example Test Corpus Format

A simple YAML format works well:

```yaml
- input: "A dog is an animal."
  expected: ">> dog is_a animal;"
  notes: "simple taxonomy"

- input: "Socrates is a man."
  expected: ">> Socrates is_a man;"
  notes: "instance/class"

- input: "A wheel is part of a car."
  expected: ">> wheel part_of car;"
  notes: "part-whole relation"
```

Advantages:

- human readable
- easy to expand
- works well with pytest

---

# 2. Integrating the YAML Corpus with pytest

Suggested project layout:

```
tagr/
  tagr.py
  test_tagr.py
  tests/
      corpus_basic.yaml
      corpus_edge.yaml
```

Example pytest integration:

```python
import yaml
import pytest
from tagr import translate

def load_cases():
    with open("tests/corpus_basic.yaml") as f:
        cases = yaml.safe_load(f)

    return [
        pytest.param(case["input"], case["expected"], id=case.get("notes", case["input"]))
        for case in cases
    ]

@pytest.mark.parametrize("text, expected", load_cases())
def test_translation(text, expected):
    assert translate(text) == expected
```

Benefits:

- each corpus entry becomes an independent pytest test
- failures are easy to identify
- thousands of examples scale naturally

---

# 3. Example‑Driven Grammar Discovery

Instead of designing a large grammar up front:

```
design rules → write tests
```

you invert the process:

```
add failing example
→ implement minimal rule
→ run corpus
→ refactor rules
```

This is **true TDD for language translators**.

---

# 4. Why the Brown Corpus Is Not Ideal

The **Brown Corpus** is historically important but not ideal for `tagr`.

Reasons:

1. sentences are long prose
2. grammar is complex and stylistic
3. not optimized for semantic relations

Example Brown sentence:

```
The Fulton County Grand Jury said Friday an investigation of Atlanta's
recent primary election produced no evidence that any irregularities
took place.
```

This does not map well to the simple TAGL structure:

```
subject relator object
```

---

# 5. Better Corpus Sources

Corpora emphasizing **definitions and relations** are more useful.

## Dictionary corpora

- VOA Wordbook
- WordNet glosses
- Wiktionary definitions

Example:

```
dog: a domesticated carnivorous mammal
```

---

## Wikipedia lead sentences

First sentences are often definitional:

```
A dog is a domesticated mammal.
```

These map very cleanly to taxonomy relations.

---

## Wikidata / DBpedia triples

Structured relations such as:

```
dog instance_of mammal
wheel part_of car
```

These can be converted into natural language test inputs.

---

## Simple English Wikipedia

Probably one of the best corpus sources.

Reasons:

- simplified grammar
- short sentences
- definitional style

Example:

```
A cat is a small carnivorous mammal.
```

---

# 6. Organizing Corpus Tests

Instead of one huge corpus file, organize them by semantic category:

```
tests/
  corpus/
      taxonomy.yaml
      definitions.yaml
      relations.yaml
      predicates.yaml
      edge_cases.yaml
```

Example:

## taxonomy.yaml

```yaml
- input: "A dog is an animal."
  expected: ">> dog is_a animal;"

- input: "A whale is a mammal."
  expected: ">> whale is_a mammal;"
```

## relations.yaml

```yaml
- input: "A wheel is part of a car."
  expected: ">> wheel part_of car;"

- input: "A key opens a door."
  expected: ">> key opens door;"
```

---

# 7. Categories of Tests

Over time the corpus should include multiple test types.

## Gold tests

Exact output must match.

```
dog is an animal
→ >> dog is_a animal;
```

---

## Tolerance tests

Only structural validity required.

Example:

```
>> subject relator object;
```

Useful for ambiguous language.

---

## Regression tests

Examples that previously failed.

Example:

```
dog is animal
```

If it ever breaks again, the test will catch it.

---

# 8. Long‑Term Vision

Eventually this corpus could become a standalone dataset:

```
tagr-corpus
```

Containing:

- thousands of relational sentences
- expected TAGL translations
- edge cases and ambiguous structures

Such a dataset would be extremely valuable for:

- testing translators
- experimenting with NLP parsing
- validating semantic extraction systems

---

# 9. Optional Corpus Runner

A CLI tool can help run corpus tests quickly:

```
tagr --corpus tests/corpus_basic.yaml
```

Example output:

```
PASS dog is an animal
PASS Socrates is a man
FAIL wheel part_of car
```

This can speed up grammar experimentation outside of pytest.

---

# Key Idea

For a project like `tagr`, the **growing example corpus is the real product**.

The translator improves by repeatedly asking:

```
Does this rule handle the examples?
```

rather than:

```
Does this grammar theory seem correct?
```
