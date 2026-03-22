# tagr

Reads raw bytes and outputs TAGL as well as serving as a tagspace repository development tool.

## Directories

* `bin/`: `tagr` build binary and utilities
* `data/`: data helpful for constructing tagspaces
* `inspiration/`:
  + `meyers-c++11-word-count.cc`: word segmentation; modern,safe mem-mapping
  + `thai-breaker/`: beautiful use of NLP pattern constituents as const exressions and lambdas; modern c++;  input stream positional marking, utf-8, style ...
* `src/`:  tagr source code
* `tests/`: unit and system tests, etc.


## Data

Build instructions for `data/` directory:

### Reverse Frequency Table of `{WORD}\t{tagd POS token}`

```bash
$ bin/simple-english-rev-freq.sh > data/simple-english-rev-freq.txt
```

### Each Word of Reverse Frequency Table of `{WORD}:\t{`?? $word;`query list`}`

```bash
$ bin/simple-english-rev-freq.sh \
    | awk '{print $2}' \
    | while read word
        do
            printf '%s:\t%s' "$word"
            tagsh -f ~/projects/tagd-simple-english/simple-english.tagl --tagl "?? \"$word\""  -n
        done \
    | tee data/simple-english-rev-freq-word-query.txt
```

