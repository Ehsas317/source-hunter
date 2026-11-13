/* Source Hunter service worker: research -> verify -> chain.
 * Mirrors sourcehunter/trace.py exactly (same verdict names, same note fields). */

import {
  claimKeywords,
  claimNumbers,
  classifyWording,
  reportMarkers,
  yearFrom,
  stepVerdict,
  traceVerdict,
} from "./lib/parse.js";

const AGENT = "https://agent.tinyfish.ai";
const FETCH = "https://api.fetch.tinyfish.ai";
const POLL_MS = 5000;
const VERIFY_TOP = 12;

const state = {
  running: false,
  phase: "idle",
  claim: "",
  runId: null,
  error: null,
  trace: null,
};

async function apiKey() {
  const d = await chrome.storage.sync.get(["tinyfishApiKey"]);
  return d.tinyfishApiKey || "";
}

async function api(path, opts = {}) {
  const key = await apiKey();
  const res = await fetch(path, {
    ...opts,
    headers: {
      "X-API-Key": key,
      "Content-Type": "application/json",
      ...(opts.headers || {}),
    },
  });
  if (!res.ok)
    throw new Error(`${opts.method || "GET"} ${path} -> ${res.status}`);
  return res.json();
}

async function verifyOne(url, keywords, numbers) {
  try {
    const d = await api(FETCH, {
      method: "POST",
      body: JSON.stringify({ urls: [url], format: "markdown", ttl: 0 }),
    });
    if (d.errors && d.errors.length)
      return {
        url,
        link: "dead",
        error: String(d.errors[0].error || "fetch error"),
        wording: null,
        quoted: [],
      };
    const r0 = d.results[0];
    const [wording, quoted] = classifyWording(r0.text || "", keywords, numbers);
    return {
      url,
      link: "live",
      wording,
      quoted,
      title: r0.title || "",
      published_date: r0.published_date || null,
      final_url: r0.final_url || url,
    };
  } catch (e) {
    return {
      url,
      link: "dead",
      error: String(e.message || e),
      wording: null,
      quoted: [],
    };
  }
}

async function runTrace(claim) {
  state.running = true;
  state.error = null;
  state.trace = null;
  state.claim = claim;
  state.phase = "starting research";
  try {
    const started = await api(`${AGENT}/v1/automation/run-research-async`, {
      method: "POST",
      body: JSON.stringify({
        query: `Where did this claim originate? Trace it back to the earliest reliable original source, showing each step: ${claim}`,
        mode: "deep",
      }),
    });
    state.runId = started.research_run_id;

    let detail = null;
    for (let i = 0; i < 180; i++) {
      state.phase = `research running (poll ${i + 1})`;
      await new Promise((r) => setTimeout(r, POLL_MS));
      detail = await api(`${AGENT}/v1/research-run/${state.runId}`);
      if (["COMPLETED", "FAILED", "CANCELLED"].includes(detail.status)) break;
    }
    if (!detail || detail.status !== "COMPLETED")
      throw new Error("research did not complete");

    const deep = detail.deep_result || {};
    const report = deep.result || "";
    const citations = [...new Set(deep.citations || [])];
    const keywords = claimKeywords(claim);
    const numbers = claimNumbers(claim);

    state.phase = `verifying ${Math.min(citations.length, VERIFY_TOP)} sources`;
    const settled = await Promise.all(
      citations
        .slice(0, VERIFY_TOP)
        .map((u) => verifyOne(u, keywords, numbers)),
    );
    const rest = citations.slice(VERIFY_TOP).map((u) => ({
      url: u,
      link: "dead",
      wording: null,
      quoted: [],
      note: "not verified (beyond top-N)",
    }));
    const steps = [...settled, ...rest].map((s) => ({
      ...s,
      step: stepVerdict(s.link, s.wording),
    }));

    const years = steps
      .filter(
        (s) =>
          s.link === "live" &&
          ["matches", "changed"].includes(s.wording) &&
          yearFrom(String(s.published_date)),
      )
      .map((s) => [yearFrom(String(s.published_date)), s]);
    const earliest = years.length
      ? years.reduce((a, b) => (b[0] < a[0] ? b : a))[1]
      : null;

    state.trace = {
      claim,
      keywords,
      numbers,
      research_run_id: state.runId,
      research_status: "completed",
      report_markers: reportMarkers(report).slice(0, 5),
      chain: steps,
      earliest_verifiable_source: earliest,
      trace_verdict: traceVerdict(steps.map((s) => s.step)),
      steps_shown: steps.length,
      citations_total: citations.length,
    };
    state.phase = "done";
  } catch (e) {
    state.error = String(e.message || e);
    state.phase = "error";
  } finally {
    state.running = false;
  }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg && msg.type === "TRACE") {
    if (state.running) {
      sendResponse({ ok: false, error: "a trace is already running" });
      return;
    }
    runTrace(msg.claim);
    sendResponse({ ok: true });
  }
  if (msg && msg.type === "GET_STATE") {
    sendResponse({ ...state });
  }
});
