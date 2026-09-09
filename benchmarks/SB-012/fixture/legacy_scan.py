# coverage_api/legacy_scan.py
# Unchanged since 2026-08-25, not touched by the fix commit — included so
# it can be ruled out as the source of the bug.

from pathlib import Path

from .merge_sources import LocalFile

_REPORT_SUFFIXES = {".xlsx", ".pdf", ".csv"}


def scan_legacy_drop_folder(date_dir: Path) -> list[LocalFile]:
    if not date_dir.is_dir():
        return []
    result = []
    for path in sorted(date_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _REPORT_SUFFIXES:
            continue
        team = path.relative_to(date_dir).parts[0]
        result.append(LocalFile(
            rel_path=str(path.relative_to(date_dir)),
            filename=path.name,
            team=team,
        ))
    return result
