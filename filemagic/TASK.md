# TASK.md

## Purpose

Build a small C prototype in this repository that identifies the type of a byte
stream as early as possible.

This is not just a wrapper around `file -i`. The goal is to sit upstream from
that behavior: we control the file handle, we read the bytes ourselves, and we
try to determine the stream identity from progressively accumulated input.

The project should be grounded in the ethos of `~/projects/tagr-c++` and its
`inspiration/` assets.

## Grounding in `tagr-c++`

The prototype should follow these ideas:

- Read unknown raw bytes like `cat`.
- Infer structure from the stream itself instead of assuming a file type up
  front.
- Classify incrementally and short-circuit once the identity is known.
- Keep logic small, explicit, and composable.
- Prefer clear data flow and direct error handling over clever abstractions.
- Make the smallest change set necessary for the prototype.
- Preserve room for future extension by returning structured identification
  results rather than only printing ad hoc text.

In practical terms, this means the prototype should feel like a stream parser
primitive, not a batch utility that only works after reading the whole file.

## Required Prototype

Create a prototype executable named `tagd-filemagic`.

It should:

- Read input from `STDIN` using a `libevent` buffer.
- Use `libmagic` to identify the incoming bytes.
- Return as soon as the content identity is known well enough.
- Capture at least the same identification fidelity as `file -i`, including:
  - MIME / content-type
  - charset, when available

## Core Functions

### `magic_stream(evbuffer)`

Responsibilities:

- Accept a `libevent` `evbuffer`.
- Read bytes from that buffer progressively.
- Feed the accumulated bytes into `libmagic`.
- Detect when the content type is known with sufficient confidence.
- Short-circuit at that point instead of waiting unnecessarily for full input.
- Return structured type information, at minimum enough to print:
  `content-type; charset`

This function should be designed as an upstream reusable primitive.

### `main`

Responsibilities:

- Open or attach `STDIN` to a `libevent` buffer.
- Call `magic_stream(evbuffer)`.
- Print output in the form:

```text
PATH: content-type; charset
```

- On error, print a clear reason to `STDERR`.
- Exit with a nonzero status on failure.

## Expected Behavior

Prototype usage is currently expected to look like:

```bash
./tagd-filemagic /tmp/main.js
/tmp/main.js: application/javascript; charset=utf-8
```

The immediate prototype may accept a path argument for display and input setup,
but the implementation should still be conceptually centered on streaming bytes
through `STDIN` / file-handle control rather than delegating the problem to an
external `file` command.

## Engineering Constraints

- Do not write unrelated code.
- Do not broaden scope beyond the prototype.
- Favor minimal, reviewable changes.
- Keep the result readable by humans and straightforward for an agent to
  implement.
- Treat this as an early stream-classification building block for larger parsing
  work later.
