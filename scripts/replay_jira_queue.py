"""CLI entry point for the JIRA queue replay worker.

Usage::

    python -m scripts.replay_jira_queue --once            # single sweep
    python -m scripts.replay_jira_queue --interval 60     # daemon loop

Requires the JIRA_* env vars; without them a sweep just reports skipped
items. All state lives in the app database.
"""
from __future__ import annotations

import sys

from lead_ingest.jira_replay import main

if __name__ == "__main__":
    sys.exit(main())
