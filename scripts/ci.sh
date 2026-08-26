#!/usr/bin/env bash
set -euo pipefail

# Деякі fixtures навмисно синтаксично пошкоджені — це предмет benchmark,
# тому compile gate застосовується лише до harness/runner/tests.
python3 -m compileall -q superbench scripts tests
python3 -m superbench validate
python3 -m unittest discover -s tests -v
python3 -m superbench render --output site

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks git --redact --no-banner
else
  echo "[ci] gitleaks unavailable; GitHub Actions installs it separately" >&2
fi
