"""Explicit state machines for Source Hunter.

    Link status ....... live | dead
    Wording status .... matches | changed | missing   (exact wording on the page)
    Step verdict ...... matches | changed | not_found | no_source
    Trace verdict ..... traced | changed_along_the_way | no_traceable_source
    Run state ......... queued | running | completed | failed

One source of truth; the extension's lib/parse.js mirrors these names exactly.
"""

from __future__ import annotations

from typing import Literal

LinkStatus = Literal["live", "dead"]
WordingStatus = Literal["matches", "changed", "missing"]
StepVerdict = Literal["matches", "changed", "not_found", "no_source"]
TraceVerdict = Literal["traced", "changed_along_the_way", "no_traceable_source"]

LINK_LIVE, LINK_DEAD = "live", "dead"
WORD_MATCHES, WORD_CHANGED, WORD_MISSING = "matches", "changed", "missing"
STEP_MATCHES, STEP_CHANGED, STEP_NOT_FOUND, STEP_NO_SOURCE = (
    "matches",
    "changed",
    "not_found",
    "no_source",
)
TRACED, CHANGED_ALONG_THE_WAY, NO_TRACEABLE = (
    "traced",
    "changed_along_the_way",
    "no_traceable_source",
)


def step_verdict(link_status: str, wording_status: str) -> str:
    """One citation -> one step verdict."""
    if link_status == LINK_DEAD:
        return STEP_NO_SOURCE
    if wording_status == WORD_MATCHES:
        return STEP_MATCHES
    if wording_status == WORD_CHANGED:
        return STEP_CHANGED
    return STEP_NOT_FOUND


def trace_verdict(step_verdicts: list[str]) -> str:
    """Fold the chain into one verdict for the claim itself.

    - any step wording matches an original claim -> traced (even if others changed)
    - no step matches, but at least one 'changed' -> the claim as quoted has drifted
    - nothing verifiable -> be honest, say so
    """
    if not step_verdicts:
        return NO_TRACEABLE
    if STEP_MATCHES in step_verdicts:
        return TRACED
    if STEP_CHANGED in step_verdicts:
        return CHANGED_ALONG_THE_WAY
    return NO_TRACEABLE


def run_state(status: str | None) -> str:
    """Normalize a research run status to lowercase, None or blank -> 'none'."""
    s = (status or "").upper()
    if not s:
        return "none"
    return {
        "COMPLETED": "completed",
        "FAILED": "failed",
        "CANCELLED": "cancelled",
        "QUEUED": "queued",
        "RUNNING": "running",
    }.get(s, s.lower())
