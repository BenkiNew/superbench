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

# 26.08.2026: gitleaks ловить лише секрето-подібні патерни (ключі, токени),
# не internal hostnames/IP з приватної інфраструктури, звідки анонімізуються
# інциденти. Перевіряємо весь публічний tracked tree, а не лише fixtures.
DENYLIST=(
  'benkigeek'
  'benkiserver'
  '100\.97\.13\.'
  '100\.88\.122\.'
  '\.cloud\.lan'
)
LEAK_FOUND=0
for pattern in "${DENYLIST[@]}"; do
  if git ls-files -z | grep -zv '^scripts/ci.sh$' | xargs -0 grep -InE "$pattern" -- 2>/dev/null; then
    echo "[ci] internal identifier in public tracked tree: $pattern" >&2
    LEAK_FOUND=1
  fi
done
if [ "$LEAK_FOUND" -ne 0 ]; then
  echo "[ci] internal hostname/IP denylist failed in benchmarks/ — see matches above" >&2
  exit 1
fi
