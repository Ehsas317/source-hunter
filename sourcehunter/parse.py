"""Pure parsers: research answer -> claim keywords, steps, report markers.

No API key, no network, fully unit-tested.
"""

from __future__ import annotations

import re

_WORD = re.compile(r"[a-zA-Z']+")
_NUM = re.compile(r"\d+(?:[.,]\d+)?%?")

_STOPWORDS = set(
    """
a an the and or of to in on for with without from by at as is are was were be been being
this that these those it its their our your his her they we you who whom whose which what
where when why how if then than so such not no can could would should may might will shall
do does did done has have had having about into over under again further once here there
all any both each few more most other some only own same too very just also
""".split()
)


def claim_keywords(claim: str) -> list[str]:
    """Distinctive terms from the claim, ignoring stopwords.

    Kept so the wording check looks for claim-specific vocabulary
    (e.g. 'brain', 'napoleon', 'wall') rather than generic text.
    """
    words = [w.lower() for w in _WORD.findall(claim) if w.lower() not in _STOPWORDS]
    return list(dict.fromkeys(words))


def claim_numbers(claim: str) -> list[str]:
    """Numbers quoted in the claim ('10%', '6371', '13 percent' -> '13')."""
    out = []
    for m in _NUM.findall(claim):
        out.append(m)
    # spelled-out percent forms
    for w, n in [
        ("ten percent", "10"),
        ("one-tenth", "10"),
        ("one tenth", "10"),
        ("one-tenth of", "10"),
        ("half", "50"),
    ]:
        if w in claim.lower() and n not in out:
            out.append(n)
    return out


def page_numbers(text: str) -> list[str]:
    return _NUM.findall(text)


def find_exact_wording(text: str, keywords: list[str], limit: int = 3) -> list[str]:
    """Sentences on a page that carry claim keywords - the 'exact wording' evidence.

    A sentence counts only if it contains at least one keyword; ranked by how
    many distinct keywords it carries, then by keyword density.
    """
    if not text or not keywords:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    hits = []
    for s in sentences:
        s_clean = " ".join(s.split())
        if len(s_clean) < 12 or len(s_clean) > 600:
            continue
        low = s_clean.lower()
        carried = [k for k in keywords if k in low]
        if carried:
            hits.append((len(carried), s_clean))
    hits.sort(key=lambda h: -h[0])
    out, seen = [], set()
    for _score, s in hits:
        key = s[:80]
        if key not in seen:
            seen.add(key)
            out.append(s)
        if len(out) >= limit:
            break
    return out


def classify_wording(
    page_text: str, keywords: list[str], numbers: list[str]
) -> tuple[str, list[str]]:
    """matches / changed / missing for one source page.

    - missing: page has no claim keywords at all (no wording to compare)
    - matches: claim numbers appear in the same sentences as the keywords
    - changed: keywords appear but the claim numbers do not (narrative drifted)
    """
    if not page_text:
        return "missing", []
    low = page_text.lower()
    if not any(k in low for k in keywords):
        return "missing", []
    sentences = find_exact_wording(page_text, keywords, limit=10)
    if not sentences:
        return "missing", []
    if not numbers:
        return "matches", sentences[:3]
    for s in sentences:
        s_nums = page_numbers(s)
        for n in numbers:
            if n in s_nums:
                return "matches", sentences[:3]
    return "changed", sentences[:3]


FIRST_DOCUMENTED = re.compile(
    r"(first documented use|earliest documented|first appeared in print|originated in|"
    r"dates back to|first use in print|earliest known)",
    re.I,
)
MONTHS = "january february march april may june july august september october november december"


def report_markers(report_md: str) -> list[dict]:
    """Sentences in the research report that assert an origin ('first documented', ...)."""
    out = []
    for para in (report_md or "").split("\n"):
        if "FIRST_DOCUMENTED_PLACEHOLDER" in para:
            continue
        if FIRST_DOCUMENTED.search(para):
            out.append(
                {
                    "marker": FIRST_DOCUMENTED.search(para).group(1),
                    "sentence": " ".join(para.split())[:400],
                }
            )
    return out


def year_from(text: str) -> int | None:
    m = re.search(r"\b(1[6-9]\d{2}|20\d{2})\b", text or "")
    return int(m.group(1)) if m else None
