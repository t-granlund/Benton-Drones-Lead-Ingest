.PHONY: install test test-e2e test-e2e-browser test-e2e-live test-all run init-db clean

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests

# HTTP-level E2E suite (55 tests).
# Default pattern test_*.py naturally excludes browser_test_*.py.
test-e2e:
	$(PYTHON) -m unittest discover -s tests/e2e -t tests/e2e -v

# Browser-automation E2E tests against the local ephemeral server.
# Requires Playwright + Chromium (`make install` first).
test-e2e-browser:
	$(PYTHON) -m unittest discover -s tests/e2e -t tests/e2e -v -p 'browser_test_*.py'

# Browser-automation E2E tests against the live Render instance.
# Set E2E_ADMIN_PASSWORD in your environment; public-only tests run without it.
test-e2e-live:
ifndef E2E_BASE_URL
	$(error E2E_BASE_URL is not set. Example: E2E_BASE_URL=https://benton-drones-lead-ingest.onrender.com)
endif
	$(PYTHON) -m unittest discover -s tests/e2e -t tests/e2e -v -p 'browser_test_*.py'

# Runs the existing suite (tests/) and the isolated E2E suite (tests/e2e/).
test-all: test test-e2e

run:
	ADMIN_PASSWORD=change-me $(PYTHON) -m lead_ingest.server

init-db:
	$(PYTHON) scripts/init_db.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ *.egg-info
