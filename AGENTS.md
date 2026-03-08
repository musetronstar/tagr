# AGENTS.md

## Purpose

`tagr` is a Python program that translates English text from `STDIN` into TAGL on `STDOUT`.

## Goal

Build a deterministic, test-driven pipeline that:

1. reads English text from `STDIN`
2. normalizes input
3. performs NLP analysis (tokenization + NLP POS tagging)
4. extracts structural relations
5. applies pure translation rules
6. emits valid TAGL output on `STDOUT`

## Terminology

Three concepts must not be conflated.

### NLP POS

Part-of-speech tags produced by the NLP engine.

Examples:

- spaCy POS (`token.pos_`)
- Universal Dependencies POS classes (`DET`, `NOUN`, `VERB`, `ADJ`, `ADV`)

Use the terms `NLP POS` or `spaCy POS` when relevant.

### tagd Repository

During development, the `tagd` repository is assumed to exist at:

`../tagd/`


### PUT Grammar

`../tagd/README.md` contains BNF grammar examples for TAGL statements:

```
put_statement ::= ">>" subject_sub_relation relations
put_statement ::= ">>" subject_sub_relation
put_statement ::= ">>" subject relations

subject_sub_relation ::= subject SUB TAG

subject ::= TAG

relations ::= relations predicate_list
relations ::= predicate_list

predicate_list ::= relator object_list

relator ::= TAG

object_list ::= object_list ',' object
object_list ::= object

object ::= TAG EQUALS QUANTIFIER
object ::= TAG EQUALS MODIFIER
object ::= TAG EQUALS QUOTED_STR
object ::= TAG
```

However, the canonical productions, terminals, and parser terminology are defined in:

`../tagd/tagl/src/parser.y`

Use `README.md` for quick orientation and `parser.y` as the source of truth.

### tagd POS

Semantic tag types defined by tagd, for example:

- `tagd::POS_RELATOR`
- `tagd::POS_SUB_RELATOR`
- `tagd::POS_TAG`

### Naming guidance

Code, tests, comments, and docs should clearly distinguish:

- `NLP POS`
- `TAGL grammar terms`
- `tagd POS`

Prefer names that make the layer obvious, e.g.:

- `nlp_pos_sequence`
- `tagl_relator`
- `tagd_pos_type`

## Translation Contract

`tagr` is a deterministic structural translator.

Input may include:

- normal sentences
- dictionary-like definitions
- sparse phrases or fragments

Output must be syntactically valid TAGL PUT statement shapes.

Agents must:

- translate by structure, not guesswork
- extract deterministic `subject relator object` shapes from NLP POS structures
- prefer best-effort valid TAGL when a clear structural relation exists
- implement translation rules as small, testable, pure functions
- rely on POS classes and structural patterns rather than literal words

Agents must not:

- invent semantic meaning not supported by structure
- hard-code English lexical tokens as grammar rules
- couple translation logic to specific hard TAGL tags such as `_is_a`
- reject input merely because it is not a complete sentence

If no deterministic relation shape can be constructed, raise an explicit error.

Target processing model:

`input text -> best-effort POS/structure analysis -> valid TAGL-shaped output`

Not:

`input text -> strict natural-language validation -> failure`

## Scope

Initial scope should remain intentionally narrow.

The system should:

- support a small subset of English grammar first
- expand incrementally toward Universal Dependencies
- remain deterministic
- separate parsing from I/O
- keep NLP engine details behind an adapter layer

The system should not:

- attempt full natural-language understanding
- silently guess ambiguous meaning
- become a monolithic translator

## Design Principles

- TDD first
- small pure functions
- deterministic translation
- composable pipeline
- clear error behavior
- NLP adapter boundary

## Architecture

Current repository layout:

```text
tagr/
  tagr.py
  test_tagr.py
```

Logical areas of concern:

- `cli` - STDIN -> pipeline -> STDOUT
- `normalize` - input normalization
- `nlp` - NLP adapter (spaCy)
- `parse` - structural parsing
- `rules` - translation rules
- `emit` - TAGL formatting
- `models` - internal structures
- `errors` - translation errors

Modules may be introduced gradually as the system evolves.

## Development Workflow

Development should be incremental and test-driven.

Rules:

- add or update tests first
- prefer minimal, reviewable diffs
- prefer modifying existing code before introducing new abstractions
- avoid broad speculative refactors unless they clearly support the requested change

Exploration documents under `docs/` (for example, `docs/voa-starter-grammar.md`) are non-normative.
`AGENTS.md` plus repository tests define current required behavior.

## Dependency Policy

Dependencies should remain minimal.

Approved dependencies:

- spaCy
- pytest

Do not introduce additional dependencies without clear justification.

### Future NLP engines

spaCy is the initial NLP engine.

If spaCy becomes limiting, especially for:

- strict Universal Dependencies alignment
- richer morphological features
- multilingual UD consistency

maintainers should evaluate Stanza.

spaCy must remain behind an adapter boundary so the NLP engine can be replaced.

## TAGL Grammar Grounding

`tagr` translation logic must be grounded in:

`../tagd/tagl/src/parser.y`

This grammar is the canonical source for:

- production names
- terminal names
- parser terminology
- relation terminology used in code, comments, tests, and docs

Agents should:

- follow `parser.y` naming for TAGL-side structures
- prefer TAGL grammar terminology over ad hoc wording for TAGL-side structure
- keep NLP terms for NLP-side analysis only
- keep tagd terms for tagd semantic validation only

Agents should not:

- invent alternate parser terminology when grammar terms already exist
- introduce naming that drifts from `parser.y` without reason
- use English surface labels when a TAGL grammar name is available

## spaCy Integration Rules

- use spaCy as an NLP provider, not project semantics owner
- convert spaCy tokens/tags/dependencies into internal models before rules
- do not let spaCy objects leak across the codebase
- keep grammar and TAGL mapping logic independent from spaCy APIs where practical

## Architectural Rules

- keep I/O separate from translation logic
- keep translation rules small and pure
- keep behavior deterministic
- use internal intermediate data structures
- follow TAGL grammar naming from `parser.y` for TAGL-side names
- use `sub` / `subordinate relation` terminology for parser-rule design where applicable

TAGL output target shape:

`>> <subject> <relator> <object>;`

Relator construction should be shape-driven TAGLization (e.g., joining relator token sequences with `_`).

When multiple objects share the same relator, emit one `predicate_list` with an `object_list`:

`>> <subject> <relator> <object_a>, <object_b>;`

Emit each PUT statement on a single line on `STDOUT`.

Semantic validation using tagd POS is deferred to tagd/tagdb execution time. `tagr` is responsible for deterministic structural translation.

In this prototype stage, structural translation is primary; strict semantic validation modes may be added later.

If a structural relation exists but no explicit relator can be deterministically extracted, `_rel` is the only allowed fallback relator.

## Coding Rules

- Python only
- small focused functions
- avoid monolithic translator functions
- type hints where practical
- readable code over clever code
- minimal dependencies

Code should clearly distinguish NLP POS, TAGL grammar terms, and tagd POS.

## Rule Design

Translation rules should be decomposed into:

- normalization
- token recognition
- NLP POS pattern matching
- phrase recognition
- relation-shape extraction (`subject`, `relator`, `object`)
- TAGL emission

Each rule should:

- declare or make clear the NLP POS pattern it matches
- use TAGL grammar terminology where applicable
- have explicit inputs and outputs
- be testable in isolation
- avoid side effects
- avoid hidden global state
- remain language-portable by relying on POS classes/structures rather than lexical literals

For starter grammar growth, prefer explicit rule profiles backed by tests (for example: adjective-phrase definitions, `to VERB` chains, and noun-gloss synonym shapes).

Grammar behavior should be traceable:

`test -> rule -> emitted TAGL`

## Error Handling

- do not invent ambiguous meaning
- unsupported input should produce explicit errors
- diagnostics belong on `STDERR`
- `STDOUT` should contain only valid TAGL output

## Testing

Tests should cover:

- normalization
- NLP adapter behavior
- parse/grammar recognition
- translation rules
- TAGL emission
- end-to-end translation

Every behavior change should include tests.

## Avoid

- speculative refactors
- premature broad English coverage
- hidden heuristics
- mixing CLI and parsing/translation concerns
- unnecessary dependencies
