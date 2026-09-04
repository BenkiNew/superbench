"""sync_findings_to_db.py <verified.json> — upserts the findings database
from a completed pipeline run. Only invoked as the last step of a full run
that reached pass 2 (verified.json exists). Best-effort: any DB error is a
silent no-op so it never fails the scan pipeline itself.

Nothing in this repository re-runs this sync outside of a full pipeline
pass, and nothing re-renders the dashboard from the database — the two
stores are updated independently, on different triggers.
"""
import json
import sys

RESOLVE_SQL = """
UPDATE findings SET status = 'resolved', resolved_at = now()
WHERE source = 'codescan' AND status = 'open' AND identity_key <> ALL(%(still_open)s);
"""


def main(verified_path):
    doc = json.load(open(verified_path))
    still_open = {f"{f['rule_id']}|{f['repo']}|{f['file']}" for f in doc["findings"]}
    # ... upsert current findings, then RESOLVE_SQL closes anything no
    # longer present in this run's findings list.


if __name__ == "__main__":
    main(sys.argv[1])
