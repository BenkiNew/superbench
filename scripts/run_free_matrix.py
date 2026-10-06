#!/usr/bin/env python3
"""Матриця incident × free-модель: запуск candidate + локальний heuristic score.

Лише локальний інструмент оператора. Результати: .superbench/runs/<incident>/<model>.md,
.meta.json і зведення .superbench/runs/summary.md. Ключ не друкується (див. run_openai_candidate.py).
  python3 scripts/run_free_matrix.py --incidents SB-001 SB-002 --workers 3
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("runner", ROOT / "scripts/run_openai_candidate.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def one(incident: str, model: str, retries: int = 2) -> dict:
    slug = model.replace("/", "__").replace(":", "_")
    out = ROOT / ".superbench/runs" / incident / f"{slug}.md"
    result = {"incident": incident, "model": model, "score": None, "verdict": None, "error": None, "cost": None, "latency_s": None}
    for attempt in range(retries + 1):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/run_openai_candidate.py"), incident, "--model", model, "--out", str(out)],
                              capture_output=True, text=True, cwd=ROOT)
        if proc.returncode == 0:
            meta = json.loads(out.with_suffix(".meta.json").read_text(encoding="utf-8"))
            result.update(cost=meta.get("gateway_cost"), latency_s=meta.get("latency_s"), error=None)
            score = subprocess.run([sys.executable, "-m", "superbench", "score", incident, str(out)], capture_output=True, text=True, cwd=ROOT)
            try:
                data = json.loads(score.stdout)
                result.update(score=data["score"], verdict=data["heuristic_verdict"])
            except (json.JSONDecodeError, KeyError):
                result["error"] = "score failed: " + score.stderr[-120:]
            return result
        result["error"] = (proc.stderr or proc.stdout)[-160:].strip().replace("\n", " ")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--incidents", nargs="+", required=True)
    parser.add_argument("--models", nargs="*", default=sorted(runner.FREE_MODELS))
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    jobs = [(i, m) for i in args.incidents for m in args.models]
    print(f"{len(jobs)} запусків, workers={args.workers}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for res in pool.map(lambda job: one(*job), jobs):
            results.append(res)
            print(json.dumps(res, ensure_ascii=False), flush=True)
    runs = ROOT / ".superbench/runs"
    (runs / "summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["| модель | " + " | ".join(args.incidents) + " | середнє | pass |", "|---|" + "---|" * (len(args.incidents) + 2)]
    for model in args.models:
        cells, scores = [], []
        for inc in args.incidents:
            r = next(x for x in results if x["incident"] == inc and x["model"] == model)
            cells.append("ERR" if r["score"] is None else str(r["score"]))
            if r["score"] is not None:
                scores.append(r["score"])
        passed = sum(1 for inc in args.incidents for r in [next(x for x in results if x["incident"] == inc and x["model"] == model)] if r["verdict"] == "pass")
        lines.append(f"| {model} | " + " | ".join(cells) + f" | {round(sum(scores) / len(scores)) if scores else '-'} | {passed}/{len(args.incidents)} |")
    (runs / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
