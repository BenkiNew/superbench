"""Experimental evidence contract. Data validation only; no model code execution."""
import re

BINDINGS=('case_sha256','response_sha256','proposal_sha256','recipe_sha256','environment_sha256')


def evaluate_proof(expected, proof):
    # Reject malformed/mismatched metadata; return unverified for absent/weak proof.
    if not isinstance(expected, dict):
        raise ValueError('Expected metadata must be an object')
    canonical = {}
    for key in BINDINGS:
        value = expected.get(key)
        if not isinstance(value, str) or not re.fullmatch('[0-9a-fA-F]{64}', value):
            raise ValueError('Invalid expected binding: '+key)
        canonical[key] = value.lower()
    unknown={'status':'unverified','official_score':None,'requires_manual_review':True}
    if proof is None:
        return {**unknown,'reason':'no_proof'}
    if not isinstance(proof, dict):
        raise ValueError('Proof must be an object or None')
    for key in BINDINGS:
        value=proof.get(key)
        if not isinstance(value,str) or not re.fullmatch('[0-9a-fA-F]{64}',value):
            raise ValueError('Invalid binding: '+key)
        if value.lower()!=canonical[key]:
            raise ValueError('Evidence belongs to a different '+key)
    scope=proof.get('scope')
    if not isinstance(scope,str) or not scope.strip():
        raise ValueError('Explicit proof scope required')
    if proof.get('exact_proposal') is not True:
        return {**unknown,'reason':'reconstruction_not_exact_proposal','scope':scope}
    if proof.get('baseline_pass') is not False:
        return {**unknown,'reason':'no_reproduced_failing_baseline','scope':scope}
    passed=proof.get('repair_pass')
    count=proof.get('checks')
    if type(passed) is not bool or type(count) is not int or count<1:
        return {**unknown,'reason':'missing_or_invalid_check_result','scope':scope}
    return {**unknown,'status':'supported' if passed else 'refuted',
            'reason':'scoped_checks_pass' if passed else 'scoped_checks_fail','scope':scope,'checks':count}


def record_proof(expected, proof, output):
    """Write a new scoped assessment; never replace an existing revision."""
    import hashlib
    import json
    from pathlib import Path
    from . import __version__

    assessment = evaluate_proof(expected, proof)
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    report = {'schema_version': 1, 'harness_version': __version__,
              'experimental': True, 'official_verdict': False,
              'expected_sha256': hashlib.sha256(canonical(expected)).hexdigest(),
              'proof_sha256': hashlib.sha256(canonical(proof)).hexdigest(),
              'assessment': assessment}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
    return report
