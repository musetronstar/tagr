CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2
CPPFLAGS ?=
LDFLAGS ?=
LDLIBS ?= -levent -lmagic

SRC = ../src/
BIN = ./test-tagd-filemagic

.PHONY: all test clean

all: $(BIN)

tests: $(BIN)
	$(BIN)

$(BIN): test-tagd-filemagic.c $(SRC)/tagd-filemagic.c $(SRC)/tagd-filemagic.h
	$(CC) $(CPPFLAGS) -I$(SRC) $(CFLAGS) -DTAGD_FILEMAGIC_NO_MAIN $(LDFLAGS) \
		-o $@ test-tagd-filemagic.c $(SRC)/tagd-filemagic.c $(LDLIBS)

clean:
	rm -f $(BIN)
