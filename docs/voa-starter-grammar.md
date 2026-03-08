# tagr — Starter Grammar Rules for VOA Wordbook Definitions

This document is a **working hypothesis for initial rule exploration**.
Actual rules will be confirmed through tests in the repository.

AGENTS.md supercedes this and contains the **development and design rules**.

This document describes a **small starter rule set (5 rules)** for translating
VOA Wordbook dictionary definitions into TAGL.

The goal is not full natural language understanding. The goal is **deterministic
structural extraction** of a relation shape that can be expressed as a TAGL
`PUT` statement.

# PUT Grammar:

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

General pipeline:

input text
↓
NLP analysis (tokens + NLP POS)
↓
pattern match
↓
(subject, relator, object)
↓
>> subject relator object;

These rules should be implemented as **small pure translation rules** and
verified through unit tests.

---

# Rule 1 — Adjective Phrase Definition

Example:

able    having the power to do something

Simplified normalized input:

able having power to do something

Typical NLP POS pattern:

ADJ VERB NOUN PART AUX PRON

Simplified structural pattern:

HEAD ADJ/VERB NOUN

Extraction:

subject = able
relator = having
object  = power
relator = to_do
object  = something

TAGL:

We TAGLize `to do` into `to_do`.

RULE: multi-token relators may be joined with "_" during TAGLization

>> able having power to_do something;

Rule: 

As a *structural translator*, we want to create a best fit to TAGL syntax.
We might not always have a subordinate relation given between the word and the gloss.
At this point we don't do semantic validation (though it would be a powerful option to have in the future).
Many of the put statements, though being structurally sound, might not have been defined yet with a subordinate relation. That's okay for now. We will develop strategies to resolve that later.
We should not inject relations that don't exist in the text except `_rel` as a *controlled structural fallback* when needed to produce structurally valid TAGL.
For now, let's create a structural translation that does not presuppose anything except `_rel` (for now) - rather we should try to faithfully represent only what is provided in the gloss.

---

# Rule 2 — “to VERB” Definition

Example:

accept  to agree to receive

Typical NLP POS pattern:

VERB PART VERB PART VERB

Simplified pattern:

HEAD to VERB

Extraction:

subject = accept
relator = to
object  = agree
relator = to
object  = receive

TAGL:

>> accept to agree, receive;

---

# Rule 3 — “someone …” Definition

Example:

actor   someone acting in a play or show

Typical NLP POS pattern:

NOUN PRON VERB ADP DET NOUN CCONJ VERB

Structural pattern:

HEAD someone VERB ...

Extraction:

subject = actor
relator = [NONE]
object  = someone
relator = acting
object  = play
object  = show

TAGL:

In this example here we fallback to `_rel` which is safer than _sub because subordinate relations define identity and position within the tagspace tree.
I don't see any way around the fallback until we build up robustness and intelligence of the system (later).

This is a legal TAGL statment having repeated relators without an `object_list`:

>> actor _rel someone
acting play
acting show;

Canonically, in tagspace dumps, we use more compact `object_list` and put a newline for each `relator`:

>> actor _rel someone
acting play, show;

But to make it line oriented and grep-able, the entire put statment should be one line:
RULE: repeated relators must be compacted into an `object_list`.

>> actor _rel someone acting play, show;

---

# Rule 4 — “one who …” Definition

Example:

activist    one who seeks change through action

Typical NLP POS pattern:

ADJ NOUN PRON VERB NOUN ADP NOUN

Pattern:

HEAD one who VERB ...

Extraction:

subject = activist
relator = _rel
object  = one
relator = seeks
object = change
relator = through
object = action

I would think that "one" might be too ambigous for Simple English, because its means a person, not a number. But nonetheless, we have to deal with it.

TAGL:

>> activist _rel one seeks change through action;

---

# Rule 5 — Simple Noun Synonym

Example:

accident    an unplanned event

Typical NLP POS pattern:

NOUN DET ADJ NOUN

Pattern:

HEAD DET ADJ NOUN

Extraction:

subject = accident
relator = _rel
object  = unplanned_event

TAGL:

Using reason and intelligent inference, we might define with a proper sub relations as below,
But we can't because is_a sub relation is inferred but not parsed directly from the text.

>> accident is_a unplanned_event;

In this stage of our structural translator,  we don't have reason or intelligent inference, so we have to use the safe relator and it will have to be fixed by an intelligent agent later.

>> accident _rel unplanned_event;

---

# Why These 5 Rules Are A Good Start

VOA Wordbook definitions are typically **short glosses** rather than full
sentences.

From a small sample, most definitions fall into a small number of structural patterns:

Pattern | Example | Coverage
noun synonym | an unplanned event | high
adjective phrase | having power | high
to‑verb definition | to agree to receive | medium
someone/one who | someone acting | medium
prepositional phrase | at a higher place | medium

However, we shouldn't rush to conclusions based on a small sample because we have 2723 definitions.

```bash
$ wc -l word-list-defs.tsv
2724 word-list-defs.tsv
```

We should aim to provide **high coverage** with as minimal a grammar as possible, but we will build it up over time using an iterative process, not by presupposing and jumping to conclusions.

---

# Important Implementation Guidance

Do **not hard‑code English lexical tokens** in translation rules.

Avoid patterns like:

if "someone" in text:

Instead rely on **NLP POS structure and dependency relations**.

Example pattern:

if pos == ["DET", "ADJ", "NOUN"]:

or dependency‑based checks from the NLP parser.

This keeps the translator aligned with the architectural principles in
`AGENTS.md`, and importantly, adhere to TAGL PUT grammar rules.

---

# Recommended Starter Tests

Example unit tests:

assert translate("accident an unplanned event") == ">> accident _rel unplanned_event;"

Notice that two relations having the same `relator` "to" are compacted into an `object_list`

assert translate("accept to agree to receive") == ">> accept to agree, receive;"

Here `_rel` is `relator`, but not a `sub_relator`. `actor` is related to `someone`, not subordinate to `someone`

assert translate("actor someone acting in a play or show") == ">> actor _rel someone acting play, show;"

Tests define the supported grammar behavior.

---

# Philosophy

`tagr` is **not an NLP understanding system**.

It is a:

NLP-assisted grammar-to-TAGL translator

The NLP layer provides linguistic structure.

The grammar rules define the language.
