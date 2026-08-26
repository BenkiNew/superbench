#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from superbench.core import ROOT, append_jsonl, create_run, get_incident, prepare_bundle


INFRA_MARKERS = (
    "429",
    "rate limit",
    "weekly limit",
    "usage limit",
    "out of usage credits",
    "provider returned error",
    "timed out",
    "timeout",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one candidate agent with bounded retries")
    parser.add_argument("incident")
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=3, choices=(1, 2, 3))
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--command", default="cn")
    return parser.parse_args()


def ledger(results: Path, **fields: object) -> None:
    append_jsonl(
        results / "results.jsonl",
        {"date": datetime.now(timezone.utc).isoformat(), **fields},
    )


def main() -> int:
    args = parse_args()
    incident = get_incident(args.incident)
    workspace = ROOT / ".superbench" / "workspace" / "current"
    prepare_bundle(incident, workspace, force=True)
    prompt = (workspace / "PROMPT.md").read_text(encoding="utf-8")
    command = [args.command, "--config", str(args.config), "--readonly", "-p", prompt]
    environment = os.environ.copy()
    for attempt in range(1, args.attempts + 1):
        started = time.monotonic()
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                timeout=args.timeout,
                check=False,
            )
            latency_ms = round((time.monotonic() - started) * 1000)
            combined = (result.stdout + "\n" + result.stderr).strip()
            infra_error = result.returncode != 0 and any(
                marker in combined.lower() for marker in INFRA_MARKERS
            )
            if result.returncode == 0 and result.stdout.strip():
                run = create_run(
                    incident,
                    args.model,
                    result.stdout,
                    args.results,
                    provider=args.provider,
                    attempt=attempt,
                    latency_ms=latency_ms,
                )
                print(run)
                return 0
            ledger(
                args.results,
                event="attempt_finished",
                incident_id=incident.id,
                model=args.model,
                provider=args.provider,
                attempt=attempt,
                verdict="infra_error" if infra_error else "invalid_submission",
                latency_ms=latency_ms,
                exit_code=result.returncode,
            )
            if not infra_error:
                return 2
        except subprocess.TimeoutExpired:
            latency_ms = round((time.monotonic() - started) * 1000)
            ledger(
                args.results,
                event="attempt_finished",
                incident_id=incident.id,
                model=args.model,
                provider=args.provider,
                attempt=attempt,
                verdict="infra_error",
                latency_ms=latency_ms,
                reason="timeout",
            )
        if attempt < args.attempts:
            time.sleep(2 ** (attempt - 1))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
