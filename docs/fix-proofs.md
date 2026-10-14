# Scoped repair evidence (experimental)

SUPERBENCH 0.4 adds separate repair evidence without changing diagnosis scores, existing cases, adjudication, or leaderboard verdicts.

```sh
python3 -m superbench proof-record --expected expected.json --proof proof.json --output assessments/revision-1.json
```

The trusted evaluator supplies expected.json with five SHA-256 bindings: case_sha256, response_sha256, proposal_sha256, recipe_sha256, environment_sha256. They identify the frozen case, original response bytes, exact reviewed repair, check recipe, and runtime manifest. Hex casing is normalized without mutating input objects.

Full proof.json contains those bindings plus scope, exact_proposal, baseline_pass, repair_pass, and checks; see [schema](schemas/fix-proof-v1.schema.json). JSON null means absent evidence. Missing or weak checks remain unverified. A reproduced failing baseline and exact proposal are required. Repair results must be actual Booleans; check counts must be positive integers, excluding true/false. Failed checks yield refuted; passed checks yield supported only within explicit scope.

Malformed or mismatched identity metadata and non-object inputs produce CLI errors. Output is exclusively created: existing revisions cannot be replaced. It includes input hashes, harness version, experimental status, and assessment, without copying response or patch text.

Hashes provide integrity, not authentication or proof of execution. This command validates data; it never executes model code, produces tests, contacts providers, or proves universal correctness. The trusted producer must establish execution and adequate coverage. Manual review remains required and official scores remain unset.

Keep private responses, runtime details and proof files outside public Git. Changes to cases, recipes or environments require new revisions; do not retrofit old results silently.
