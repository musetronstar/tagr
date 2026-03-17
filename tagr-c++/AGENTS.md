# AGENTS.md

## Project

`tagr` reads unknown raw bytes (like `cat`) but outputs TAGL.

It tries its best (e.g. like a browser would) to parse input and make sense of it.

### INPUT: default <STDIN>
  default STDIN  - TODO may adde "read from file option" not to be confuse with `--file` option use to specify tagspace to validate agaist
* identifies content-type from patterns in files/streams to identify input (or uses "magic")
* tokenizes input according to content-type
* creates a quick-lookup trie of tokens
  + that can do get/put values like a key/value store does (e.g. RocksDB)
  + but the key will be internally represented as a trie
  + each tree node will have a pointer to data (can be nullptr)
  + the trie will benefit us in tokenization, classification and lookup
  + TODO (later): smemory-map trie tokens suitable for shared non-blocking I/O among multiple threads or processes

### OUTPUT: STDOUT
TODO:
1 TAGL shaped statements (not semantically validated [because tags unknown])
2 Or, with `-V`, `--validate` options followed by `--file tagspace.tagl` 
  + inherit from `tagsh` the way `httagd` does - share command line processing TAGL parser, etc)
    + Start by adding the TAGL parser driver `lookup_pos()` to this project
  + Outputs valid TAGL statements

### OUTPUT: STDERR
  See how the `../tagd/` project outputs TAGL errors.
  + output valid `tagd:error` TAGL statements
  + see the TCL `expect` tests to see the errors as TAGL that tagd outputs

### TEST: Output Types and Conditions
1. statements in the valid `<subject> <relator> <object>` **shape of TAGL** statments
2. [optional] if a `--validate` and `--file` option given, statements will use tagd to output valid TAGL
3. If 1 or optionally 2 above fail, output TAGL errors


## Usage

Partly TAGLized: Translated into TAGL-shapted statement, but validy unknown
```bash
cat 'tagr is a byte to TAGL parser' | tagr
>> tagr is_a byte_to_TAGL_parser ;
echo $?
0
```

Fully TAGLized: Translated into valid TAGL.
Example contains known (defined) tags.
```bash
$ cat "person of human" | tagr \
    --file ../tagd-simple-english/simple-english.tagl \
    --tagl "<< person" -n
>> person of human;
echo $?
0
```

TAGLized into TAGL shape, but non valid:
```
$ cat 'tagr is a byte to TAGL parser' | tagr \
    --file ../tagd-simple-english/simple-english.tagl \
    --tagl "<< tagr" -n
TS_NOT_FOUND _type_of _error
_caused_by _unknown_tag = tagr
echo $?
1
```
In the error above, the first token `tagr` would cause `pos_lookup()` to return `tagd_pos:TOK_UKNOWN` (or something like that, TODO verify)


## Inspiration

Follow the style, conventions and mindset of the authors. Write code as if the authors of these example wrote it themselves.

1. `inspiration/thai-breaker/`
   + beautiful modern c++ and expressive
   + decompose natural language features using well organized lambda functions organized like a parser grammar
   + TODO (later)
     * create NLP modules for different language targets
        + `src/nlp.h`
        + `src/nlp.cc`
        + `nlp/en/*`
        + `nlp/es/*`
        + `nlp/th/*`
        etc.
     * `src/nlp.h` general NLP related utility funcions - interface shared by all language specific modules
     * refactor and generalize `thai-breaker` into this structure
     * create a simple english modlue parser directory structure for NLP modules for different languages
2. `inspiration/meyers-c++11-word-count.cc` master at his craft - tutorial how to tokenize, word count and memory map in a modern c++ way
3. `../tagd/` the tagd semantic relational engine and TAGL language - follow specific terminology for types and grammar when speaking about tagd or TAGL


## Current State

The codebase is being refactored from a genomic sequence matcher (DNA bases
A/T/C/G, 4-slot trie nodes) to a generic byte trie (256-slot nodes) that
handles arbitrary input including UTF-8 sequences naturally — one byte at a
time, no special casing needed.

I also *tried* to hack together code to print an ngram frequency table from the trie, but its messy and broken.

## TODOs (from source)

1. Strip out the genomic ATCG code and language - this is now a byte parser
2. Add frequency counts of trie nodes

## Philosophy, Style & Workflow

### One small step at a time

Do not make sweeping changes. Each edit should do exactly one thing. If the
task is "replace the 4-slot genomic node with a 256-slot byte node", change
only that. Do not reformat surrounding code, do not rename things, do not
reorganize includes.

### Preserve the author's style

- Do not reformat lines that don't need changing
- Do not change whitespace, indentation, or brace style on untouched lines
- Do not alter comments — the author's comments and TODOs are design intent,
  not clutter
- Do not remove commented-out code blocks without being explicitly asked to

### Minimal diffs

Produce the smallest possible diff that achieves the goal. If a line doesn't
need to change to make the feature work, don't touch it. The author may review
changes via `git diff` and will notice unnecessary edits.

### Prefer patch-based review

When making non-trivial changes, prefer producing a diff the author can review
and edit before applying, rather than rewriting files directly.

### Build and test after every change

```bash
make
```

Make sure each task is complete and well tested before reporting.

Upon success, provide a concise and meaningful summary.
