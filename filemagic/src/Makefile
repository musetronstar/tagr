CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2
LDFLAGS ?=
LDLIBS ?= -levent -lmagic

BIN = ../bin/tagd-filemagic

.PHONY: all test clean

all: $(BIN)

$(BIN): tagd-filemagic.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

tests:
	$(MAKE) -C ../tests tests

clean:
	rm -f $(BIN)
