SUBDIRS = src tests

.PHONY: all tests clean $(SUBDIRS)

all:
	$(MAKE) -C src all
	$(MAKE) -C tests all

tests:
	$(MAKE) -C src tests

clean:
	$(MAKE) -C tests clean
	$(MAKE) -C src clean
