/* Popup: shows the live trace (polls the service worker state). */

const statusEl = document.getElementById("status");
const bodyEl = document.getElementById("body");

function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, '"');
}

function render(s) {
  statusEl.textContent = s.phase || "idle";
  bodyEl.innerHTML = "";
  if (s.error) {
    bodyEl.innerHTML = '<div class="err">' + esc(s.error) + "</div>";
    return;
  }
  if (!s.trace) {
    bodyEl.innerHTML =
      '<div class="idle">No trace yet. Highlight a statistic or quote on any web page and click </div>';
    return;
  }
  const t = s.trace;
  const head = document.createElement("div");
  head.innerHTML =
    '<div style="margin:6px 0 8px"><span class="verdict ' +
    esc(t.trace_verdict) +
    '">' +
    esc(t.trace_verdict) +
    "</span></div>" +
    '<div class="status">claim: ' +
    esc(t.claim || "") +
    "</div>" +
    '<div class="status">steps: ' +
    esc(t.steps_shown) +
    " shown / " +
    esc(t.citations_total) +
    " citations &middot; run " +
    esc(t.research_run_id || "") +
    "</div>";
  bodyEl.appendChild(head);

  if (t.earliest_verifiable_source) {
    const e = t.earliest_verifiable_source;
    const el = document.createElement("div");
    el.className = "step matches";
    el.innerHTML =
      "<b>Earliest verifiable source</b> " +
      '<a href="' +
      esc(e.url) +
      '" target="_blank">' +
      esc(e.url) +
      "</a>" +
      '<div class="quote">published: ' +
      esc(e.published_date || "unknown") +
      (e.quoted && e.quoted[0]
        ? " &mdash; " + esc(e.quoted[0].slice(0, 180))
        : "") +
      "</div>";
    bodyEl.appendChild(el);
  }
  for (const st of t.chain.slice(0, 14)) {
    const el = document.createElement("div");
    el.className = "step " + esc(st.step);
    el.innerHTML =
      "[" +
      esc(st.step) +
      "] " +
      '<a href="' +
      esc(st.url) +
      '" target="_blank">' +
      esc(st.url) +
      "</a>" +
      '<div class="quote">' +
      esc(st.published_date || "") +
      (st.quoted && st.quoted[0]
        ? " &middot; " + esc(st.quoted[0].slice(0, 160))
        : "") +
      "</div>";
    bodyEl.appendChild(el);
  }
}

async function poll() {
  let s = {};
  try {
    s = await chrome.runtime.sendMessage({ type: "GET_STATE" });
  } catch (e) {
    /* worker asleep */
  }
  render(s || { phase: "idle" });
  setTimeout(poll, s && s.running ? 1500 : 4000);
}
poll();
