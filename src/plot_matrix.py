#!/usr/bin/env python3
"""Draw results/tool_metric_matrix.html: a static heatmap of the tool x metric matrix.

Input:   results/tool_metric_matrix_long.csv   (from build_matrix.py)
Output:  results/tool_metric_matrix.html       (one self-contained file, no scripts)
Run:     python3 src/build_matrix.py && python3 src/plot_matrix.py
"""
import csv
from html import escape

from paths import ROOT

RESULTS = ROOT / "results"
STATUS = [  # status, glyph, label, meaning
    ("built-in", "B", "Built-in", "A documented built-in metric"),
    ("integration", "I", "Integration", "Only through a third-party library the tool wraps"),
    ("community", "C", "Community", "A community-contributed metric in the docs"),
    ("template", "T", "Template", "A copy-and-run example, not a shipped metric"),
    ("generic custom", "G", "Generic custom", "No specific metric, but the tool documents a way to write your own evaluator"),
    ("records scores", "R", "Records scores", "Stores scores produced elsewhere; no evaluator of its own"),
    ("not documented", "·", "Not documented", "Nothing found in the pages read; not proof the tool lacks it"),
]
BY = {s[0]: s for s in STATUS}
cls = lambda status: "s-" + status.replace(" ", "-")

CSS = """
:root{--bg:#fbfaf8;--fg:#1d2328;--muted:#5d666d;--line:#dcd9d2;--panel:#ffffff;--accent:#1f6f8b;--on-accent:#ffffff}
@media (prefers-color-scheme:dark){:root{--bg:#14181b;--fg:#e8ebec;--muted:#98a1a7;--line:#2c343a;--panel:#1a1f23;--accent:#5cb3d1;--on-accent:#0d1316}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:2rem max(1rem,4vw)}
h1{font:400 1.7rem/1.2 Georgia,"Times New Roman",serif;margin:0 0 .4rem}
.lead{margin:0 0 1.2rem;color:var(--muted);max-width:68ch}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:1.2rem;max-width:80rem}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));gap:.45rem 1.4rem;margin:0 0 1.2rem;padding:0;list-style:none;font-size:.82rem;color:var(--muted)}
.legend li{display:flex;gap:.5rem;align-items:flex-start}
.sw{flex:none;display:inline-grid;place-items:center;width:1.3rem;height:1.3rem;border-radius:3px;font-size:.7rem;font-weight:600}
.legend b{color:var(--fg);font-weight:600}
.scroll{overflow-x:auto}
table{border-collapse:separate;border-spacing:2px;min-width:max-content}
th,td{padding:0;font-weight:400}
.corner{vertical-align:bottom;text-align:left;font-size:.78rem;color:var(--muted);padding-right:.8rem}
.hd{height:12rem;vertical-align:bottom;text-align:center}
.hd div{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:.3rem;height:100%}
.hd .vt{writing-mode:vertical-rl;transform:rotate(180deg);font-size:.78rem;white-space:nowrap}
.hd .n{font-size:.78rem;font-weight:600;font-variant-numeric:tabular-nums}
.hd .bar{width:.5rem;background:var(--accent);border-radius:2px 2px 0 0}
.last{vertical-align:bottom;text-align:left;font-size:.78rem;color:var(--muted);padding-left:.5rem}
.grp th{text-align:left;padding:.9rem 0 .2rem;border-bottom:1px solid var(--line);font-size:.78rem;color:var(--muted)}
.grp b{color:var(--fg);font-weight:600;margin-right:.5rem}
.lbl{text-align:left;font-size:.8rem;padding-right:.8rem;min-width:11rem;white-space:nowrap}
.c{width:2.4rem;height:1.7rem;border-radius:3px;text-align:center;font-size:.7rem;font-weight:600}
.s-built-in{background:var(--accent);color:var(--on-accent)}
.s-integration{background:color-mix(in srgb,var(--accent) 60%,var(--panel))}
.s-community{background:color-mix(in srgb,var(--accent) 45%,var(--panel))}
.s-template{background:color-mix(in srgb,var(--accent) 32%,var(--panel))}
.s-generic-custom,.s-records-scores{background:color-mix(in srgb,var(--accent) 12%,var(--panel));color:var(--muted)}
.s-not-documented{background:transparent;color:var(--muted);outline:1px dashed var(--line);outline-offset:-1px}
.rb{display:flex;align-items:center;gap:.4rem;padding-left:.5rem;font-size:.78rem;font-variant-numeric:tabular-nums}
.rb .tr{flex:none;width:4.5rem;height:.5rem;background:color-mix(in srgb,var(--fg) 8%,transparent);border-radius:2px}
.rb .tr i{display:block;height:100%;background:var(--accent);border-radius:2px}
.note{margin:1rem 0 0;font-size:.78rem;color:var(--muted);max-width:75ch}
"""


def main():
    with open(RESULTS / "tool_metric_matrix_long.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    tools, metrics, cell = [], [], {}
    for r in rows:
        if r["tool"] not in tools:
            tools.append(r["tool"])
        if not any(m["metric"] == r["metric"] for m in metrics):
            metrics.append(r)
        cell[(r["tool"], r["metric"])] = r
    per_tool = {t: sum(cell[(t, m["metric"])]["status"] == "built-in" for m in metrics) for t in tools}
    per_metric = {m["metric"]: sum(cell[(t, m["metric"])]["status"] == "built-in" for t in tools) for m in metrics}
    max_tool = max(per_tool.values())
    best_tool = max(tools, key=lambda t: per_tool[t])
    best_metric = max(metrics, key=lambda m: per_metric[m["metric"]])["metric"]

    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>Agent Metrics Matrix</title><style>" + CSS + "</style></head><body>",
           "<h1>Agent metrics by tool</h1>",
           f'<p class="lead">Each cell shows whether a tool documents a metric as built-in. {escape(best_tool)} documents the most built-in metrics '
           f"({per_tool[best_tool]} of {len(metrics)}); {escape(best_metric)} is the metric most tools ship built-in ({per_metric[best_metric]} of {len(tools)} tools).</p>",
           '<div class="card"><ul class="legend">']
    for status, glyph, label, meaning in STATUS:
        out.append(f'<li><span class="sw {cls(status)}">{glyph}</span><span><b>{label}</b>: {escape(meaning)}</span></li>')
    out.append('</ul><div class="scroll"><table><thead><tr><th class="corner">Built-in metrics per tool</th>')
    for t in tools:
        h = round(22 * per_tool[t] / max_tool)
        out.append(f'<th class="hd"><div><span class="bar" style="height:{h}px"></span><span class="n">{per_tool[t]}</span><span class="vt">{escape(t)}</span></div></th>')
    out.append('<th class="last">Tools with it built-in</th></tr></thead><tbody>')
    last = None
    for m in metrics:
        g = (m["type"], m["category"])
        if g != last:
            last = g
            out.append(f'<tr class="grp"><th colspan="{len(tools) + 2}"><b>{escape(m["category"])}</b>{escape(m["type"])}</th></tr>')
        out.append(f'<tr><th class="lbl" scope="row">{escape(m["metric"])}</th>')
        for t in tools:
            r = cell[(t, m["metric"])]
            s = BY[r["status"]]
            tip = f'{m["metric"]} / {t}: {s[2]}'
            if r["tool_specific_names"]:
                tip += f' (called: {r["tool_specific_names"]})'
            out.append(f'<td class="c {cls(s[0])}" title="{escape(tip, quote=True)}">{s[1]}</td>')
        n = per_metric[m["metric"]]
        out.append(f'<td><div class="rb"><span class="tr"><i style="width:{round(100 * n / len(tools))}%"></i></span>{n}</div></td></tr>')
    out.append("</tbody></table></div>")
    out.append('<p class="note">A dashed cell means nothing was found in the documentation pages read. That is not proof the tool lacks the metric. '
               "Counts are documentation entries, not capability scores: some documentation lists many narrow metrics, other documentation a few broad ones. "
               "Source: results/tool_metric_matrix_long.csv, built by src/build_matrix.py.</p></div></body></html>")
    (RESULTS / "tool_metric_matrix.html").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {RESULTS / 'tool_metric_matrix.html'}: {len(metrics)} metrics x {len(tools)} tools")


if __name__ == "__main__":
    main()
