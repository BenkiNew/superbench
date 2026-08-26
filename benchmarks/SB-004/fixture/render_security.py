import json
from pathlib import Path

STATE = Path(__file__).parent / "state"


def load(name: str) -> dict:
    return json.loads((STATE / name).read_text())


def security_view() -> dict:
    latest = load("latest_scan.json")
    if latest["status"] == "verified":
        source = latest
    else:
        source = load("last_verified.json")
    return {
        "heading": f"Підтверджені знахідки ({len(source['findings'])})",
        "findings": source["findings"],
    }


if __name__ == "__main__":
    print(json.dumps(security_view(), ensure_ascii=False, indent=2))
