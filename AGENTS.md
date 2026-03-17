# STDIN libevent stream to File Magic Short Circuit Identification

## Goals and Inspiration

Read `~/projects/tagr-c++/*.md`
Inspect `~/projects/tagr-c++/inspiration/*`

Use `tagr-c++` as a goal and **inspiration** assests as a guide of style and coding mindset.

## Task

Make a C prototype the reads from STDIN like `cat`

### Functions 

#### Function magic_stream
function magic_stream(evbuffer)
* reads bytes in from a libevent buffer
* uses libmagic to identify streams of bytes - return (short circuit) when identity known
* returns content-type

function main:
    opens FH STDIN libevent buffer
    calls magic_stream(evbuffer)
    prints PATH: content-type; charset

on error, print reason to STDERR and exit with error code

## Example:

```bash
$ file -i /tmp/main.js
/tmp/main.js: application/javascript; charset=utf-8
```

I'd like to capture (return from function) at least as much information as that above command.

But we need to be upstream from it. We control the FH that is passed in.

## Usage

prototype for now...

```bash
./tagd-filemagic /tmp/main.js
/tmp/main.js: application/javascript; charset=utf-8
```


