"""render_dashboard.py — builds the public status page.

Deliberately does NOT read from the findings database. The dashboard is a
deterministic, file-based snapshot of the last full pipeline run that
actually completed — the database is a separate, continuously-updated
tracker used elsewhere, not the source for this page.
"""
import glob
import json


def latest_verified_run(state_dir="state/runs"):
    run_dirs = sorted(glob.glob(f"{state_dir}/*/"))
    for run_dir in reversed(run_dirs):
        try:
            with open(f"{run_dir}/verified.json") as f:
                return json.load(f)
        except FileNotFoundError:
            continue  # this run never finished pass 2; skip to the previous one
    return None


def render_confirmed_findings_section():
    doc = latest_verified_run()
    findings = doc["findings"] if doc else []
    return f"Confirmed findings from the last full scan ({len(findings)})", findings
