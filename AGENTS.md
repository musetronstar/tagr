# AGENTS.md

## Purpose

This repository contains a Python program named `tagr` that we intent to
translate English text from `STDIN` into TAGL on `STDOUT`.

## Goal

Build a small, test-driven pipeline that:

1. reads English from `STDIN`
2. cleans and normalizes the text
3. tokenizes and POS-tags it with spaCy
4. parses supported grammar structures
5. applies pure translation rules
6. writes valid TAGL to `STDOUT`

## Scope

Start intentionally narrow.

It should:

- start with a very small subset of English sentence patterns,
  but eventually support Universal Dependencies
- use deterministic translation rules
- break translation into small pure functions
- keep grammar recognition separate from I/O
- use spaCy as the NLP layer for tokenization, POS tagging, and parsing

It should not:

- try to understand arbitrary natural language
- silently guess when input is ambiguous
- mix parsing logic with CLI code
- become one large “magic” translation function
- let spaCy-specific objects leak through the whole codebase

## Design Principles

- **TDD first**: each supported grammar pattern begins with tests
- **Small pure functions**: rules should behave like grammar terminals and productions
- **Composable pipeline**: normalization, NLP, parsing, translation, and emission stay separate
- **Deterministic output**: the same input should produce the same TAGL
- **Fail clearly**: unsupported or ambiguous input should be reported explicitly
- **NLP adapter boundary**: spaCy provides linguistic analysis, while `tagr` owns the translation semantics

## Initial Architecture

```text
tagr/
  tagr.py         # main entry point
  test_tagr.py    # unit tests
```

### Sections (Areas of Concern)

Whether as functions, classes or modules here are the areas of concern:

- cli          # STDIN -> pipeline -> STDOUT
- normalize    # cleaning and normalization
- nlp          # spaCy adapter layer
- parse        # parse structures / grammar units
- rules        # pure translation rules
- emit         # TAGL output formatting
- models       # internal data structures
- errors       # translation / parse errors

## Dependency Strategy

Keep dependencies minimal but practical.

Core dependencies:

- **spaCy** for tokenization, POS tagging, and dependency parsing
- **pytest** for tests

Use spaCy only as the NLP layer. Convert spaCy output into internal project data structures such as tokens, phrases, and sentence representations before applying translation rules.

## Testing Strategy

- unit tests for normalization
- unit tests for NLP adapter output shaping
- unit tests for parse-unit recognition
- unit tests for each pure translation rule
- unit tests for TAGL emission
- end-to-end tests from English input to TAGL output

## Development Style

Use an iterative, test-driven development approach.

For each new feature:

1. write or update tests first
2. implement the smallest change needed
3. refactor only after tests pass

## Priorities

Focus on a narrow but clean pipeline:

- read from `STDIN`
- normalize input
- analyze text with spaCy
- convert spaCy output into internal structures
- parse supported grammar units
- translate parse structures into TAGL
- write TAGL to `STDOUT`

## Dependency Policy

Keep dependencies minimal, but be pragmatic.

Approved core dependencies:

- **spaCy** for tokenization, POS tagging, and dependency parsing
- **pytest** for automated testing

Do not add new dependencies without clear justification.

### Future NLP Engine Considerations

spaCy is the initial NLP engine because it offers a practical and productive development experience.

However, `tagr` should remain architecturally capable of switching NLP backends.

If spaCy becomes limiting—particularly regarding:

- strict **Universal Dependencies (UD)** requirements
- richer **morphological features**
- **multilingual UD consistency**
- or any feature where **Stanza provides a clearly superior implementation**

then maintainers should evaluate adding or replacing the NLP adapter with **Stanza**.

This is why spaCy must remain **behind an adapter boundary** so the NLP engine can be swapped with minimal impact on the rest of the system.

## Architectural Rules

- Keep I/O separate from translation logic.
- Keep translation rules as small pure functions.
- Organize rules analogously to grammar terminals and productions.
- Use internal intermediate data structures rather than directly transforming raw text into TAGL strings.
- Make rule composition explicit and testable.
- Prefer deterministic behavior over cleverness.
- Keep spaCy behind an adapter boundary.

## spaCy Integration Rules

- Use spaCy as an NLP provider, not as the owner of project semantics.
- Convert spaCy tokens, tags, and dependencies into internal project models before applying translation rules.
- Avoid spreading direct spaCy object usage throughout the codebase.
- Keep grammar and TAGL mapping rules independent from spaCy-specific APIs wherever practical.

## Coding Rules

- Python only
- small functions
- no giant monolithic translator function
- type hints where practical
- minimal dependencies
- keep modules focused on one responsibility
- write readable code over clever code

## Rule Design Expectations

Translation rules should be broken into building blocks.

Examples of desirable decomposition:

- normalization rules
- token-level recognition
- POS-based matching
- phrase-level recognition
- sentence-pattern recognition
- TAGL emission

Each rule should:

- have a clear input and output
- be testable in isolation
- avoid side effects
- avoid hidden global state

## Error Handling

- Do not silently invent meaning for ambiguous input.
- Fail clearly when input is unsupported.
- Surface errors through explicit return values or exceptions.
- Preserve debuggability.
- Do not pollute `STDOUT` with diagnostics.

## Output Rules

- Final output must be valid TAGL text on `STDOUT`.
- Diagnostics and debug information belong on `STDERR` or in tests.
- Keep TAGL formatting consistent and deterministic.

## Testing Requirements

Add or update tests for every behavior change.

At minimum, cover:

- normalization
- NLP adapter shaping
- parse-unit recognition
- translation rules
- TAGL emission
- end-to-end pipeline behavior

## Avoid

- large speculative refactors
- premature support for broad English coverage
- hidden guessing
- mixing parsing, translation, and CLI concerns
- introducing heavy dependencies without clear need
