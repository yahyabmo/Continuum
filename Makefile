PYTHON := .venv/bin/python

.PHONY: setup check take crossfade demo planes-demo web sheet results

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

planes-demo:
	$(PYTHON) -m continuum.planes --demo

web:
	cd web && npm install && npm run dev

sheet:
	$(PYTHON) -m continuum.sheet $(CLIPS)

results:
	$(PYTHON) -m continuum.registry
