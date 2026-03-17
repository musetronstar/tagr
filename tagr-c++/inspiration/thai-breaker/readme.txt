Thai Syllable Breaker
=====================

The purpose of this project is to implement a Finite State Machine (FSM)
that identifies syllables in Thai text. The input file of Thai script
will be transformed into a stream containing spaces that identify breaks
between syllables.

The workflow is broken into three steps:

1) Pipe the UTF-8 input file into our syllable breaking program using `cat`.

2) Insert spaces as syllable breaks into the Thai script output stream.

This program was implement using C++11.  C++11 can represent Unicode literals
in the source files, but does not have encoding/decoding capabilities as
part of the standard distribution.  Some of SQLite's UTF-8 processing code
was used for this purpose. Its in the Public Domain, so in can be shared freely
for any purpose.  All UTF-8 code is located in the file utf8.h.

The FSM accept states and transitions are defined in lambda functions
which use closures to simplify logic and readability. Plain old lookup
functions for each character category are used rather than a hash map.  It
turned out to be easier to implement and just as expressive (and probably
faster).

A lookup table of codepoints, to accept states, to transitions that eliminates
all the "if codepoint is in category" comparisons would probably be the fastest
approach, but would tricky to implement because codepoints can belong to
multiple categories, otherwise, this probably would have been the approach used.

Initially, a string byte buffer was used to store processing syllables and
spaces, but was cumbersome.  Instead, it first scans the input, storing the
offset of each start syllable position in a vector, then loops though the
offsets to print the syllables as substrings of the input delimited by spaces.
It appears to be faster, uses less memory, simpler, and more extensible for
other uses (other than printing spaces).  The input line of UTF-8 is held in a
single string and nowhere else - with no string copying, insertion, etc.

3) Finally, wrap the output stream into an HTML template.

The output stream of the syllable breaker is wrapped into an HTML template
using `awk`.  Each line of output is appended with a <br> tag. The single tick
("'") characters in the provided XHTML template example was causing problems
with awk, so I chose to use a simple HTML5 template.  I hope this is acceptable.

