from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (
    BENCHMARKS,
    ROOT,
    BenchError,
    add_review,
    adjudicate,
    create_run,
    get_incident,
    incidents,
    prepare_bundle,
    score_response,
    validate_all,
)
from .render import render_site
from .proofs import record_proof
from .experiments import prepare_control_pair, record_control_review, control_summary
from .core import read_json


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="superbench")
    sub = root.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="показати каталог інцидентів")
    listing.add_argument("--json", action="store_true")
    sub.add_parser("validate", help="перевірити структуру benchmark")
    prepare = sub.add_parser("prepare", help="створити oracle-free bundle для агента")
    prepare.add_argument("incident")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--force", action="store_true")
    score = sub.add_parser("score", help="евристично оцінити Markdown-відповідь")
    score.add_argument("incident")
    score.add_argument("response", type=Path)
    record = sub.add_parser("record", help="зареєструвати відповідь для agent-panel")
    record.add_argument("incident")
    record.add_argument("response", type=Path)
    record.add_argument("--model", required=True)
    record.add_argument("--provider", default="unknown")
    record.add_argument("--attempt", type=int, default=1, choices=range(1, 4))
    record.add_argument("--latency-ms", type=int)
    record.add_argument("--results", type=Path, default=ROOT / "results")
    review = sub.add_parser("review", help="додати незалежний agent-review")
    review.add_argument("run", type=Path)
    review.add_argument("review_json", type=Path)
    decide = sub.add_parser("adjudicate", help="порахувати consensus трьох агентів")
    decide.add_argument("run", type=Path)
    render = sub.add_parser("render", help="побудувати статичний портал")
    render.add_argument("--output", type=Path, default=ROOT / "site")
    render.add_argument("--results", type=Path, default=ROOT / "results")
    pair = sub.add_parser("control-prepare", help="prepare an evaluator-only key and blinded bundles")
    pair.add_argument("incident")
    pair.add_argument("--correct", type=Path, required=True)
    pair.add_argument("--incorrect", type=Path, required=True)
    pair.add_argument("--defect-id", required=True)
    pair.add_argument("--output", type=Path, required=True)
    control = sub.add_parser("control-record", help="append a locally adjudicated panel report")
    control.add_argument("pair", type=Path)
    control.add_argument("sample")
    control.add_argument("report", type=Path)
    summary = sub.add_parser("control-summary", help="summarize latest control reports without ranking")
    summary.add_argument("pair", type=Path)
    proof = sub.add_parser("proof-record", help="record experimental scoped repair evidence")
    proof.add_argument("--expected", type=Path, required=True)
    proof.add_argument("--proof", type=Path, required=True, help="JSON object or null for absent evidence")
    proof.add_argument("--output", type=Path, required=True, help="new immutable assessment path")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "list":
            items = [item.data for item in incidents(BENCHMARKS)]
            if args.json:
                print(json.dumps(items, ensure_ascii=False, indent=2))
            else:
                for item in items:
                    print(f"{item['id']}  {item['difficulty']:<8} {item['title']}")
            return 0
        if args.command == "validate":
            errors = validate_all()
            if errors:
                print("\n".join(f"ERROR: {item}" for item in errors), file=sys.stderr)
                return 1
            print(f"OK: {len(incidents())} інцидентів валідні")
            return 0
        if args.command == "prepare":
            print(prepare_bundle(get_incident(args.incident), args.output, args.force))
            return 0
        if args.command == "score":
            response = args.response.read_text(encoding="utf-8")
            print(json.dumps(score_response(get_incident(args.incident), response), ensure_ascii=False, indent=2))
            return 0
        if args.command == "record":
            response = args.response.read_text(encoding="utf-8")
            print(create_run(
                get_incident(args.incident), args.model, response, args.results,
                provider=args.provider, attempt=args.attempt, latency_ms=args.latency_ms,
            ))
            return 0
        if args.command == "review":
            print(add_review(args.run, args.review_json))
            return 0
        if args.command == "adjudicate":
            print(json.dumps(adjudicate(args.run), ensure_ascii=False, indent=2))
            return 0
        if args.command == "control-prepare":
            print(prepare_control_pair(get_incident(args.incident), args.correct, args.incorrect,
                                       args.defect_id, args.output))
            return 0
        if args.command == "control-record":
            print(json.dumps(record_control_review(args.pair, args.sample, read_json(args.report)),
                             ensure_ascii=False, indent=2))
            return 0
        if args.command == "control-summary":
            print(json.dumps(control_summary(args.pair), ensure_ascii=False, indent=2))
            return 0
        if args.command == "proof-record":
            try:
                report = record_proof(read_json(args.expected),
                                      json.loads(args.proof.read_text(encoding="utf-8")), args.output)
            except (ValueError, TypeError) as exc:
                raise BenchError(str(exc)) from exc
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        if args.command == "render":
            print(render_site(args.output, args.results))
            return 0
    except (BenchError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
