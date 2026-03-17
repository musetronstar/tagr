#!/usr/bin/env python3

import argparse
import sys

import spacy

nlp = spacy.load("en_core_web_sm")


def print_token_table(text):
    """
    Print token information for quick NLP inspection.

    Columns:
    i     token index
    text  token text
    pos   coarse POS (NLP POS)
    tag   fine POS
    dep   dependency relation
    head  syntactic head token
    """
    doc = nlp(text)

    print(f"{'i':>2} {'text':<12} {'pos':<6} {'tag':<6} {'dep':<10} head")
    print("-" * 50)

    for t in doc:
        print(
            f"{t.i:>2} {t.text:<12} {t.pos_:<6} {t.tag_:<6} {t.dep_:<10} {t.head.text}"
        )


def print_coarse_pos_list(text):
    """Print coarse spaCy NLP POS tags as a single space-delimited line."""
    doc = nlp(text)
    print(" ".join(t.pos_ for t in doc))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Inspect spaCy tokens or print a coarse NLP POS sequence."
    )
    parser.add_argument(
        "-p",
        "--pos",
        action="store_true",
        help="Print coarse POS sequence instead of the token table.",
    )
    parser.add_argument("text", nargs="+", help="Input text to analyze.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    text = " ".join(args.text)

    if args.pos:
        print_coarse_pos_list(text)
    else:
        print_token_table(text)


if __name__ == "__main__":
    main()
