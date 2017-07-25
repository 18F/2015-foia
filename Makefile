all: contacts

setup:
	$(MAKE) -C contacts $@

contacts:
	$(MAKE) -C contacts $@

test:
	$(MAKE) -C contacts $@

.PHONY: all contacts setup test
