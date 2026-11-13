"""Verdict machine tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sourcehunter.states import (  # noqa: E402
    LINK_DEAD,
    LINK_LIVE,
    STEP_CHANGED,
    STEP_MATCHES,
    STEP_NOT_FOUND,
    STEP_NO_SOURCE,
    TRACED,
    CHANGED_ALONG_THE_WAY,
    NO_TRACEABLE,
    run_state,
    step_verdict,
    trace_verdict,
)


def test_step_verdict_matrix():
    assert step_verdict(LINK_LIVE, "matches") == STEP_MATCHES
    assert step_verdict(LINK_LIVE, "changed") == STEP_CHANGED
    assert step_verdict(LINK_LIVE, "missing") == STEP_NOT_FOUND
    assert step_verdict(LINK_DEAD, "matches") == STEP_NO_SOURCE


def test_trace_verdict_traced_when_any_match():
    assert trace_verdict([STEP_NOT_FOUND, STEP_MATCHES, STEP_NO_SOURCE]) == TRACED


def test_trace_verdict_changed_when_no_match_but_changed():
    assert trace_verdict([STEP_NOT_FOUND, STEP_CHANGED]) == CHANGED_ALONG_THE_WAY


def test_trace_verdict_no_traceable_when_nothing_verifiable():
    assert trace_verdict([STEP_NOT_FOUND, STEP_NO_SOURCE]) == NO_TRACEABLE
    assert trace_verdict([]) == NO_TRACEABLE


def test_run_state():
    assert run_state("COMPLETED") == "completed"
    assert run_state("RUNNING") == "running"
    assert run_state(None) == "none"
