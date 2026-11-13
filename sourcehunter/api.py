"""TinyFish API wrappers for Source Hunter.

  POST /v1/automation/run-research-async   start a research run (returns run_id)
  GET  /v1/research-run/{id}               poll until COMPLETED
  POST api.fetch.tinyfish.ai               verify each source page (Fetch)
  GET  /v1/research-run/{id}/events        optional SSE progress for the extension

All calls use one key; Search/Fetch are free within the daily allowance,
Research deep runs are metered.
"""

from __future__ import annotations

import json
import urllib.request

AGENT = "https://agent.tinyfish.ai"
FETCH = "https://api.fetch.tinyfish.ai"
MAX_POLL_SECONDS = 15 * 60


class ResearchClient:
    def __init__(self, api_key: str, timeout: int = 120):
        self.api_key = api_key
        self.timeout = timeout

    def _req(self, url: str, body: dict | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method="POST" if data is not None else "GET",
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode())

    def start(self, claim: str, mode: str = "deep") -> str:
        d = self._req(
            f"{AGENT}/v1/automation/run-research-async",
            {
                "query": f"Where did this claim originate? Trace it back to the "
                f"earliest reliable original source, showing each step: {claim}",
                "mode": mode,
            },
        )
        return d["research_run_id"]

    def get(self, run_id: str) -> dict:
        return self._req(f"{AGENT}/v1/research-run/{run_id}")

    def wait(self, run_id: str, max_seconds: int = MAX_POLL_SECONDS) -> dict:
        import time

        deadline = time.time() + max_seconds
        while time.time() < deadline:
            d = self.get(run_id)
            if d.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
                return d
            time.sleep(5)
        raise TimeoutError(f"research {run_id} did not finish in {max_seconds}s")


class FetchClient:
    """Verification fetches - also the extension's wording check."""

    def __init__(self, api_key: str, timeout: int = 60):
        self.api_key = api_key
        self.timeout = timeout

    def fetch(self, url: str) -> dict:
        body = json.dumps({"urls": [url], "format": "markdown", "ttl": 0}).encode()
        req = urllib.request.Request(
            FETCH,
            data=body,
            method="POST",
            headers={"X-API-Key": self.api_key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.loads(r.read().decode())
        if d.get("errors"):
            return {"live": False, "error": d["errors"][0].get("error"), "url": url}
        r0 = d["results"][0]
        return {
            "live": True,
            "url": url,
            "final_url": r0.get("final_url") or url,
            "title": r0.get("title") or "",
            "published_date": r0.get("published_date"),
            "text": r0.get("text") or "",
        }
