# Security policy

[Українська](SECURITY.md) · **English**

- The benchmark does not require provider API keys. Never add them to Git or GitHub Actions.
- Fixtures must not contain personal data, production documents, tokens, `.env` files, dumps or raw private logs.
- Candidate bundles exclude oracles, historical results and other models' answers.
- If a credential is exposed, revoke it with the provider; removing it only from HEAD is insufficient.
- Fixtures are rewritten, generalized reproductions, not direct copies from private repositories. Replace identifying file, service, host and user names while preserving the failure mechanism.
- CI scans secrets and blocks private infrastructure identifiers in the tracked tree.
- Only the static `site/` directory is published through GitHub Pages. Private server deployments are not exposed by this repository.
- Control keys and evaluator snapshots stay with the evaluator; send only an individual sample bundle to a reviewer.
