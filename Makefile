.PHONY: install test run init-db clean

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests

run:
	ADMIN_PASSWORD=change-me $(PYTHON) -m lead_ingest.server

init-db:
	$(PYTHON) scripts/init_db.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info
