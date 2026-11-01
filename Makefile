PYTHON := .venv/bin/python

.PHONY: setup check take crossfade demo

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --quiet -e ".[dev]"

check:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m pytest

take:
	$(PYTHON) -m continuum.prep $(FILE)

crossfade:
	$(PYTHON) -m continuum.bench $(CLIPS)

demo:
	$(PYTHON) -m continuum.bench --demo
