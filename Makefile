.PHONY: install test test-e2e test-all run init-db clean

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests

test-e2e:
	$(PYTHON) -m unittest discover -s tests/e2e -t tests/e2e -v

# Runs the existing suite (tests/) and the isolated E2E suite (tests/e2e/).
test-all: test test-e2e

run:
	ADMIN_PASSWORD=change-me $(PYTHON) -m lead_ingest.server

init-db:
	$(PYTHON) scripts/init_db.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info
