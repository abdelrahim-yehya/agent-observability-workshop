#!/usr/bin/env python3
"""Draw two flow diagrams of the tool-selection rules.

  results/selection_flow.svg      the first selection (C1 applied to every tool), as in the paper's funnel table
  results/selection_flow_new.svg  the strategy of the 2026-11-09 amendment (adoption for open source, Google for closed source)
  results/selection_flow_simple.svg  the same strategy, simplified to the essential steps


The boxes state the rules of docs/search_protocol.md and docs/screening_rules.md as they were applied (search frozen
2026-10-22) with the counts of the paper's funnel table. Orange outlines mark the criteria that depend on Google source
counts (I3, C1, S4). Counts are typed here, not computed; update them if the data change.

Output:  results/selection_flow.svg   (fixed light colours)
PNG:     "Brave Browser" --headless --force-device-scale-factor=2 --window-size=1100,<height> --screenshot=results/selection_flow.png file://.../selection_flow.svg
Run:     python3 src/plot_selection_flow.py
"""
from html import escape

from paths import ROOT

W = 1100
FONT = "Helvetica, Arial, 'Liberation Sans', sans-serif"
INK, MUTED, LINE = "#1d2328", "#5d666d", "#8a8f94"
STYLE = {  # fill, stroke
    "channel": ("#e8f1f5", "#1f6f8b"),
    "rule": ("#ffffff", "#5d666d"),
    "google": ("#fff4ea", "#d9822b"),
    "count": ("#f4f2ee", "#8a8f94"),
    "result": ("#e9f4ea", "#3c8a4a"),
    "metric": ("#f3eefa", "#6f4fa0"),
    "adopt": ("#e6f6f1", "#1e8e6e"),
}
out, boxes = [], {}


def reset():
    out.clear()
    boxes.clear()


def box(key, x, y, w, title, lines, style="rule", result=None):
    fill, stroke = STYLE[style]
    n = len(lines) + (1 if result else 0)
    h = 16 + 18 + n * 15 + 8
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="{2.2 if style in ("google", "adopt") else 1.4}"/>')
    out.append(f'<text x="{x + 12}" y="{y + 21}" font-size="13" font-weight="700" fill="{INK}">{escape(title)}</text>')
    yy = y + 40
    for s in lines:
        out.append(f'<text x="{x + 12}" y="{yy}" font-size="11.5" fill="{INK}">{escape(s)}</text>')
        yy += 15
    if result:
        out.append(f'<text x="{x + 12}" y="{yy}" font-size="12" font-weight="700" fill="{stroke}">{escape(result)}</text>')
    boxes[key] = (x, y, w, h)
    return h


def arrow(a, b, label="", side="down", tx=0.5, label_at=None):
    ax, ay, aw, ah = boxes[a]
    bx, by, bw, bh = boxes[b]
    if side == "down":
        x1, y1, x2, y2 = ax + aw / 2, ay + ah, bx + bw * tx, by
        path = f"M{x1},{y1} L{x2},{y2}" if abs(x1 - x2) < 2 else f"M{x1},{y1} L{x1},{(y1 + y2) / 2} L{x2},{(y1 + y2) / 2} L{x2},{y2}"
    else:  # right
        x1, y1, x2, y2 = ax + aw, ay + ah / 2, bx, by + bh / 2
        path = f"M{x1},{y1} L{x2},{y2}"
    out.append(f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="1.5" marker-end="url(#ah)"/>')
    if label:
        lx, ly = label_at or ((x2 + 8, (y1 + y2) / 2 + 4) if side == "down" else ((x1 + x2) / 2, y1 - 6))
        out.append(f'<text x="{lx}" y="{ly}" font-size="11" fill="{MUTED}" {"" if side == "down" else "text-anchor=\"middle\""}>{escape(label)}</text>')


def note(x, y, lines, color=MUTED):
    for i, s in enumerate(lines):
        out.append(f'<text x="{x}" y="{y + i * 14}" font-size="11" fill="{color}">{escape(s)}</text>')


def draw_current():
    reset()
    out.append(f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>')
    out.append(f'<text x="30" y="34" font-size="21" font-family="Georgia,serif" fill="{INK}">How tools were selected: first selection (C1 for every tool)</text>')
    out.append(f'<text x="30" y="55" font-size="12" fill="{MUTED}">As applied (search frozen 2026-10-22). Orange outline: the criterion depends on Google source counts. Counts are from the paper\'s funnel table.</text>')

    box("gh", 30, 80, 330, "1 · GitHub search (open source)", ["10 topic and 7 keyword queries, sorted by stars", "I2 in the query: at least 1,000 stars, not archived,", "a push in the last 6 months"], "channel")
    box("go", 385, 80, 330, "2 · Google search (open and closed source)", ["6 queries, first 30 results each (173 results)", "titles and snippets only, one day, signed out", "records every tool named (68 tools)"], "channel")
    box("st", 740, 80, 330, "3 · Standards", ["OpenTelemetry GenAI conventions as the", "vendor-neutral reference (also named by Google)"], "channel")

    box("gh2", 30, 200, 330, "Manual check of the 182 repositories", ["I1: primary purpose is tracing, monitoring or", "evaluating LLM applications or agents", "not E1 gateway, E2 agent framework,", "E3 model benchmark harness, E4 tutorial or list"], "rule", "37 kept  (145 removed)")
    box("go2", 385, 200, 330, "Screening of the 68 tools named", ["I1 purpose; E1 to E5; E6 drops general-purpose", "platforms (Datadog, Grafana)", "Open source: I2 stars and activity (Ragas out)", "Closed source: I3 public docs and 2 independent", "sources; C1 at least 2 independent sources"], "google", "13 kept  (55 removed)")
    arrow("gh", "gh2"); arrow("go", "go2")

    box("merge", 220, 380, 660, "Merge the lists (E5: an SDK and its platform count as one tool)", ["37 from GitHub + 5 found only by Google (LangSmith, Braintrust, Galileo, Weave, OpenTelemetry)"], "rule", "42 candidates")
    arrow("gh2", "merge", "37", tx=0.25, label_at=(203, 342)); arrow("go2", "merge", "13 (8 of them also on GitHub)", tx=0.75, label_at=(560, 350))
    out.append(f'<path d="M905,{80 + 16 + 18 + 2 * 15 + 8} L905,{380 + 36} L880,{380 + 36}" fill="none" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#ah)"/>')

    box("s1", 220, 490, 660, "S1 scope (decided from the tool's own description)", ["Keep: primary purpose is observability or evaluation of LLM applications or agents.", "Out: benchmarks, prompt formats, MCP-only testing, broader suites, end-user applications,", "general-purpose observability platforms."], "rule", "31 kept  (11 removed, one borderline treated as out)")
    arrow("merge", "s1", "42")
    box("s2", 220, 610, 660, "S2 role label (no removal)", ["standard: telemetry conventions or instrumentation  ·  platform: stores and shows traces, offers evaluation", "framework: library or CLI that runs evaluations, no trace backend"], "rule")
    arrow("s1", "s2", "31")
    box("a1", 130, 720, 380, "A1 agent relevance", ["Official docs explicitly cover agents, tool calls or", "multi-step traces; the quote is checked against", "a saved copy of the page", ""], "rule")
    box("c1", 560, 720, 410, "C1 corroboration  (applies to every tool)", ["At least 2 independent sources in the Google log;", "the tool's own website does not count; a competitor's", "comparison post does count. Added after the first Google run"], "google", "13 pass  /  18 fail")
    arrow("s2", "a1"); arrow("a1", "c1", side="right")
    box("s4", 330, 900, 440, "S4 ranking (orders only, does not select)", ["Independent Google sources, then GitHub stars"], "google")
    arrow("c1", "s4", "13", label_at=(775, 880))
    note(790, 925, ["The 18 that fail are open-source tools", "found through GitHub, for example", "MLflow (0 independent sources),", "Evidently (0), Laminar (0), OpenLIT (0),", "LangWatch (1), AgentOps (1), TruLens (1)."])
    box("res", 190, 990, 720, "Result: 13 entries", ["10 tools: 9 platforms and 1 framework  +  3 standards (OpenTelemetry, OpenLLMetry, OpenInference)", "The paper reports the standards apart from the tools (S2)"], "result")
    arrow("s4", "res")

    ys = 1130
    xs = [30, 300, 570, 840]
    titles = [("S3 built-in metrics", ["Metrics the tool ships, read from", "official docs: URL, verbatim quote,", "saved page, access date"]),
              ("M1 metric scope", ["Keep how a run executes or how good", "its output is. Drop text match, retrieval,", "audio, image, task-specific, custom-only"]),
              ("Result: 231 built-in rows", ["193 from the ten tools and", "38 from the three standards"]),
              ("Mapping to unique metrics", ["Hand-made, one row per pair:", "45 unique metrics (18 + 27) and 1 that", "only standards document"])]
    for i, (t, ls) in enumerate(titles):
        box(f"m{i}", xs[i], ys, 240, t, ls, "metric")
    arrow("res", "m0")
    for i in range(3):
        arrow(f"m{i}", f"m{i + 1}", side="right")
    height = ys + 110

    out.append(f'<rect x="30" y="{height - 6}" width="22" height="12" rx="3" fill="{STYLE["google"][0]}" stroke="{STYLE["google"][1]}" stroke-width="2.2"/>')
    note(60, height + 4, ["depends on Google source counts (I3 for closed-source tools, C1, S4)"])
    out.append(f'<rect x="440" y="{height - 6}" width="22" height="12" rx="3" fill="{STYLE["rule"][0]}" stroke="{STYLE["rule"][1]}" stroke-width="1.4"/>')
    note(470, height + 4, ["other rule (I1, I2, E1 to E6, S1, S2, A1, M1)"])
    height += 30

    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-family="{FONT}" role="img" aria-label="Flow diagram of the tool selection rules"><rect width="{W}" height="{height}" fill="#ffffff"/>'
    target = ROOT / "results" / "selection_flow.svg"
    target.write_text(head + "\n".join(out) + "</svg>", encoding="utf-8")
    print(f"wrote {target}: {W}x{height}")


def draw_new():
    reset()
    out.append(f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>')
    out.append(f'<text x="30" y="34" font-size="21" font-family="Georgia,serif" fill="{INK}">Search strategy from 2026-11-09 (post-hoc amendment)</text>')
    out.append(f'<text x="30" y="55" font-size="12" fill="{MUTED}">Open-source tools are selected by adoption (C2), closed-source tools by Google corroboration (C1). E1 to E6, S1, S2 and A1 are unchanged. Green: new rule; orange: Google-based.</text>')

    box("gh", 30, 80, 330, "1 · GitHub search (open source)", ["10 topic and 7 keyword queries, sorted by stars", "I2 in the query: at least 1,000 stars, not archived,", "a push in the last 6 months"], "channel")
    box("go", 385, 80, 330, "2 · Google search (closed source, and discovery)", ["6 queries, first 30 results each (173 results)", "titles and snippets only, one day, signed out", "evidence for closed-source tools (I3, C1)"], "channel")
    box("st", 740, 80, 330, "3 · Standards", ["OpenTelemetry GenAI conventions as the", "vendor-neutral reference (also named by Google)"], "channel")
    box("gh2", 30, 200, 330, "Manual check of the 182 repositories", ["I1 purpose; not E1 gateway, E2 agent framework,", "E3 benchmark harness, E4 tutorial or list"], "rule", "37 kept  (145 removed)")
    box("go2", 385, 200, 330, "Screening of the 68 tools named", ["I1 purpose; E1 to E6 (E6 drops general-purpose", "platforms such as Datadog and Grafana)"], "rule")
    arrow("gh", "gh2"); arrow("go", "go2")
    box("merge", 220, 340, 660, "Merge the lists (E5: an SDK and its platform count as one tool)", ["37 from GitHub + 5 found only by Google (LangSmith, Braintrust, Galileo, Weave, OpenTelemetry)"], "rule", "42 candidates (unchanged)")
    arrow("gh2", "merge", "37", tx=0.25, label_at=(203, 332)); arrow("go2", "merge", "5 closed-source", tx=0.75, label_at=(560, 330))
    out.append(f'<path d="M905,{80 + 16 + 18 + 2 * 15 + 8} L905,{340 + 36} L880,{340 + 36}" fill="none" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#ah)"/>')
    box("s1", 220, 450, 660, "S1 scope  ·  S2 role label  ·  A1 agent relevance (unchanged)", ["S1 keeps tools whose primary purpose is observability or evaluation of LLM apps or agents (31 kept, 11 removed);", "S2 labels standard, platform or framework; A1 needs official docs that cover agents, tool calls or multi-step traces."], "rule", "31 candidates: 26 open source with a repository, 5 without")
    box("c2", 60, 580, 480, "C2 adoption  (open-source tools)", ["I2: at least 1,000 stars, not archived, push in the last 6 months", "and at least 5,000 stars, or at least 1M downloads in 30 days", "(larger of PyPI and npm); with a package, at least 100k downloads", "Stars, push and downloads read on one date (2026-11-06)"], "adopt", "14 pass  ·  12 fail (11 adoption, 1 activity)")
    box("c1", 590, 580, 450, "C1 corroboration  (closed-source tools)", ["At least 2 independent sources in the Google log;", "own website does not count; a competitor's comparison", "post does count", "LangSmith 13, Braintrust 5, Galileo 3, W&B Weave 2"], "google", "4 pass")
    arrow("merge", "s1", "42"); arrow("s1", "c2"); arrow("s1", "c1")
    box("recheck", 60, 735, 480, "E1 to E6 re-applied to tools new to the study", ["Pydantic Logfire: out (E6, general observability platform)", "Evidently: out (E6, general ML monitoring)  ·  Harbor: out (S1/E3, benchmark runner)", "MLflow: in, E6 exception (mlflow-tracing is an LLM-specific package", "distributed on its own)"], "rule", "Laminar, LangWatch and MLflow pass")
    arrow("c2", "recheck")
    box("res", 190, 880, 720, "Result", ["Kept: 6 open-source tools (Langfuse, Opik, Helicone, promptfoo, DeepEval, Arize Phoenix) + 4 closed-source tools = 10 tools", "Added under C2: MLflow, Laminar, LangWatch  =  13 tools (12 platforms, 1 framework)", "Standards: OpenLLMetry and OpenInference (pass C2) and OpenTelemetry (Channel 3), reported apart"], "result")
    arrow("recheck", "res"); arrow("c1", "res")
    ys = 1030
    xs = [30, 300, 570, 840]
    titles = [("S3 built-in metrics", ["Metrics the tool ships, read from", "official docs: URL, verbatim quote,", "saved page, access date"]),
              ("M1 metric scope", ["Keep how a run executes or how good", "its output is; drop text match, retrieval,", "audio, image, task-specific, custom-only"]),
              ("Collected 2026-11-09", ["33 built-in rows for the three added", "tools (MLflow 16, LangWatch 13,", "Laminar 4); one new metric: Fluency"]),
              ("Mapping to unique metrics", ["Hand-made, one row per pair:", "46 unique metrics (18 + 28) and 1", "that only standards document"])]
    for i, (tt, ls) in enumerate(titles):
        box(f"m{i}", xs[i], ys, 240, tt, ls, "metric")
    arrow("res", "m0")
    for i in range(3):
        arrow(f"m{i}", f"m{i + 1}", side="right")
    height = ys + 110
    for x0, key, text in ((30, "adopt", "new rule (C2)"), (230, "google", "depends on Google source counts (C1)"), (560, "rule", "other rule (I1, E1 to E6, S1, S2, A1, M1)")):
        out.append(f'<rect x="{x0}" y="{height - 6}" width="22" height="12" rx="3" fill="{STYLE[key][0]}" stroke="{STYLE[key][1]}" stroke-width="{2.2 if key != "rule" else 1.4}"/>')
        note(x0 + 30, height + 4, [text])
    height += 30
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-family="{FONT}" role="img" aria-label="Flow diagram of the tool selection strategy from 2026-11-09"><rect width="{W}" height="{height}" fill="#ffffff"/>'
    target = ROOT / "results" / "selection_flow_new.svg"
    target.write_text(head + "\n".join(out) + "</svg>", encoding="utf-8")
    print(f"wrote {target}: {W}x{height}")


def draw_simple():
    reset()
    out.append(f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>')
    out.append(f'<text x="30" y="36" font-size="22" font-family="Georgia,serif" fill="{INK}">How the tools were found and selected</text>')
    out.append(f'<text x="30" y="58" font-size="12.5" fill="{MUTED}">Open-source tools are chosen by adoption on GitHub and package registries; closed-source tools by how often independent sources name them.</text>')

    box("gh", 60, 90, 470, "GitHub search  (open-source tools)", ["17 queries; at least 1,000 stars, not archived,", "active in the last 6 months", "182 repositories, 37 kept after a manual check"], "channel")
    box("go", 570, 90, 470, "Google search  (closed-source tools, and discovery)", ["6 queries, first 30 results each", "68 tools named", "5 closed-source tools kept (two independent sources)"], "channel")
    box("cand", 300, 245, 500, "42 candidate tools", ["duplicates merged: an SDK and its platform count as one"], "rule")
    arrow("gh", "cand", "37", tx=0.3, label_at=(303, 222)); arrow("go", "cand", "5", tx=0.7, label_at=(813, 222))
    box("screen", 300, 345, 500, "Screening", ["purpose: observability or evaluation of LLM apps or agents (I1, S1)", "exclusions: gateways, agent frameworks, benchmarks, general-purpose platforms (E1 to E6)", "agent relevance: official docs cover agents, tool calls or traces (A1)"], "rule", "30 tools")
    arrow("cand", "screen", "42")
    box("c2", 60, 505, 470, "Open source: adoption (C2)", ["at least 5,000 stars or 1M downloads in 30 days", "(PyPI or npm), and at least 100k downloads", "when a package exists; active in 6 months"], "adopt", "25 checked  →  9 tools + 2 standards")
    box("c1", 570, 505, 470, "Closed source: corroboration (C1)", ["at least 2 independent Google sources;", "the tool's own website does not count"], "google", "4 checked  →  4 tools")
    arrow("screen", "c2"); arrow("screen", "c1")
    box("res", 250, 655, 600, "13 tools  +  3 standards", ["12 platforms and 1 framework; the standards (OpenTelemetry, OpenLLMetry,", "OpenInference) are the layer beneath the tools and are reported apart"], "result")
    arrow("c2", "res"); arrow("c1", "res")
    box("met", 250, 775, 600, "46 unique metrics", ["built-in metrics read from official docs (264 rows, each with URL and verbatim quote),", "scoped by M1 and merged by property: 18 Observability + 28 Evaluation"], "metric")
    arrow("res", "met")
    height = 775 + 90
    for x0, key, text in ((60, "adopt", "adoption rule (C2)"), (290, "google", "depends on Google source counts (C1)"), (620, "rule", "other rule")):
        out.append(f'<rect x="{x0}" y="{height - 6}" width="22" height="12" rx="3" fill="{STYLE[key][0]}" stroke="{STYLE[key][1]}" stroke-width="{2.2 if key != "rule" else 1.4}"/>')
        note(x0 + 30, height + 4, [text])
    height += 30
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" font-family="{FONT}" role="img" aria-label="Simplified flow diagram of the tool selection"><rect width="{W}" height="{height}" fill="#ffffff"/>'
    target = ROOT / "results" / "selection_flow_simple.svg"
    target.write_text(head + "\n".join(out) + "</svg>", encoding="utf-8")
    print(f"wrote {target}: {W}x{height}")


def main():
    draw_current()
    draw_new()
    draw_simple()


if __name__ == "__main__":
    main()
