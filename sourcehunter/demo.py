"""The 5-claim demo the bounty asks for (incl. at least one claim that is wrong).

Each claim is a real TinyResearch run + live Fetch verification of every citation.
Outputs: examples/demo-<slug>.json (+ one combined markdown report).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .trace import trace

DEMO_CLAIMS = [
    {
        "id": "brain-10-percent",
        "claim": "Humans only use 10% of their brain",
        "expectation": "wrong - myth traced to 1929 advertising; James said 'a small part', no percentage",
    },
    {
        "id": "napoleon-height",
        "claim": "Napoleon Bonaparte was short",
        "expectation": "wrong - average height for his era; British propaganda + French/British inch units",
    },
    {
        "id": "great-wall-space",
        "claim": "The Great Wall of China is visible from space with the naked eye",
        "expectation": "contested - astronauts said yes from low orbit; broadly false from the Moon",
    },
    {
        "id": "carrots-eyesight",
        "claim": "Carrots improve your eyesight",
        "expectation": "wrong - WWII propaganda covering for radar; vitamin A link real but not night vision",
    },
    {
        "id": "emc-1905",
        "claim": "Albert Einstein published E=mc2 in 1905",
        "expectation": "true - traces to the 1905 Annalen der Physik paper, a real primary source",
    },
]


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def run_demo(
    research, fetch, out_dir: str = "examples", verify_top: int = 8
) -> list[dict]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for spec in DEMO_CLAIMS:
        print(f"[demo] {spec['id']}: tracing '{spec['claim']}' ...")
        t = trace(spec["claim"], research, fetch, verify_top=verify_top)
        t["expected_outcome"] = spec["expectation"]
        t["demo_id"] = spec["id"]
        (out / f"demo-{spec['id']}.json").write_text(json.dumps(t, indent=2))
        results.append(t)
        print(
            f"[demo] {spec['id']}: verdict={t['trace_verdict']} steps={t['steps_shown']}"
        )
    return results


def summary_markdown(results: list[dict]) -> str:
    lines = ["# Source Hunter - demo report", ""]
    for t in results:
        lines.append(f"## {t['demo_id']}: {t['claim']}")
        lines.append(f"- Expected: {t['expected_outcome']}")
        lines.append(
            f"- Trace verdict: **{t['trace_verdict']}** "
            f"(steps shown: {t['steps_shown']} of {t['citations_total']} citations)"
        )
        e = t.get("earliest_verifiable_source")
        if e:
            lines.append(
                f"- Earliest verifiable source: {e['url']} "
                f'(published: {e.get("published_date")}) - "{e["quoted"][0][:160]}"'
                if e.get("quoted")
                else f"- Earliest verifiable source: {e['url']} (published: {e.get('published_date')})"
            )
        else:
            lines.append("- Earliest verifiable source: none found")
        for s in t["chain"][:6]:
            lines.append(f"  - [{s['step']}] {s['url']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import os
    from .api import FetchClient, ResearchClient

    key = os.environ.get("TINYFISH_API_KEY", "")
    if not key:
        raise SystemExit("TINYFISH_API_KEY not set")
    results = run_demo(ResearchClient(key), FetchClient(key))
    Path("examples/DEMO-REPORT.md").write_text(summary_markdown(results))
    print("wrote examples/DEMO-REPORT.md")
