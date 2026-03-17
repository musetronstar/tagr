# `tagr` Design Sketch: Recursive spaCy Dependency Walker for TAGL

This document proposes a production-minded design for translating spaCy parses into TAGL by walking the **dependency tree** recursively and synthesizing **NP-like** and **VP-like** semantic units.

Repository context: `tagr` currently translates natural language text into TAGL statements and aims for structural translation, even when semantic validation is incomplete.

---

## 1. Problem Summary

The current temptation is to process spaCy output as a **flat sequence of POS tags**. That is usually the wrong abstraction for TAGL.

Given a sentence such as:

> The themes for the Hearings will be based on the comprehensive report of the Secretary-General, contained in document A/59/2005, and the clusters defined therein.

The useful structure is not the token list itself, but the **headed dependency graph**:

- `based` is the main predicate
- `themes` is its passive subject
- `report` is the object of `on`
- `contained` modifies `report`
- `defined` is conjoined to the main predicate
- `clusters` is the subject of `defined`
- `therein` likely points back to `document A/59/2005`

For TAGL purposes, this is much closer to:

- build **NP-like entities** from noun heads and their modifiers
- build **VP-like relations** from verb heads and governed particles/prepositions
- recurse through subordinate and coordinated clauses

That gives a better fit than matching linear POS patterns.

---

## 2. Key Design Principle

Do **not** treat spaCy as “a list of tokens with POS tags.”

Treat spaCy as:

- a dependency tree rooted at one or more clause heads
- with token metadata used only to support tree walking

In practice, the important spaCy features are:

- `token.dep_`
- `token.head`
- `token.children`
- `token.subtree`
- `doc.noun_chunks` (supporting heuristic, not primary truth)

The translator should therefore be organized around **recursive tree walking**, not regex-like matching on tag sequences.

---

## 3. Translation Goal

The translator does **not** need to preserve all English syntax.

It needs to reduce English into a compact semantic form such as:

```tagl
>> hearings:themes based_on Secretary_General:comprehensive_report
contained_in document_A_59_2005
defined_therein document_A_59_2005:clusters;
```

This means the translator should normalize toward:

- **entity expressions** from noun phrases
- **relation expressions** from verb phrases / verbal predicates
- **chains of related clauses** when appropriate

---

## 4. High-Level Architecture

Recommended module decomposition:

```text
spacy -> clause extraction -> NP builder (for subject or objects) / relation builder -> TAGL emitter
```

Suggested internal components:

- `parse_doc(doc) -> list[ClauseNode]`
- `extract_root_clauses(doc) -> list[Token]`
- `taglize_clause(root, ctx) -> list[TaglStmt | TaglChain]`
- `taglize_np(head, ctx) -> TaglEntity`
- `taglize_relation(head, ctx) -> TaglRelation`
- `taglize_modifier_clause(head, anchor, ctx) -> list[...]`
- `resolve_reference(token, ctx) -> TaglEntity | None`
- `emit_tagl(ast) -> str`

### Why an intermediate representation

Do not emit TAGL directly while walking spaCy tokens.

Instead, build an intermediate semantic structure first.

Example dataclasses:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TaglEntity:
    head: str
    qualifiers: list[str] = field(default_factory=list)
    owner: Optional['TaglEntity'] = None
    source_span: tuple[int, int] | None = None

@dataclass
class TaglRelation:
    head: str
    particle: Optional[str] = None
    adverb: Optional[str] = None
    source_span: tuple[int, int] | None = None

@dataclass
class TaglClause:
    subject: TaglEntity
    relation: TaglRelation
    objects: list[TaglEntity | str] = field(default_factory=list)
    chained: list['TaglClause'] = field(default_factory=list)
    source_root_i: int | None = None
```
```

This gives you a place to:

- normalize names
- drop determiners
- fold compounds
- resolve pronoun-like adverbs such as `therein`
- emit different TAGL forms later without rewriting parsing logic

---

## 5. Core Translation Strategy

### 5.1 Clause-first

For each sentence:

1. find the main root predicate(s)
2. extract core arguments
3. build normalized subject/object entities
4. recurse into attached clauses (`acl`, `relcl`, `conj`, etc.)
5. emit one TAGL chain or several related TAGL statements

### 5.2 Head-driven NP building

For a noun head token, build the TAGL entity from the **head noun plus selected dependents**.

Typical dependents to inspect:

- `compound`
- `amod`
- `poss`
- `prep` with objects such as `of`, `for`, `in`, `on`
- appositional material where useful
- named-entity-like continuations (`Secretary-General`, `A/59/2005`)

Examples:

- `themes` + `for Hearings` -> `hearings:themes`
- `report` + `comprehensive` + `of Secretary-General` -> `Secretary_General:comprehensive_report`
- `clusters` + `defined therein` -> maybe `document_A_59_2005:clusters`

### 5.3 Head-driven relation building

For a verb or verbal predicate head, build the TAGL relation from:

- main verb lemma or normalized surface
- selected particles or governed prepositions
- selected adverbials when semantically essential
- ignore support auxiliaries unless TAGL needs tense/modality

Examples:

- `will be based on` -> `based_on`
- `contained in` -> `contained_in`
- `defined therein` -> `defined_therein`

---

## 6. Dependency Types That Matter Most

For the first implementation, focus on these dependencies:

### Clause skeleton

- `ROOT`
- `nsubj`
- `nsubjpass`
- `dobj` / `obj`
- `attr`
- `acomp`
- `prep`
- `pobj`
- `agent`
- `aux`
- `auxpass`
- `conj`
- `cc`

### NP structure

- `compound`
- `amod`
- `det` (usually ignored)
- `poss`
- `prep`
- `pobj`
- `appos`
- `nummod`

### Attached clause structure

- `acl`
- `relcl`
- `advcl`
- `xcomp`
- `ccomp`

### Reference / context clues

- `advmod`
- pronouns and deictic adverbs such as `therein`, `thereof`, `thereby`

---

## 7. Recommended Processing Pipeline

## Stage 1: Sentence segmentation

Use spaCy sentence boundaries and process each sentence independently.

```python
def process_doc(doc):
    outputs = []
    for sent in doc.sents:
        outputs.extend(process_sentence(sent))
    return outputs
```

## Stage 2: Root and coordinated predicates

Find the main root verb, then collect related coordinated predicates.

```python
def sentence_roots(sent):
    roots = [t for t in sent if t.dep_ == "ROOT"]
    return roots
```

From each root, also inspect `conj` children where the conjunct is verbal or clause-like.

## Stage 3: Build primary clause

For a root predicate:

- subject: `nsubj`, `nsubjpass`, sometimes inherited subject from prior clause
- object/complement: `obj`, `attr`, `prep`+`pobj`, passive complements
- relation: main verb + important preposition/adverb

## Stage 4: Build attached subordinate clauses

Inspect children of the main verb or important NP heads:

- `acl` on nouns -> creates secondary clause about that noun phrase
- `relcl` -> relative clause attached to noun
- `conj` on verbs -> coordinated clause

## Stage 5: Contextual reference resolution

Maintain a lightweight discourse context to support terms like `therein`.

Suggested context state:

```python
@dataclass
class Context:
    last_document: TaglEntity | None = None
    last_np: TaglEntity | None = None
    recent_entities: list[TaglEntity] = field(default_factory=list)
```

When parsing `contained in document A/59/2005`, set `last_document`.

Then `defined therein` can map `therein` to that entity.

## Stage 6: Emit TAGL

Emit either:

- a single chained TAGL statement
- or multiple statements joined by indentation / continuation logic

The emitter should be deterministic and separate from parsing.

---

## 8. Heuristics for NP TAGLization

These heuristics align well with the examples discussed.

### 8.1 Determiners

Usually drop:

- `the`
- `a`
- `an`

### 8.2 Adjectives

Retain semantically meaningful adjectives as prefixes:

- `comprehensive report` -> `comprehensive_report`

### 8.3 Compounds / proper names

Merge compounds into a single normalized tag:

- `Secretary-General` -> `Secretary_General`
- `document A/59/2005` -> `document_A_59_2005`

### 8.4 Prepositional ownership / qualification

Selected prepositions can invert into TAGL ownership-style notation.

Examples:

- `themes for the Hearings` -> `hearings:themes`
- `report of the Secretary-General` -> `Secretary_General:report`

This should be **heuristic and configurable**, because English prepositions are not semantically uniform.

Suggested initial rule table:

```python
NP_LINK_PREPS = {
    "of": "owner",
    "for": "context_owner",
}
```

Then apply custom rendering:

- owner-like relations -> `owner:head`

### 8.5 Numbers

When useful:

- `4 legs` -> `legs = 4`

This may already fit your existing quantifier handling.

---

## 9. Heuristics for VP / Relation TAGLization

### 9.1 Auxiliaries

Ignore default support auxiliaries in most cases:

- `will`
- `be`
- `is`
- `was`

unless the modal itself matters semantically:

- `can bark` -> `can bark`
- `must comply` -> `must comply`

### 9.2 Verb + preposition fusion

Common pattern:

- `based` + `on` -> `based_on`
- `contained` + `in` -> `contained_in`

Recommended rule:

- if the verb has a `prep` child that is semantically part of the relation, fuse it
- prefer the closest semantically dominant PP

### 9.3 Adverb fusion

For special adverbs such as `therein`, `thereof`, `thereby`, optionally fuse:

- `defined therein` -> `defined_therein`

This is especially useful when TAGL wants a compact relator string.

---

## 10. Worked Example: Main Target Sentence

Input:

> The themes for the Hearings will be based on the comprehensive report of the Secretary-General, contained in document A/59/2005, and the clusters defined therein.

spaCy tokens indicate approximately:

- `based` is `ROOT`
- `themes` is `nsubjpass` of `based`
- `on` is a `prep` attached to `based`
- `report` is `pobj` of `on`
- `contained` is `acl` attached to `report`
- `in` + `document A/59/2005` attaches to `contained`
- `defined` is `conj` of `based`
- `clusters` is `nsubj` of `defined`
- `therein` is `advmod` of `defined`

### Step A: Main clause

Subject NP:

- head: `themes`
- PP: `for Hearings`
- normalize: `hearings:themes`

Relation:

- head verb: `based`
- prep: `on`
- normalize: `based_on`

Object NP:

- head: `report`
- modifier: `comprehensive`
- PP: `of Secretary-General`
- normalize: `Secretary_General:comprehensive_report`

Main clause:

```tagl
hearings:themes based_on Secretary_General:comprehensive_report
```

### Step B: Attached modifier clause on `report`

Modifier clause:

- verbal head: `contained`
- prep: `in`
- object: `document A/59/2005`
- normalize object: `document_A_59_2005`

Secondary clause:

```tagl
contained_in document_A_59_2005
```

This may be attached to the report entity or emitted as a continuation in the TAGL chain.

### Step C: Coordinated clause

Conjunct predicate:

- head: `defined`
- adverb: `therein`
- subject: `clusters`
- resolve `therein` -> `document_A_59_2005`

Result NP:

- `document_A_59_2005:clusters`

Secondary clause:

```tagl
defined_therein document_A_59_2005:clusters
```

### Combined TAGL target

```tagl
>> hearings:themes based_on Secretary_General:comprehensive_report
contained_in document_A_59_2005
defined_therein document_A_59_2005:clusters;
```

---

## 11. Ambiguity Strategy

The sentence:

> Bart watched a squirrel with binoculars.

is structurally ambiguous.

Two readings:

1. Bart used binoculars to watch.
2. The squirrel had binoculars.

The translator should not pretend otherwise.

Recommended design:

- preserve the best parse selected by spaCy
- optionally expose an ambiguity flag in debug mode
- allow TAGL to remain somewhat underspecified if that aligns with project goals

Possible output:

```tagl
>> Bart watched squirrel with binoculars;
```

If future strictness is desired, the IR can carry attachment confidence metadata.

---

## 12. Proposed Implementation Skeleton

```python
class TagrTranslator:
    def __init__(self, nlp, config=None):
        self.nlp = nlp
        self.config = config or TagrConfig()

    def translate(self, text: str) -> list[str]:
        doc = self.nlp(text)
        stmts = []
        for sent in doc.sents:
            ctx = Context()
            clauses = self.process_sentence(sent, ctx)
            stmts.extend(self.emit_clause(c) for c in clauses)
        return stmts

    def process_sentence(self, sent, ctx):
        clauses = []
        roots = [t for t in sent if t.dep_ == "ROOT"]
        for root in roots:
            clauses.extend(self.taglize_clause(root, ctx))
        return clauses

    def taglize_clause(self, root, ctx):
        subject_tok = self.find_subject(root, ctx)
        if subject_tok is None:
            return []

        subject = self.taglize_np(subject_tok, ctx)
        relation = self.taglize_relation(root, ctx)
        objects = self.find_clause_objects(root, ctx)

        clause = TaglClause(
            subject=subject,
            relation=relation,
            objects=[self.taglize_np(obj, ctx) for obj in objects],
            source_root_i=root.i,
        )

        self.update_context_from_clause(clause, ctx)

        extras = []
        for child in root.children:
            if child.dep_ == "conj" and self.is_clause_head(child):
                extras.extend(self.taglize_conj_clause(child, clause, ctx))

        for obj in objects:
            extras.extend(self.taglize_np_attached_clauses(obj, ctx))

        return [clause, *extras]
```

This is intentionally incomplete, but it gives Codex a strong architectural target.

---

## 13. Suggested Detailed Helper Contracts

### `find_subject(root, ctx)`

Responsibilities:

- prefer `nsubj`
- else `nsubjpass`
- else inherited subject for conjunctions
- else return `None`

### `find_clause_objects(root, ctx)`

Responsibilities:

- collect `obj`, `attr`, relevant `prep`+`pobj`
- preserve stable ordering
- choose which prepositional complement is the primary object of the relation

### `taglize_np(head, ctx)`

Responsibilities:

- identify noun/proper-noun head
- collect compounds and adjectival modifiers
- consume selected `prep` complements recursively
- normalize to TAGL-safe text

### `taglize_relation(head, ctx)`

Responsibilities:

- choose base verb form
- optionally preserve modal when semantically meaningful
- fuse governing preposition or special adverb when configured

### `taglize_np_attached_clauses(head, ctx)`

Responsibilities:

- inspect `acl`, `relcl`, maybe `appos`
- build secondary TAGL clauses anchored to the NP

### `resolve_reference(token, ctx)`

Responsibilities:

- map `therein`, `thereof`, `thereby`, etc. to recent context entities when safe
- return unresolved marker when confidence is too low

---

## 14. Configuration Recommendations

Make these behaviors configurable, not hardcoded.

```python
@dataclass
class TagrConfig:
    drop_determiners: bool = True
    keep_adjectives: bool = True
    fuse_verb_prepositions: bool = True
    fuse_special_adverbs: bool = True
    resolve_therein: bool = True
    prefer_owner_colon_for_of: bool = True
    prefer_owner_colon_for_for: bool = True
    debug_dependency_walk: bool = False
```

You will almost certainly want to tune these heuristics sentence-by-sentence while growing the test corpus.

---

## 15. Testing Strategy

The repository already includes tests and a prototype translator entrypoint. citeturn0view0

Recommended test organization:

### 15.1 Golden translation tests

Each test case should include:

- input sentence
- expected TAGL
- notes on ambiguity / assumptions

Example:

```yaml
- input: "Bart watched a squirrel with binoculars."
  expected: ">> Bart watched squirrel with binoculars;"
  notes: "attachment ambiguous; preserve compact TAGL chain"

- input: "The themes for the Hearings will be based on the comprehensive report of the Secretary-General, contained in document A/59/2005, and the clusters defined therein."
  expected: |
    >> hearings:themes based_on Secretary_General:comprehensive_report
    contained_in document_A_59_2005
    defined_therein document_A_59_2005:clusters;
  notes: "requires NP folding, acl handling, conj handling, and therein resolution"
```

### 15.2 Debug-structure tests

Add tests that validate intermediate structure, not just final strings.

Example assertions:

- root relation normalized as `based_on`
- subject NP normalized as `hearings:themes`
- object NP normalized as `Secretary_General:comprehensive_report`
- `contained` recognized as attached clause on `report`

These tests will make refactoring much safer.

### 15.3 Regression tests for failure cases

Add cases for:

- prepositional attachment ambiguity
- passive voice
- nested `of` phrases
- coordinated predicates
- coordinated noun phrases
- document identifiers and punctuation-heavy names

---

## 16. Incremental Delivery Plan for Codex

Recommended implementation order:

### Milestone 1: Tree-walk foundation

- add IR dataclasses
- add sentence/root/clause traversal
- implement subject/object extraction for simple clauses
- keep existing simple translations working

### Milestone 2: NP builder

- compounds
- adjectives
- determiners dropped
- `of` folding
- `for` folding
- proper-name normalization

### Milestone 3: Relation builder

- verb normalization
- modal preservation where useful
- verb+preposition fusion
- special adverb fusion (`therein`)

### Milestone 4: Attached and coordinated clauses

- `acl`
- `relcl`
- `conj`
- inherited subject/object where justified

### Milestone 5: Reference resolution

- lightweight discourse context
- map `therein` and similar forms to recent entities

### Milestone 6: Debug tooling

- `--debug-deps`
- `--debug-ir`
- `--debug-taglize-np`

These will be invaluable while tuning heuristics.

---

## 17. Practical Advice for the Current Repository

For `tagr`, I would recommend the following near-term shift in mindset:

### Current mindset

- translate token stream into TAGL using local token patterns

### Better mindset

- translate **headed dependency subtrees** into semantic units, then emit TAGL

That fits both the existing project goal and the type of structures you are trying to express.

The flat token printout is useful for debugging, but it should not drive the architecture.

---

## 18. Final Recommendation

Yes: for TAGL, it is better to **recursively walk spaCy dependency trees** and synthesize **NP-like** and **VP-like** semantic units than to rely primarily on flat POS-tag sequences.

The most important design decisions are:

1. use a semantic intermediate representation
2. build noun expressions from noun heads plus selected dependents
3. build relation expressions from verb heads plus selected prepositions/adverbs
4. recurse into attached and coordinated clauses
5. keep context for lightweight reference resolution such as `therein`
6. separate parsing from emission so the translator remains testable and evolvable

That approach gives Codex a clear implementation path while keeping the heuristics explicit and adjustable.

---

## 19. Suggested Codex Prompt Stub

You may want to paste something like this into Codex:

```text
Refactor tagr so it no longer relies primarily on flat POS-sequence matching.
Use spaCy dependency structure as the primary parse representation.

Implement:
- dataclasses for TaglEntity, TaglRelation, TaglClause, Context, TagrConfig
- sentence processing by ROOT clause heads
- recursive taglize_np(head, ctx)
- recursive taglize_relation(head, ctx)
- support for compound/amod/det/prep/pobj/acl/conj/advmod
- fusion of verb+preposition such as based_on, contained_in
- special handling for therein using a lightweight context object
- unit tests for the two example sentences in this design doc

Keep emission separate from parsing.
Add debug output modes for dependency walk and intermediate representation.
Preserve existing simple behavior where possible.
```

