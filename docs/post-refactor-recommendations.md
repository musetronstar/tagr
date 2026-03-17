# Post-Refactor Recommendations

This document records recommendations after comparing the `claude-refactor`
and `codex-fresh` branches.

It is advisory only. [`AGENTS.md`](/home/inc/projects/tagr/AGENTS.md) and the
test suite remain the normative sources for current repository behavior.

## Summary

`codex-fresh` is the better refactor base.

Reason:

- it has cleaner module boundaries
- it has a stronger spaCy adapter boundary
- it improves test targeting around those boundaries

However, neither branch is aligned enough with the actual goal of translating
VOA Wordbook word + gloss entries from
[`../tagd-dictionary/word-list-defs.tsv`](/home/inc/projects/tagd-dictionary/word-list-defs.tsv)
into TAGL.

Neither branch should be merged as-is if the next milestone is real VOA
gloss translation.

## What `codex-fresh` Gets Right

### 1. Better separation of concerns

The split between CLI, NLP parsing, and TAGL emission is clearer:

- [`tagr.py`](/tmp/tagr-codex-fresh/tagr.py)
- [`nlp_parser.py`](/tmp/tagr-codex-fresh/nlp_parser.py)
- [`taglizer.py`](/tmp/tagr-codex-fresh/taglizer.py)

This is closer to the architecture described in
[`AGENTS.md`](/home/inc/projects/tagr/AGENTS.md):

- `cli`
- `normalize`
- `nlp`
- `parse`
- `rules`
- `emit`

### 2. Better NLP adapter behavior

`codex-fresh` wraps missing spaCy installation and missing model errors in
`TranslationError`, which is better operational behavior for a deterministic
CLI pipeline.

### 3. Better tests for module boundaries

The tests in `codex-fresh` verify module-level responsibilities directly
instead of continuing to treat `tagr.py` as the home of parser and emitter
logic.

## What `claude-refactor` Gets Right

### 1. More promising parser heuristics

`claude-refactor` has a somewhat better structural parser for the current toy
grammar:

- coordinated predicates
- relative-pronoun splits
- quantified object clauses

Its clause splitting is more POS-shape driven than `codex-fresh` in at least
one important way: it distinguishes predicate boundaries from object-list
continuations using token class and surrounding shape rather than splitting on
literal `"and"` alone.

### 2. Better basis for richer clause parsing

If the project were still optimizing for subject-first sentence examples such
as:

`A dog is a mammal that can bark, has 4 legs and a tail.`

then `claude-refactor` would be the better parsing base.

## Why Neither Branch Is Good Enough For The VOA Goal

The target corpus is not primarily made of complete English sentences.

Many rows in
[`word-list-defs.tsv`](/home/inc/projects/tagd-dictionary/word-list-defs.tsv)
look like:

- `able    having the power to do something`
- `accept  to agree to receive`
- `activist    one who seeks change through action`
- `accident    an unplanned event`

These glosses are fragments, not subject-first clauses.

Both branches currently assume the gloss text itself begins with a noun-like
subject. That causes both branches to reject representative VOA definitions.

This is the core design mismatch.

## Specific Problems To Avoid Carrying Forward

### 1. Subject-first parsing as the primary model

For Wordbook translation, the TSV `word` should usually become the TAGL
`subject`.

The gloss should be parsed as a structural definition fragment attached to that
subject.

Both branches currently treat the gloss as if it must independently contain
the subject.

### 2. TAGL emission that is not grammar-grounded enough

The canonical TAGL grammar is in
[`../tagd/tagl/src/parser.y`](/home/inc/projects/tagd/tagl/src/parser.y).

Relevant productions include:

- `put_statement`
- `subject_sub_relation`
- `predicate_list`
- `object_list`

Both branches currently emit multi-line predicate continuations such as:

```text
>> dog is_a mammal
can bark;
```

That is not aligned with the repo guidance to emit each PUT statement on a
single line, and it does not compact repeated relators into a canonical
`object_list` shape.

### 3. Over-reliance on toy tests

Both branches pass their own tests.

That is not enough.

The current tests mostly validate sentence-style examples built around:

- `A dog is a mammal`
- `A dog can bark`
- `A dog has 4 legs and a tail`

Those tests do not exercise the actual Wordbook workload strongly enough.

### 4. Ad hoc TAGL-side naming

Both branches use generic `Relation(subject, relator, obj)` structures.

That is workable as an intermediate model, but future code and tests should
move closer to the canonical grammar terminology from `parser.y` when dealing
with TAGL-side structure.

## Recommended Direction

Use `codex-fresh` as the refactor base, but do not keep its parser strategy as
the long-term translation model.

Recommended approach:

1. Keep the `codex-fresh` module split and adapter boundary.
2. Discard the assumption that a gloss must contain its own subject.
3. Introduce an entry-level model for Wordbook rows.
4. Add real corpus tests from `word-list-defs.tsv`.
5. Build gloss rules for fragments before expanding sentence coverage further.
6. Rework emission so repeated relators become one `predicate_list` with an
   `object_list` when possible.

## Recommended Next Milestone

The next milestone should not be another general refactor.

It should be a narrow, test-driven slice for real Wordbook entries.

Suggested scope:

### Input model

Create an internal model roughly like:

```text
WordbookEntry(word, wordbook_pos, gloss, example)
```

### First supported gloss profiles

Add failing tests for real examples such as:

- `able -> having the power to do something`
- `accept -> to agree to receive`
- `activist -> one who seeks change through action`
- `accident -> an unplanned event`

### Translation strategy

Translate from:

`word + gloss fragment`

not from:

`gloss fragment treated as a standalone sentence`

### Output strategy

Emit one-line TAGL PUT statements only.

When multiple objects share the same relator, emit one `predicate_list`
containing an `object_list`.

## Practical Recommendation

If one branch must be chosen now:

- choose `codex-fresh`

If the next work starts immediately after branch selection:

- carry over the structural-parser lessons from `claude-refactor`
- but redesign the parser around Wordbook entry translation rather than
  subject-first sentence parsing

## Final Recommendation

Adopt `codex-fresh` as the architectural base.

Do not merge either branch without immediately following it with:

- real VOA corpus tests
- entry-level translation models
- grammar-grounded TAGL emission fixes
- glossary-fragment parsing rules
