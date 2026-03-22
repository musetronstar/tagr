PRG_DIR = ..
TAGR_BIN = ../bin/tagr
TAGD_PRG_DIR = ../../../tagd
TAGD_DIR = $(TAGD_PRG_DIR)/tagd
TAGL_DIR = $(TAGD_PRG_DIR)/tagl
TAGDB_DIR = $(TAGD_PRG_DIR)/tagdb

.PHONY: all tests debug build tagr_tests expect_tests test_rev_freqs clean

CXXTEST = cxxtestgen --error-printer
CXXFLAGS ?= -std=c++23 -Wall -Wextra -Wno-unused-result -O3
INC = -I../src -I$(TAGD_DIR)/include -I$(TAGL_DIR)/include -I$(TAGDB_DIR)/include -I$(TAGDB_DIR)/sqlite/include
LFLAGS = -L$(TAGDB_DIR)/lib -ltagdb-sqlite -L$(TAGL_DIR)/lib -ltagl -L$(TAGD_DIR)/lib -ltagd -lsqlite3 -levent
TESTER = ./tester
EXPECT = expect ./tester.exp

all: tests

tests: build expect_tests test_rev_freqs

debug: CXXFLAGS += -g -O0
debug: all

build: tagr_tests

tagr_tests: $(TAGR_BIN)
	$(CXXTEST) Tester.h -o tester.cpp
	g++ $(CXXFLAGS) -o tester tester.cpp $(INC) $(LFLAGS)
	$(TESTER)

expect_tests: $(TAGR_BIN)
	$(EXPECT)

test_rev_freqs: $(TAGR_BIN)
	bash ./test-rev-freqs.sh

$(TAGR_BIN):
	make -C $(PRG_DIR)

clean:
	rm -f tester.cpp tester
