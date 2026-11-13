"""Pure parser tests - no API key, no network."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sourcehunter.parse import (  # noqa: E402
    classify_wording,
    claim_keywords,
    claim_numbers,
    find_exact_wording,
    report_markers,
    year_from,
)

CLAIM = "Humans only use 10% of their brain"


def test_claim_keywords_ignores_stopwords():
    kws = claim_keywords(CLAIM)
    assert "humans" in kws and "brain" in kws
    assert "of" not in kws and "their" not in kws


def test_claim_numbers_digits_and_words():
    assert "10%" in claim_numbers(CLAIM)
    assert "10" in claim_numbers("one-tenth of your brain-power")
    assert "50" in claim_numbers("half the brain")


def test_find_exact_wording_returns_sentences_with_keywords():
    text = (
        "The great pyramid was built by thousands of workers. "
        "Brain imaging shows most of the brain is active. "
        "Unrelated sentence about weather."
    )
    hits = find_exact_wording(text, ["brain", "imaging"], limit=3)
    assert any("brain" in h.lower() for h in hits)
    assert all("weather" not in h.lower() for h in hits)


def test_classify_matches_when_number_in_keyword_sentence():
    page = (
        "Studies show humans use more than 10% of their brain. Other text about cars."
    )
    status, quoted = classify_wording(page, ["humans", "brain"], ["10%"])
    assert status == "matches" and quoted


def test_classify_changed_when_number_missing():
    page = "Humans use most of their brain, scientists say. Brain scans confirm this."
    status, quoted = classify_wording(page, ["humans", "brain"], ["10%"])
    assert status == "changed"


def test_classify_missing_when_no_keywords():
    status, quoted = classify_wording("The weather is nice today.", ["napoleon"], [])
    assert status == "missing" and quoted == []


def test_report_markers_finds_first_documented():
    md = "The first documented use of the phrase in print was in 1929.\nOther line."
    markers = report_markers(md)
    assert markers and "1929" in markers[0]["sentence"]


def test_year_from():
    assert year_from("published 1936-xx") == 1936
    assert year_from("no date") is None
