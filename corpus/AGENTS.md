### Corpus-Driven Development

All translation behavior is defined and verified through YAML corpus files under `tagr/corpus/`.

- Every supported structural pattern must have at least one failing-then-passing corpus case before code is written.
- General patterns live in `corpus/general/` (POS/dep shapes only, no domain knowledge).
- Domain-specific corpora (VOA, future Wiktionary, etc.) live in `corpus/<domain>/` (e.g. `corpus/voa/`).
- Each domain corpus has a `test.py` that loads all `.yaml` files in its directory and yields cases.
- The generic runner `test_corpus.py` discovers all `corpus/*/test.py` modules and runs their `cases()` generator.
- Run `pytest test_corpus.py` to execute the entire corpus suite.
- Goal: 1000+ green cases before v1.0; grow until it hurts, then split sub-directories.

### Naming & Placement Rules

- `test_corpus.py` — top-level, domain-agnostic discoverer & runner
- `corpus/<module>/test.py` — module test loader; loads all `*.yaml` in its directory
- `corpus/<module>/<source>.yaml` — corpus data files
- No domain terminology in `test_corpus.py` or any shared runner logic
- Discovery is purely filesystem-based: glob `corpus/*/test.py` → call `.cases()`

### Workflow for New Patterns / Domains

1. Add new yaml file → `corpus/<module>/<something>.yaml`
2. Create `corpus/<module>/test.py` if the module is new (loads all `*.yaml` in dir)
3. Write minimal failing cases (input + hints + expected / error)
4. Run `pytest test_corpus.py` → see failures
5. Implement minimal rule in tagr → make cases green
6. Repeat until coverage feels painful → refactor/split

### Acceptance Criteria for Rules

- Rule is pure function (input: tokens/hints → output: Relation or list[Relation])
- Rule has ≥ 3 dedicated corpus cases (happy + edge + failure)
- No literal word checks unless structural (e.g. no "one who" string match — use POS/dep pattern)
- Output always valid single-line TAGL (object_list compaction preferred)

Commit often. Keep corpus green. Grow corpus faster than code.

That’s the minimal, self-consistent addition. Paste it and move on.
