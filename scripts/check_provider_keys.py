#!/usr/bin/env python3
"""Validate pasted provider credentials without printing them."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def extract(text: str, pattern: str, label: str) -> str:
    match = re.search(pattern, text)
    if not match:
        raise SystemExit(f"{label}: key not found")
    return match.group(0)


def models(label: str, url: str, key: str) -> list[str]:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
            print(f"{label}: HTTP {response.status}, credential accepted")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        try:
            parsed = json.loads(body)
            detail = parsed.get("error", parsed)
            if isinstance(detail, dict):
                detail = detail.get("message") or detail.get("detail") or detail.get("code")
        except json.JSONDecodeError:
            detail = re.sub(r"[A-Za-z0-9_-]{20,}", "[redacted]", body).strip()
        print(f"{label}: HTTP {exc.code}: {detail or 'credential rejected or unavailable'}")
        return []
    return sorted(str(item.get("id")) for item in payload.get("data", []) if item.get("id"))


def main() -> int:
    source = Path(sys.argv[1]).read_text(encoding="utf-8")
    groq_key = extract(source, r"gsk_[A-Za-z0-9_-]+", "Groq")
    cerebras_key = extract(source, r"csk-[A-Za-z0-9_-]+", "Cerebras")
    groq = models("Groq", "https://api.groq.com/openai/v1/models", groq_key)
    cerebras = models("Cerebras", "https://api.cerebras.ai/v1/models", cerebras_key)
    preferred_groq = [item for item in ("openai/gpt-oss-120b", "qwen/qwen3.6-27b") if item in groq]
    preferred_cerebras = [item for item in ("gpt-oss-120b", "zai-glm-4.7") if item in cerebras]
    print("Groq preferred available:", ", ".join(preferred_groq) or "none")
    print("Cerebras preferred available:", ", ".join(preferred_cerebras) or "none")
    return 0 if preferred_groq and preferred_cerebras else 1


if __name__ == "__main__":
    raise SystemExit(main())
