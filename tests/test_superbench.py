from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from superbench.core import add_review, adjudicate, create_run, get_incident, prepare_bundle, score_response, validate_all, write_json
from superbench.render import render_site


class SuperbenchTests(unittest.TestCase):
    def test_catalog_is_valid(self) -> None:
        self.assertEqual(validate_all(), [])

    def test_bundle_excludes_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "bundle"
            prepare_bundle(get_incident("SB-001"), output)
            self.assertTrue((output / "PROMPT.md").is_file())
            self.assertTrue((output / "fixture" / "repro.py").is_file())
            self.assertFalse(any(path.name == "oracle.json" for path in output.rglob("*")))

    def test_heuristic_distinguishes_grounded_answer(self) -> None:
        incident = get_incident("SB-001")
        correct = "ALREADY_DONE дає status skipped (repro.py:10), logger.debug фільтрує INFO (repro.py:25), але є await process_item (repro.py:21)."
        invented = "Функцію викликали без await, тому це fire-and-forget."
        self.assertGreaterEqual(score_response(incident, correct)["score"], 80)
        self.assertLess(score_response(incident, invented)["score"], 50)

    def test_three_role_reducer(self) -> None:
        incident = get_incident("SB-001")
        response = "status skipped на repro.py:10, logger.debug під INFO на repro.py:25, await process_item на repro.py:21."
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = create_run(incident, "candidate", response, root)
            ids = ("skip-branch", "log-filter", "await-present", "citations")
            roles = {
                "correctness": {"criteria": [{"criterion_id": cid, "status": "met", "candidate_span": cid} for cid in ids]},
                "evidence": {"criteria": [{"criterion_id": cid, "status": "valid", "fixture_span": cid} for cid in ids]},
                "adversarial": {"challenges": []},
            }
            rid = json.loads((run / "response.json").read_text())["response_id"]
            for number, (role, payload) in enumerate(roles.items(), 1):
                source = root / f"{role}.json"
                write_json(source, {"schema_version": 1, "response_id": rid, "agent_role": role, "agent_name": f"fresh-agent-{number}", "confidence": 0.9, **payload})
                add_review(run, source)
            result = adjudicate(run)
            self.assertEqual(result["verdict"], "confirmed")
            self.assertEqual(result["score"], 100)
            self.assertEqual(len(result["reducer_trace"]), 4)

    def test_render_site(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = root / "results"
            results.mkdir()
            (results / "results.jsonl").write_text('{"event":"baseline","model":"Test","verdict":"confirmed"}\n', encoding="utf-8")
            page = render_site(root / "site", results)
            text = page.read_text(encoding="utf-8")
            self.assertIn("SUPERBENCH", text)
            self.assertIn("SB-006", text)


if __name__ == "__main__":
    unittest.main()
