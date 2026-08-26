from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .core import collect_runs, incidents


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def ledger_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: invalid JSONL: {exc}") from exc
        if isinstance(value, dict):
            rows.append(value)
    return rows


def leaderboard(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    final_events = {"baseline", "adjudication_finished"}
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"runs": 0, "confirmed": 0, "partial": 0, "rejected": 0, "infra": 0, "latencies": []}
    )
    for row in rows:
        if row.get("event") not in final_events and row.get("verdict") != "infra_error":
            continue
        model = str(row.get("model", "unknown"))
        stats = grouped[model]
        stats["runs"] += 1
        verdict = row.get("verdict")
        if verdict == "confirmed":
            stats["confirmed"] += 1
        elif verdict == "partial":
            stats["partial"] += 1
        elif verdict == "rejected":
            stats["rejected"] += 1
        elif verdict == "infra_error":
            stats["infra"] += 1
        if isinstance(row.get("latency_ms"), int):
            stats["latencies"].append(row["latency_ms"])
    result = []
    for model, stats in grouped.items():
        scored = stats["confirmed"] + stats["partial"] + stats["rejected"]
        result.append(
            {
                "model": model,
                **stats,
                "quality": round((stats["confirmed"] + 0.5 * stats["partial"]) / scored * 100) if scored else 0,
                "reliability": round((stats["runs"] - stats["infra"]) / stats["runs"] * 100) if stats["runs"] else 0,
                "latency": round(sum(stats["latencies"]) / len(stats["latencies"])) if stats["latencies"] else None,
            }
        )
    return sorted(result, key=lambda item: (item["quality"], item["reliability"], item["confirmed"]), reverse=True)


def render_site(output: Path, results_root: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    (output / "assets").mkdir(exist_ok=True)
    catalog = incidents()
    ledger = ledger_rows(results_root / "results.jsonl")
    runs = collect_runs(results_root)
    board = leaderboard(ledger)
    incident_cards = "".join(
        f'''<article class="case"><div class="case-top"><span>{e(item.id)}</span><b>{e(item.data['difficulty'])}</b></div><h3>{e(item.data['title'])}</h3><p>{e(item.data['summary'])}</p><div class="tags">{''.join(f'<i>{e(tag)}</i>' for tag in item.data['tags'])}</div></article>'''
        for item in catalog
    )
    board_rows = "".join(
        f'''<tr><td><strong>{index}</strong></td><td><b>{e(item['model'])}</b></td><td>{item['quality']}%</td><td>{item['reliability']}%</td><td>{item['confirmed']}</td><td>{item['infra']}</td><td>{str(item['latency'])+' ms' if item['latency'] else '—'}</td></tr>'''
        for index, item in enumerate(board, 1)
    ) or '<tr><td colspan="7">Результати ще накопичуються.</td></tr>'
    recent_rows = "".join(
        f'''<li><span>{e(item.get('incident_id'))}</span><b>{e(item.get('model'))}</b><i class="{e(item.get('panel_status','pending'))}">{e(item.get('panel_status','pending'))}</i></li>'''
        for item in runs[:8]
    ) or '<li><b>Нові agent-panel результати ще не записані</b></li>'
    page = f'''<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>SUPERBENCH · AI Agent Benchmark</title><link rel="stylesheet" href="/assets/app.css"></head><body><main><header><nav><div class="logo">SB</div><b>SUPERBENCH</b><span>REAL INCIDENTS · VERIFIED ANSWERS</span></nav><div class="hero"><div><p class="eyebrow">XAKERBANK · CX43 LAB</p><h1>Бенчмарк, якому<br><em>є що доводити.</em></h1><p class="lead">Реальні анонімізовані інциденти, ізольовані fixtures та три незалежні reviewer-агенти для кожної відповіді.</p><div class="hero-stats"><span><b>{len(catalog)}</b> інцидентів</span><span><b>3</b> reviewers</span><span><b>3×</b> max retry</span></div></div><aside><span>PIPELINE</span><ol><li><b>01</b> Isolated bundle</li><li><b>02</b> Candidate agent</li><li><b>03</b> Correctness review</li><li><b>04</b> Evidence review</li><li><b>05</b> Adversarial review</li><li><b>06</b> Deterministic reducer</li></ol></aside></div></header><section><div class="section-title"><div><span>01</span><h2>Каталог інцидентів</h2></div><p>Не toy-задачі — мінімальні відтворення реальних відмов</p></div><div class="cases">{incident_cards}</div></section><section><div class="section-title"><div><span>02</span><h2>Лідерборд</h2></div><p>Якість окремо від стабільності провайдера</p></div><div class="table-wrap"><table><thead><tr><th>#</th><th>Модель</th><th>Якість</th><th>Надійність</th><th>Confirmed</th><th>Infra error</th><th>Avg latency</th></tr></thead><tbody>{board_rows}</tbody></table></div></section><section class="split"><div><div class="section-title"><div><span>03</span><h2>Останні відповіді</h2></div></div><ul class="recent">{recent_rows}</ul></div><div class="principles"><span>TRUST MODEL</span><h2>Один агент не судить іншого одноосібно.</h2><p>Correctness розмічає атомарні факти. Evidence звіряє file:line. Adversarial впливає лише відтвореним контрприкладом. Reducer лишає replayable trace.</p></div></section><footer><b>SUPERBENCH 0.2</b><span>Markdown source of truth · append-only JSONL · no secrets in Git</span></footer></main></body></html>'''
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "assets" / "app.css").write_text(CSS, encoding="utf-8")
    return output / "index.html"


CSS = r''':root{--bg:#080c13;--panel:#101824;--line:#263447;--text:#f2f6fb;--muted:#8797aa;--blue:#57a8ff;--green:#4ed6a0;--orange:#ffb454}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 85% 0,#122d50 0,transparent 30rem),var(--bg);color:var(--text);font:14px/1.55 Inter,system-ui,sans-serif}main{width:min(1180px,calc(100% - 36px));margin:auto}header{padding:28px 0 64px;border-bottom:1px solid var(--line)}nav{display:flex;align-items:center;gap:12px;font:12px ui-monospace,monospace;letter-spacing:.12em}nav>span{margin-left:auto;color:#63758d}.logo{display:grid;place-items:center;width:36px;height:36px;border-radius:9px;background:#102a48;border:1px solid #2d6096;color:var(--blue);font-weight:900}.hero{display:grid;grid-template-columns:1.5fr .7fr;gap:70px;align-items:end;padding-top:72px}.eyebrow,.section-title span,.principles>span{color:var(--blue);font:700 11px ui-monospace,monospace;letter-spacing:.16em}h1{font-size:clamp(46px,7vw,82px);line-height:.98;letter-spacing:-.06em;margin:12px 0 25px}h1 em{font-style:normal;color:var(--blue)}.lead{max-width:700px;color:var(--muted);font-size:17px}.hero-stats{display:flex;gap:28px;margin-top:30px;color:#78899d}.hero-stats b{color:#fff;font-size:22px;margin-right:5px}.hero aside{padding:22px;border:1px solid #27425f;border-radius:14px;background:#0c1623}.hero aside>span{font:10px ui-monospace,monospace;color:var(--green)}ol{list-style:none;margin:18px 0 0;padding:0}ol li{padding:8px 0;border-top:1px solid #1c2a3b;color:#9aabbd}ol b{color:#4f6680;margin-right:10px}section{padding-top:54px}.section-title{display:flex;align-items:end;justify-content:space-between;margin-bottom:20px}.section-title>div{display:flex;align-items:center;gap:12px}.section-title h2{margin:0;font-size:23px}.section-title p{margin:0;color:#62748a;font-size:12px}.cases{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.case{padding:21px;border:1px solid var(--line);border-radius:13px;background:linear-gradient(145deg,#111a27,#0c121c);min-height:220px}.case-top{display:flex;justify-content:space-between;color:var(--blue);font:10px ui-monospace,monospace}.case-top b{color:var(--orange);text-transform:uppercase}.case h3{font-size:17px;line-height:1.25;margin:25px 0 9px}.case p{color:var(--muted);font-size:12px;min-height:57px}.tags{display:flex;flex-wrap:wrap;gap:5px}.tags i{font-style:normal;font:9px ui-monospace,monospace;color:#8296ad;padding:3px 6px;border:1px solid #2a3a4f;border-radius:99px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:13px;background:#0d141e}table{border-collapse:collapse;width:100%;min-width:720px}th,td{text-align:left;padding:15px 17px;border-bottom:1px solid #1d2938}th{font:9px ui-monospace,monospace;letter-spacing:.1em;color:#6f8299}td:first-child strong{color:var(--blue)}.split{display:grid;grid-template-columns:1fr 1fr;gap:26px}.recent{list-style:none;margin:0;padding:0;border:1px solid var(--line);border-radius:13px;overflow:hidden}.recent li{display:grid;grid-template-columns:80px 1fr auto;gap:10px;padding:13px 15px;border-bottom:1px solid #1d2938}.recent span{color:var(--blue);font:10px ui-monospace,monospace}.recent i{font:9px ui-monospace,monospace;text-transform:uppercase}.confirmed{color:var(--green)}.rejected{color:#ff6b7a}.pending,.partial{color:var(--orange)}.principles{padding:28px;border:1px solid #285477;border-radius:13px;background:#0d1b29}.principles h2{font-size:27px;line-height:1.15}.principles p{color:#95a7ba}footer{display:flex;justify-content:space-between;margin-top:62px;padding:25px 0 35px;border-top:1px solid var(--line);color:#5e7187;font:10px ui-monospace,monospace}@media(max-width:850px){.hero,.split{grid-template-columns:1fr}.cases{grid-template-columns:repeat(2,1fr)}}@media(max-width:560px){.cases{grid-template-columns:1fr}.hero{padding-top:42px}.section-title p,nav>span{display:none}footer{flex-direction:column;gap:8px}}'''
