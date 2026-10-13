"""Local control experiments; their events never become leaderboard verdicts."""
from __future__ import annotations

import hashlib
import json
import math
import random
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .core import BenchError, Incident, append_jsonl, prepare_bundle, read_json, write_json


def file_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def prepare_control_pair(incident: Incident, correct: Path, incorrect: Path,
                         defect_id: str, output: Path) -> Path:
    if output.exists():
        raise BenchError('Control output already exists; create a new revision')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', defect_id):
        raise BenchError('defect_id must be a stable lowercase identifier')
    answers = [(correct.read_text(encoding='utf-8'), 'correct'),
               (incorrect.read_text(encoding='utf-8'), 'incorrect')]
    if answers[0][0] == answers[1][0]:
        raise BenchError('Control answers must differ')
    random.SystemRandom().shuffle(answers)
    staging = output.with_name(output.name + '.building-' + uuid.uuid4().hex)
    try:
        samples = {}
        for name, (answer, expected) in zip(('sample-a', 'sample-b'), answers):
            bundle = staging / 'samples' / name
            prepare_bundle(incident, bundle)
            (bundle / 'ANSWER.md').write_text(answer, encoding='utf-8')
            samples[name] = {'expected': expected, 'hashes': file_hashes(bundle)}
        shutil.copytree(incident.root, staging / 'benchmark')
        benchmark_hashes = file_hashes(staging / 'benchmark')
        try:
            source_commit = subprocess.run(
                ['git', '-C', str(incident.root), 'rev-parse', 'HEAD'], capture_output=True,
                text=True, check=True, timeout=5,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            source_commit = None
        write_json(staging / 'evaluation.json', {
            'schema_version': 1, 'harness_version': __version__,
            'incident_id': incident.id, 'case_version': incident.data.get('version', 'unversioned'),
            'defect_id': defect_id, 'samples': samples,
            'benchmark_hashes': benchmark_hashes, 'source_commit': source_commit,
            'case_fingerprint': hashlib.sha256(json.dumps(benchmark_hashes, sort_keys=True).encode()).hexdigest(),
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output


def record_control_review(pair: Path, sample: str, report: dict[str, Any]) -> dict[str, Any]:
    key = read_json(pair / 'evaluation.json')
    if sample not in key['samples']:
        raise BenchError('Unknown control sample')
    try:
        changed = any(hashlib.sha256((pair / 'samples' / sample / name).read_bytes()).hexdigest() != sha
                      for name, sha in key['samples'][sample]['hashes'].items())
    except OSError as exc:
        raise BenchError('Pinned control input is missing') from exc
    if changed:
        raise BenchError('Control inputs changed; create a new pair revision')
    if report.get('schema_version') != 1:
        raise BenchError('Report schema_version must be 1')
    voices = report.get('voices')
    if not isinstance(voices, list) or not voices:
        raise BenchError('Provide every requested voice, including failures')
    ids, usable = set(), []
    for voice in voices:
        if not isinstance(voice, dict):
            raise BenchError('Each voice must be an object')
        identifier = voice.get('id')
        if not isinstance(identifier, str) or not identifier.strip() or identifier in ids:
            raise BenchError('Voice identifiers must be nonempty and distinct')
        ids.add(identifier)
        if voice.get('transport_status') not in ('completed', 'failed', 'unavailable'):
            raise BenchError('Invalid transport_status')
        review = voice.get('review')
        if review is None:
            continue
        if voice['transport_status'] != 'completed' or not isinstance(review, dict):
            raise BenchError('Failed transport cannot supply a usable review')
        if review.get('verdict') not in ('accepted', 'rejected', 'unclear'):
            raise BenchError('Review verdict must be accepted, rejected or unclear')
        findings = review.get('findings')
        if not isinstance(findings, list):
            raise BenchError('Usable review requires a findings array')
        for finding in findings:
            if not isinstance(finding, dict) or finding.get('decision') not in ('confirmed', 'unsupported'):
                raise BenchError('Findings require local adjudication decisions')
            if not isinstance(finding.get('defect_id'), str) or not finding['defect_id'].strip():
                raise BenchError('Finding requires defect_id')
            if not isinstance(finding.get('evidence'), str) or not finding['evidence'].strip():
                raise BenchError('Finding requires local evidence')
        if review['verdict'] == 'rejected' and not any(f['decision'] == 'confirmed' for f in findings):
            raise BenchError('Rejected review requires a locally confirmed finding')
        usable.append(review)
    cost = report.get('cost_usd')
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float))
                             or not math.isfinite(cost) or cost < 0):
        raise BenchError('Cost must be a finite nonnegative number or null')
    detected = any(f['defect_id'] == key['defect_id'] and f['decision'] == 'confirmed'
                   for review in usable for f in review['findings']) if usable else None
    rejected = any(review['verdict'] == 'rejected' for review in usable) if usable else None
    if usable and all(review['verdict'] == 'unclear' for review in usable):
        rejected = None
    expected = key['samples'][sample]['expected']
    event = {
        'schema_version': 1, 'event': 'control_review_recorded', 'event_id': uuid.uuid4().hex,
        'harness_version': __version__, 'incident_id': key['incident_id'],
        'case_version': key['case_version'], 'sample': sample, 'expected': expected,
        'source_commit': key['source_commit'], 'case_fingerprint': key['case_fingerprint'],
        'defect_id': key['defect_id'], 'input_hashes': key['samples'][sample]['hashes'],
        'requested_voices': len(voices), 'usable_voices': len(usable),
        'panel_status': 'complete' if len(usable) == len(voices) else ('partial' if usable else 'unavailable'),
        'target_detected': detected if expected == 'incorrect' else None,
        'control_rejected': rejected if expected == 'correct' else None,
        'cost_usd': cost, 'date': datetime.now(timezone.utc).isoformat(),
        'report': report, 'official_verdict': False,
    }
    # Each import is immutable; the append-only ledger preserves every reassessment.
    write_json(pair / 'reviews' / (event['event_id'] + '.json'), event)
    append_jsonl(pair / 'events.jsonl', event)
    return event


def control_summary(pair: Path) -> dict[str, Any]:
    key = read_json(pair / 'evaluation.json')
    latest = {}
    ledger = pair / 'events.jsonl'
    if ledger.exists():
        for line in ledger.read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            latest[event['sample']] = event
    return {'schema_version': 1, 'incident_id': key['incident_id'], 'case_version': key['case_version'],
            'harness_version': key['harness_version'],
            'samples_reviewed': sum(e['usable_voices'] > 0 for e in latest.values()),
            'samples_expected': len(key['samples']), 'latest': latest, 'official_verdict': False}
