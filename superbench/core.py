from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "benchmarks"
REQUIRED_ROLES = ("correctness", "evidence", "adversarial")
CORRECTNESS_STATES = {"met", "partial", "missed", "contradicted"}
EVIDENCE_STATES = {"valid", "invalid", "missing", "not_required"}
CHALLENGE_STATES = {"reproduced", "not_reproduced", "speculative"}


class BenchError(ValueError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchError(f"Не вдалося прочитати JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BenchError(f"{path}: очікується JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(line)


@dataclass(frozen=True)
class Incident:
    root: Path
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def prompt_path(self) -> Path:
        return self.root / str(self.data.get("prompt", "prompt.md"))

    @property
    def fixture_path(self) -> Path:
        return self.root / str(self.data.get("fixture", "fixture"))

    @property
    def oracle_path(self) -> Path:
        return self.root / str(self.data.get("oracle", "oracle.json"))


def incidents(base: Path = BENCHMARKS) -> list[Incident]:
    found: list[Incident] = []
    if not base.exists():
        return found
    for manifest in sorted(base.glob("SB-*/incident.json")):
        found.append(Incident(manifest.parent, read_json(manifest)))
    return found


def get_incident(identifier: str, base: Path = BENCHMARKS) -> Incident:
    normalized = identifier.upper()
    for incident in incidents(base):
        if incident.id.upper() == normalized or incident.root.name.upper() == normalized:
            return incident
    raise BenchError(f"Невідомий інцидент: {identifier}")


def validate_incident(incident: Incident) -> list[str]:
    errors: list[str] = []
    data = incident.data
    required = ("id", "title", "summary", "difficulty", "status", "tags")
    for key in required:
        if key not in data:
            errors.append(f"{incident.root.name}: відсутнє поле {key}")
    if not re.fullmatch(r"SB-\d{3}", str(data.get("id", ""))):
        errors.append(f"{incident.root.name}: id має формат SB-NNN")
    if not incident.prompt_path.is_file():
        errors.append(f"{incident.id}: prompt не знайдено")
    if not incident.fixture_path.is_dir():
        errors.append(f"{incident.id}: fixture не знайдено")
    if not incident.oracle_path.is_file():
        errors.append(f"{incident.id}: oracle не знайдено")
        return errors
    try:
        oracle = read_json(incident.oracle_path)
    except BenchError as exc:
        errors.append(str(exc))
        return errors
    criteria = oracle.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        errors.append(f"{incident.id}: oracle.criteria має бути непорожнім масивом")
    else:
        ids: set[str] = set()
        for item in criteria:
            if not isinstance(item, dict):
                errors.append(f"{incident.id}: criterion має бути object")
                continue
            cid = str(item.get("id", ""))
            if not cid or cid in ids:
                errors.append(f"{incident.id}: criterion id порожній або дублюється")
            ids.add(cid)
            if not item.get("patterns") or int(item.get("weight", 0)) <= 0:
                errors.append(f"{incident.id}/{cid}: потрібні patterns і weight > 0")
    threshold = oracle.get("pass_threshold")
    if not isinstance(threshold, int) or not 0 <= threshold <= 100:
        errors.append(f"{incident.id}: pass_threshold має бути 0..100")
    return errors


def validate_all(base: Path = BENCHMARKS) -> list[str]:
    found = incidents(base)
    errors = [] if found else ["Каталог benchmarks порожній"]
    seen: set[str] = set()
    for incident in found:
        if incident.id in seen:
            errors.append(f"Дубль id: {incident.id}")
        seen.add(incident.id)
        errors.extend(validate_incident(incident))
    return errors


def prepare_bundle(incident: Incident, output: Path, force: bool = False) -> Path:
    if output.exists():
        if not force:
            raise BenchError(f"Каталог уже існує: {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    shutil.copytree(incident.fixture_path, output / "fixture")
    shutil.copy2(incident.prompt_path, output / "PROMPT.md")
    bundle = {
        "schema_version": 1,
        "incident_id": incident.id,
        "title": incident.data["title"],
        "fixture_root": "fixture",
        "prompt": "PROMPT.md",
        "oracle_included": False,
    }
    write_json(output / "bundle.json", bundle)
    return output


def _matches(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def score_response(incident: Incident, response: str) -> dict[str, Any]:
    oracle = read_json(incident.oracle_path)
    positive_total = sum(int(item["weight"]) for item in oracle["criteria"])
    earned = 0
    criteria_results = []
    for item in oracle["criteria"]:
        matched = _matches(response, item["patterns"])
        weight = int(item["weight"])
        if matched:
            earned += weight
        criteria_results.append(
            {"id": item["id"], "matched": matched, "weight": weight}
        )
    penalties = []
    penalty_total = 0
    for item in oracle.get("anti_patterns", []):
        matched = _matches(response, item["patterns"])
        penalty = int(item.get("penalty", 0)) if matched else 0
        penalty_total += penalty
        penalties.append({"id": item["id"], "matched": matched, "penalty": penalty})
    raw_percent = round((earned / positive_total) * 100) if positive_total else 0
    score = max(0, raw_percent - penalty_total)
    threshold = int(oracle["pass_threshold"])
    return {
        "schema_version": 1,
        "incident_id": incident.id,
        "score": score,
        "pass_threshold": threshold,
        "heuristic_verdict": "pass" if score >= threshold else "fail",
        "criteria": criteria_results,
        "anti_patterns": penalties,
        "note": "Евристичний score не замінює незалежну agent-panel перевірку.",
    }


def response_id(incident_id: str, model: str, response: str) -> str:
    digest = hashlib.sha256(response.encode("utf-8")).hexdigest()[:10]
    safe_model = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-") or "model"
    return f"{incident_id.lower()}-{safe_model}-{digest}"


def create_run(
    incident: Incident,
    model: str,
    response: str,
    output_root: Path,
    *,
    provider: str = "unknown",
    attempt: int = 1,
    latency_ms: int | None = None,
) -> Path:
    rid = response_id(incident.id, model, response)
    run = output_root / rid
    if run.exists():
        raise BenchError(f"Відповідь уже зареєстрована: {rid}")
    run.mkdir(parents=True)
    (run / "response.md").write_text(response.rstrip() + "\n", encoding="utf-8")
    record = {
        "schema_version": 1,
        "response_id": rid,
        "incident_id": incident.id,
        "model": model,
        "provider": provider,
        "attempt": attempt,
        "latency_ms": latency_ms,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "response_sha256": hashlib.sha256(response.encode("utf-8")).hexdigest(),
        "heuristic": score_response(incident, response),
        "panel_status": "pending",
    }
    write_json(run / "response.json", record)
    append_jsonl(
        output_root / "results.jsonl",
        {
            "event": "attempt_finished",
            "response_id": rid,
            "incident_id": incident.id,
            "model": model,
            "provider": provider,
            "attempt": attempt,
            "verdict": "pending_review",
            "latency_ms": latency_ms,
            "date": record["created_at"],
        },
    )
    return run


def validate_review(review: dict[str, Any], response_id_value: str) -> list[str]:
    errors: list[str] = []
    if review.get("schema_version") != 1:
        errors.append("schema_version має дорівнювати 1")
    if review.get("response_id") != response_id_value:
        errors.append("response_id не відповідає відповіді")
    if review.get("agent_role") not in REQUIRED_ROLES:
        errors.append(f"agent_role має бути одним із {', '.join(REQUIRED_ROLES)}")
    confidence = review.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence має бути числом 0..1")
    if not str(review.get("agent_name", "")).strip():
        errors.append("agent_name обов'язковий")
    role = review.get("agent_role")
    if role == "correctness":
        rows = review.get("criteria")
        if not isinstance(rows, list) or not rows:
            errors.append("correctness-review потребує criteria[]")
        else:
            for row in rows:
                if row.get("status") not in CORRECTNESS_STATES:
                    errors.append("correctness status має бути met|partial|missed|contradicted")
                if not row.get("criterion_id"):
                    errors.append("criterion_id обов'язковий")
    elif role == "evidence":
        rows = review.get("criteria")
        if not isinstance(rows, list) or not rows:
            errors.append("evidence-review потребує criteria[]")
        else:
            for row in rows:
                if row.get("status") not in EVIDENCE_STATES:
                    errors.append("evidence status має бути valid|invalid|missing|not_required")
                if not row.get("criterion_id"):
                    errors.append("criterion_id обов'язковий")
    elif role == "adversarial":
        rows = review.get("challenges")
        if not isinstance(rows, list):
            errors.append("adversarial-review потребує challenges[]")
        else:
            for row in rows:
                if row.get("status") not in CHALLENGE_STATES:
                    errors.append("challenge status має бути reproduced|not_reproduced|speculative")
                if not row.get("criterion_id"):
                    errors.append("criterion_id обов'язковий")
    return errors


def add_review(run: Path, review_path: Path) -> Path:
    response = read_json(run / "response.json")
    review = read_json(review_path)
    errors = validate_review(review, response["response_id"])
    if errors:
        raise BenchError("; ".join(errors))
    reviews_dir = run / "reviews"
    reviews_dir.mkdir(exist_ok=True)
    existing = [read_json(path) for path in reviews_dir.glob("*.json")]
    if any(item["agent_role"] == review["agent_role"] for item in existing):
        raise BenchError(f"Роль уже заповнена: {review['agent_role']}")
    if any(item["agent_name"] == review["agent_name"] for item in existing):
        raise BenchError("Кожну відповідь мають перевіряти різні агенти")
    destination = reviews_dir / f"{review['agent_role']}.json"
    write_json(destination, review)
    return destination


def adjudicate(run: Path) -> dict[str, Any]:
    response = read_json(run / "response.json")
    reviews_dir = run / "reviews"
    reviews = [read_json(path) for path in sorted(reviews_dir.glob("*.json"))] if reviews_dir.exists() else []
    by_role = {item.get("agent_role"): item for item in reviews}
    missing = [role for role in REQUIRED_ROLES if role not in by_role]
    trace: list[dict[str, Any]] = []
    score = None
    hard_fail = False
    if missing:
        verdict = "pending"
        reason = "Потрібні три різні schema-valid agent-review"
    else:
        incident = get_incident(response["incident_id"])
        oracle = read_json(incident.oracle_path)
        correctness = {
            row["criterion_id"]: row for row in by_role["correctness"]["criteria"]
        }
        evidence = {row["criterion_id"]: row for row in by_role["evidence"]["criteria"]}
        reproduced = {
            row["criterion_id"]
            for row in by_role["adversarial"]["challenges"]
            if row["status"] == "reproduced"
        }
        total = sum(int(item["weight"]) for item in oracle["criteria"])
        earned = 0.0
        for criterion in oracle["criteria"]:
            cid = criterion["id"]
            state = correctness.get(cid, {}).get("status", "missed")
            factor = {"met": 1.0, "partial": 0.5, "missed": 0.0, "contradicted": 0.0}[state]
            evidence_state = evidence.get(cid, {}).get("status", "missing")
            adjustment = []
            if criterion.get("requires_evidence") and evidence_state != "valid":
                factor = 0.0
                adjustment.append(f"evidence={evidence_state}")
            if cid in reproduced:
                factor = 0.0
                adjustment.append("reproduced counterexample")
            if criterion.get("core") and (state == "contradicted" or cid in reproduced):
                hard_fail = True
                adjustment.append("core hard-fail")
            points = int(criterion["weight"]) * factor
            earned += points
            trace.append(
                {
                    "criterion_id": cid,
                    "correctness": state,
                    "evidence": evidence_state,
                    "points": points,
                    "max_points": int(criterion["weight"]),
                    "adjustments": adjustment,
                }
            )
        score = round((earned / total) * 100) if total else 0
        core_met = all(
            correctness.get(item["id"], {}).get("status") == "met"
            for item in oracle["criteria"]
            if item.get("core")
        )
        if hard_fail or score < 50:
            verdict = "rejected"
        elif score >= 80 and core_met:
            verdict = "confirmed"
        else:
            verdict = "partial"
        reason = f"deterministic reducer: score={score}; core_met={core_met}; hard_fail={hard_fail}"
    result = {
        "schema_version": 1,
        "response_id": response["response_id"],
        "incident_id": response["incident_id"],
        "model": response["model"],
        "verdict": verdict,
        "score": score,
        "hard_fail": hard_fail,
        "reason": reason,
        "missing_roles": missing,
        "agent_names": [item.get("agent_name") for item in reviews],
        "reducer_trace": trace,
        "adjudicated_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(run / "adjudication.json", result)
    response["panel_status"] = verdict
    write_json(run / "response.json", response)
    append_jsonl(
        run.parent / "results.jsonl",
        {
            "event": "adjudication_finished",
            "response_id": response["response_id"],
            "incident_id": response["incident_id"],
            "model": response["model"],
            "attempt": response.get("attempt", 1),
            "verdict": verdict,
            "score": score,
            "date": result["adjudicated_at"],
        },
    )
    return result


def collect_runs(results_root: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not results_root.exists():
        return runs
    for response_path in results_root.glob("*/response.json"):
        record = read_json(response_path)
        adjudication = response_path.parent / "adjudication.json"
        if adjudication.exists():
            record["adjudication"] = read_json(adjudication)
        runs.append(record)
    return sorted(runs, key=lambda item: str(item.get("created_at", "")), reverse=True)
