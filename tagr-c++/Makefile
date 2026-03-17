PRG_DIR = $(HOME)/projects/
TAGD_DIR = $(PRG_DIR)/tagd/tagd
TAGL_DIR = $(PRG_DIR)/tagd/tagl
TAGDB_DIR = $(PRG_DIR)/tagd/tagdb
TAGSH_DIR = $(PRG_DIR)/tagd/tagsh

INC = -I$(TAGD_DIR)/include -I$(TAGL_DIR)/include -I$(TAGDB_DIR)/include -I$(TAGDB_DIR)/sqlite/include -I$(TAGSH_DIR)/include
LFLAGS = -L$(TAGSH_DIR)/lib -ltagsh -L$(TAGDB_DIR)/lib -ltagdb-sqlite -L$(TAGL_DIR)/lib -ltagl -L$(TAGD_DIR)/lib -ltagd -lsqlite3 -lreadline -levent

all:
	g++ -O3 -std=c++23 -W -o tagr tagr.cc $(INC) $(LFLAGS)

clean:
	rm tagr
