#!/usr/bin/env python3
"""Запускає ОДНОГО candidate через OpenAI-сумісний chat/completions API і зберігає answer.md.

Лише локальний інструмент оператора (не CI, не GitHub Actions): ключ читається зі змінної
середовища або з env-файлу поза репозиторієм (типово ~/.config/superbench/clinepass.env,
права 0600) і ніколи не друкується й не зберігається в репо. Модель бачить те саме, що
candidate у bundle: PROMPT.md і файли fixture/ (з нумерацією рядків, щоб можна було цитувати
`файл:рядок`) — жодних oracle-даних. Відправляються ЛИШЕ анонімізовані fixtures benchmark.

За замовчуванням дозволені тільки безкоштовні моделі зі вкладки Free (власник: «лише free»);
будь-яка інша модель відхиляється, доки не передано --allow-any-model.

  python3 scripts/run_openai_candidate.py SB-002 --model deepseek/deepseek-v4.1-flash \
      --out .superbench/runs/SB-002-deepseek.md
  python3 -m superbench score SB-002 .superbench/runs/SB-002-deepseek.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ENV = Path.home() / ".config/superbench/clinepass.env"
# Безкоштовні моделі вкладки Free у Cline (26.09.2026). Pixel Canary в API-списку не знайдено.
# Моделі з ПІДТВЕРДЖЕНИМ нульовим cost у відповіді API (26.09.2026, проба з крихітним запитом).
FREE_MODELS = {
    "stealth/space-bunny-alpha",
    "xiaomi/mimo-v2.6-flash",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "poolside/laguna-s-2.1:free",
}
# Мають позначку FREE у Cline UI або суфікс :free, але через API: метровані (cost>0) або дають HTTP 500.
# Потребують --allow-any-model.
NOT_ZERO_COST_OR_FLAKY = {
    "deepseek/deepseek-v4.1-flash",  # cost>0
    "google/gemini-3.8-flash",       # cost>0
    "meta/muse-spark-1.3-contributor",  # HTTP 500
    "qwen/qwen3.8-27b:free", "google/gemma-4-31b-it:free", "google/gemma-4-26b-a4b-it:free",
    "thinkingmachines/inkling:free",  # HTTP 500
}
SYSTEM = (
    "Ти досвідчений інженер, що розбирає баг за наданим bundle. Відповідай українською, "
    "точно й лише за фактами з файлів. Кожне твердження підкріплюй цитатою у форматі "
    "`шлях/до/файлу:рядок` (номери рядків наведено). Не вигадуй коду, якого немає у файлах."
)


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def build_prompt(bundle: Path) -> str:
    parts = [(bundle / "PROMPT.md").read_text(encoding="utf-8"), "\n\n# Файли bundle\n"]
    for path in sorted((bundle / "fixture").rglob("*")):
        if path.is_file():
            rel = path.relative_to(bundle).as_posix()
            numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1))
            parts.append(f"\n## {rel}\n```\n{numbered}\n```\n")
    return "".join(parts)


def call(base: str, key: str, model: str, prompt: str, max_tokens: int, timeout: int) -> dict:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }).encode()
    request = urllib.request.Request(f"{base.rstrip('/')}/chat/completions", data=body, method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    last: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            last = RuntimeError(f"HTTP {exc.code}: {detail}")
            if exc.code not in (429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
        time.sleep(4 * (attempt + 1))
    raise RuntimeError(str(last))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("incident")
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--max-tokens", type=int, default=6000)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--allow-any-model", action="store_true", help="дозволити не-free модель (може витрачати кредити)")
    args = parser.parse_args()

    if args.model not in FREE_MODELS and not args.allow_any_model:
        print(f"Модель {args.model} не в списку безкоштовних: {', '.join(sorted(FREE_MODELS))}", file=sys.stderr)
        return 2

    load_env(args.env_file)
    key, base = os.environ.get("CLINEPASS_API_KEY", ""), os.environ.get("CLINEPASS_API_BASE", "")
    if not key or not base:
        print("Немає CLINEPASS_API_KEY / CLINEPASS_API_BASE (env або --env-file)", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "superbench", "prepare", args.incident, "--output", tmp, "--force"],
                       cwd=root, check=True, capture_output=True)
        prompt = build_prompt(Path(tmp))

    started = time.time()
    data = call(base, key, args.model, prompt, args.max_tokens, args.timeout)
    data = data.get("data", data)  # Cline API загортає відповідь у {"data": {...}}
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    answer = (message.get("content") or "").strip()
    if not answer:  # частина reasoning-моделей віддає текст лише в reasoning
        answer = (message.get("reasoning") or "").strip()
    gateway = ((message.get("provider_metadata") or {}).get("gateway") or {})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(answer + "\n", encoding="utf-8")
    meta = {"incident": args.incident, "model": args.model, "latency_s": round(time.time() - started, 1),
            "usage": data.get("usage"), "finish_reason": choice.get("finish_reason"),
            "gateway_cost": gateway.get("cost"), "chars": len(answer)}
    args.out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    return 0 if answer else 1


if __name__ == "__main__":
    raise SystemExit(main())
