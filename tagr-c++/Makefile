TAGR_BIN=bin/tagr

.PHONY: src data tests clean

all: src data

src:
	make -C src all

data:
	bin/simple-english-rev-freq.sh > data/simple-english-rev-freq.txt

tests: src
	make -C tests tests

clean:
	rm -f $(TAGR_BIN)
	make -C tests clean
