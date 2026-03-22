SHELL := /bin/bash

.PHONY: all tagr clean

PRG_DIR = $(HOME)/projects/tagd
TAGD_DIR = $(PRG_DIR)/tagd
TAGL_DIR = $(PRG_DIR)/tagl
TAGDB_DIR = $(PRG_DIR)/tagdb
TAGSH_DIR = $(PRG_DIR)/tagsh
TAGR_BIN=../bin/tagr

INC = -I$(TAGD_DIR)/include -I$(TAGL_DIR)/include -I$(TAGDB_DIR)/include -I$(TAGDB_DIR)/sqlite/include -I$(TAGSH_DIR)/include
LFLAGS = -L$(TAGSH_DIR)/lib -ltagsh -L$(TAGDB_DIR)/lib -ltagdb-sqlite -L$(TAGL_DIR)/lib -ltagl -L$(TAGD_DIR)/lib -ltagd -lsqlite3 -lreadline -levent

all: tagr

tagr:
	g++ -O3 -std=c++23 -W -o $(TAGR_BIN) tagr.cc $(INC) $(LFLAGS)

clean:
	rm -f $(TAGR_BIN)
