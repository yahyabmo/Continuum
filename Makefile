PYTHON := .venv/bin/python

.PHONY: setup check

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --quiet -e ".[dev]"

check:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m pytest
