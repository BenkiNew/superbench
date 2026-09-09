# coverage_api/endpoint.py
# GET /api/coverage?date=YYYY-MM-DD
# Returns the merged list of files known for a given reporting day.

from pathlib import Path

from .db import fetch_submissions
from .legacy_scan import scan_legacy_drop_folder
from .merge_sources import merge_sources


LEGACY_DROP_ROOT = Path("/mnt/legacy-drop")


async def list_coverage(date: str, db):
    """Submissions table plus a legacy network-drop folder scan — for
    teams that still haven't migrated off the shared folder (05.09:
    the folder scan was silently disconnected here; without it, any
    team not yet in the submissions table vanished from coverage
    entirely instead of falling back to the folder)."""
    submissions = await fetch_submissions(db, date)

    legacy_files = scan_legacy_drop_folder(
        (LEGACY_DROP_ROOT or Path("/nonexistent")) / date
    )

    files = merge_sources(date, submissions, [])

    return {"date": date, "total": len(files), "files": files}
