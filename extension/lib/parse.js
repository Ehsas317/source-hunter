/* Source Hunter - pure logic port (mirrors sourcehunter/parse.py + states.py).
 * No Chrome APIs used here: testable, and identical verdict names to the Python. */

const STOPWORDS = new Set(
  (
    "a an the and or of to in on for with without from by at as is are was " +
    "were be been being this that these those it its their our your his her they we you who whom " +
    "whose which what where when why how if then than so such not no can could would should may " +
    "might will shall do does did done has have had having about into over under again further once " +
    "here there all any both each few more most other some only own same too very just also"
  ).split(" "),
);

const FIRST_DOCUMENTED =
  /(first documented use|earliest documented|first appeared in print|originated in|dates back to|first use in print|earliest known)/i;

export function claimKeywords(claim) {
  const words = (claim.toLowerCase().match(/[a-z']+/g) || []).filter(
    (w) => !STOPWORDS.has(w),
  );
  return [...new Set(words)];
}

export function claimNumbers(claim) {
  const out = (claim.match(/\d+(?:[.,]\d+)?%?/g) || []).slice();
  const spelled = [
    ["ten percent", "10"],
    ["one-tenth", "10"],
    ["one tenth", "10"],
    ["one-tenth of", "10"],
    ["half", "50"],
  ];
  for (const [w, n] of spelled)
    if (claim.toLowerCase().includes(w) && !out.includes(n)) out.push(n);
  return out;
}

function pageNumbers(text) {
  return text.match(/\d+(?:[.,]\d+)?%?/g) || [];
}

export function findExactWording(text, keywords, limit = 3) {
  if (!text || !keywords || !keywords.length) return [];
  const sentences = text.split(/(?<=[.!?])\s+|\n+/);
  const hits = [];
  for (let raw of sentences) {
    const s = raw.replace(/\s+/g, " ").trim();
    if (s.length < 12 || s.length > 600) continue;
    const low = s.toLowerCase();
    const carried = keywords.filter((k) => low.includes(k));
    if (carried.length) hits.push([carried.length, s]);
  }
  hits.sort((a, b) => b[0] - a[0]);
  const out = [],
    seen = new Set();
  for (const [, s] of hits) {
    if (seen.has(s.slice(0, 80))) continue;
    seen.add(s.slice(0, 80));
    out.push(s);
    if (out.length >= limit) break;
  }
  return out;
}

export function classifyWording(text, keywords, numbers) {
  if (!text) return ["missing", []];
  const low = text.toLowerCase();
  if (!keywords.some((k) => low.includes(k))) return ["missing", []];
  const sentences = findExactWording(text, keywords, 10);
  if (!sentences.length) return ["missing", []];
  if (!numbers.length) return ["matches", sentences.slice(0, 3)];
  for (const s of sentences) {
    const nums = pageNumbers(s);
    if (numbers.some((n) => nums.includes(n)))
      return ["matches", sentences.slice(0, 3)];
  }
  return ["changed", sentences.slice(0, 3)];
}

export function reportMarkers(report) {
  const out = [];
  for (const para of (report || "").split("\n")) {
    const m = para.match(FIRST_DOCUMENTED);
    if (m)
      out.push({
        marker: m[1],
        sentence: para.replace(/\s+/g, " ").slice(0, 400),
      });
  }
  return out;
}

export function yearFrom(text) {
  const m = (text || "").match(/\b(1[6-9]\d{2}|20\d{2})\b/);
  return m ? parseInt(m[1], 10) : null;
}

/* ---- verdict machine (same names as states.py) ---- */

export function stepVerdict(link, wording) {
  if (link === "dead") return "no_source";
  if (wording === "matches") return "matches";
  if (wording === "changed") return "changed";
  return "not_found";
}

export function traceVerdict(steps) {
  if (!steps.length) return "no_traceable_source";
  if (steps.includes("matches")) return "traced";
  if (steps.includes("changed")) return "changed_along_the_way";
  return "no_traceable_source";
}
