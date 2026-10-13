# Control pairs and incomplete panels

[Українська](CONTROL_EXPERIMENTS.md) · **English**

Control experiments check whether reviewers detect an injected defect and
whether they reject a correct answer. They do not alter official three-role
adjudication or the coding-agent leaderboard.

```bash
python3 -m superbench control-prepare SB-004 \
  --correct correct.md --incorrect incorrect.md \
  --defect-id premature-resolution --output .superbench/control-004-v1
```

The evaluator defines and verifies the correct answer and target defect.
The CLI randomly assigns answers to neutral sample-a/sample-b labels.
Give a reviewer only one directory under `samples/`. Keep `evaluation.json`
and `benchmark/` private to the evaluator: they contain the expected outcomes,
version, hashes and an oracle snapshot. Use fresh reviewer sessions and control
shared context/memory; random labels alone do not prove blinding.

After an actual review and local finding adjudication, provide normalized JSON:

```json
{
  "schema_version": 1,
  "cost_usd": null,
  "voices": [
    {
      "id": "reviewer-1",
      "transport_status": "completed",
      "review": {
        "verdict": "rejected",
        "findings": [
          {
            "defect_id": "premature-resolution",
            "decision": "confirmed",
            "evidence": "latest_scan.json:3-5: incomplete; no relevant negative evidence"
          }
        ]
      }
    },
    {
      "id": "reviewer-2",
      "transport_status": "completed",
      "error": "Model unavailable; no substantive review"
    },
    {
      "id": "reviewer-3",
      "transport_status": "failed",
      "error": "Timeout"
    }
  ]
}
```

```bash
python3 -m superbench control-record .superbench/control-004-v1 sample-a report.json
python3 -m superbench control-summary .superbench/control-004-v1
```

Include every requested reviewer, including failures. Add `requested_voice_ids` with the complete requested roster. The CLI rejects
omitted, extra or duplicate voice IDs when this field is present. Legacy reports
without a roster cannot be checked for omissions; the roster itself still needs
to be verified against the original request. Completed transport alone is not a usable
review. Supply `review` only for substantive results. Normalize its verdict to
accepted, rejected or unclear; the CLI does not grade arbitrary raw text.
Each finding requires a locally adjudicated confirmed/unsupported decision
and evidence. Rejection requires at least one locally confirmed finding.
Minor suggestions should not be treated as rejection without an unmet requirement.

Panel completeness is complete, partial or unavailable. With no usable reviewer,
the outcome is unknown rather than clean. `target_detected` reports a confirmed
injected defect on the incorrect control. `control_rejected` records rejection
of the correct control for possible false-positive analysis; it does not prove
the evaluator's key is infallible. An empty findings list is not a general guarantee.

Unknown cost is null, not zero. Store service time and total session wall time
separately. Additional supplied provenance, version and timing fields are retained.
Never include credentials, personal data or private infrastructure information.

Every import creates an immutable JSON in `reviews/` and appends to
`events.jsonl`. Summary uses the latest event per sample; previous imports
remain available. Changed pinned inputs block recording: create a new pair
revision instead. Control events never enter the official leaderboard ledger.
