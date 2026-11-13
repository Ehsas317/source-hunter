"""Trace orchestration: research -> parse -> verify (Fetch) -> structured chain."""

from __future__ import annotations

import json

from .api import FetchClient, ResearchClient
from .parse import (
    classify_wording,
    claim_keywords,
    claim_numbers,
    report_markers,
)
from .states import (
    LINK_LIVE,
    TRACED,
    run_state,
    step_verdict,
    trace_verdict,
)


def _result_of(detail: dict) -> tuple[str, list[str]]:
    """Research detail -> (report markdown, citations)."""
    deep = detail.get("deep_result") or {}
    report = (
        deep.get("result") or detail.get("quick_result", {}).get("answer", "") or ""
    )
    citations = deep.get("citations") or []
    return report, list(dict.fromkeys(citations))


def trace(
    claim: str,
    research: ResearchClient,
    fetch: FetchClient,
    verify_top: int = 12,
    mode: str = "deep",
) -> dict:
    keywords = claim_keywords(claim)
    numbers = claim_numbers(claim)

    run_id = research.start(claim, mode=mode)
    detail = research.wait(run_id)
    report, citations = _result_of(detail)

    steps = []
    for url in citations[:verify_top]:
        page = fetch.fetch(url)
        if not page.get("live"):
            steps.append(
                {
                    "url": url,
                    "link": "dead",
                    "wording": None,
                    "step": step_verdict("dead", "missing"),
                    "quoted": [],
                    "error": page.get("error"),
                    "published_date": None,
                }
            )
            continue
        wording, quoted = classify_wording(page["text"], keywords, numbers)
        steps.append(
            {
                "url": url,
                "link": LINK_LIVE,
                "wording": wording,
                "step": step_verdict(LINK_LIVE, wording),
                "quoted": quoted,
                "title": page.get("title"),
                "published_date": page.get("published_date"),
                "final_url": page.get("final_url") or url,
            }
        )
    for url in citations[verify_top:]:
        steps.append(
            {
                "url": url,
                "link": "dead",
                "wording": None,
                "step": step_verdict("dead", "missing"),
                "quoted": [],
                "note": "not verified (beyond top-N)",
            }
        )

    # earliest verifiable source: by published_date year of live steps that carry wording
    from .parse import year_from

    live_years = []
    for s in steps:
        d = s.get("published_date") or ""
        y = year_from(str(d))
        if s["link"] == LINK_LIVE and s.get("wording") in ("matches", "changed") and y:
            live_years.append((y, s))
    earliest = min(live_years, key=lambda t: t[0])[1] if live_years else None

    verdicts = [s["step"] for s in steps]
    return {
        "claim": claim,
        "claim_keywords": keywords,
        "claim_numbers": numbers,
        "research_run_id": run_id,
        "research_status": run_state(detail.get("status")),
        "report_markers": report_markers(report)[:5],
        "chain": steps,
        "earliest_verifiable_source": earliest,
        "trace_verdict": trace_verdict(verdicts),
        "steps_shown": len(steps),
        "citations_total": len(citations),
        "report": report,
    }


def to_json(t: dict) -> str:
    return json.dumps(t, indent=2)
