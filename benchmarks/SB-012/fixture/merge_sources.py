# coverage_api/merge_sources.py
# Pure function, unit-tested, unchanged in the fix commit below — not the
# source of the bug. Included so the function itself can be inspected and
# ruled out.

from dataclasses import dataclass


@dataclass(frozen=True)
class LocalFile:
    rel_path: str
    filename: str
    team: str


def merge_sources(date, submissions, local_files, teams=None):
    """DB submissions are canonical; local_files fills in anything not
    yet ingested (e.g. a team still dropping files in the legacy folder
    instead of using the bot)."""
    teams = teams or {}
    seen_paths = {s["rel_path"] for s in submissions}

    files = list(submissions)
    for local in local_files:
        if local.rel_path in seen_paths:
            continue
        files.append({
            "date": date,
            "team": local.team,
            "filename": local.filename,
            "rel_path": local.rel_path,
            "source": "legacy_folder",
        })
    return files
