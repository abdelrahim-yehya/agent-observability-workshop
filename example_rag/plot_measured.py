#!/usr/bin/env python3
"""Draw results/metrics_measured_<tag>.svg: only the metrics the three tools actually reported in the run.

    python3 plot_measured.py results/turns_<tag>.json

Unlike plot_matrix.py this figure assumes the reader knows nothing about the paper's taxonomy: no types, no
categories, no unmeasured rows. Rows are grouped by who produced the value (the tracer or the evaluators).
Inputs and value computation are shared with plot_matrix.py; the picture is drawn by this script.
"""
import csv
import json
import os
import re
import sys
from html import escape

from plot_matrix import COLS, D2NAME, P2NAME, REPO, TOOL_NAME, eval_cells, langfuse_cells

CHAR = 6.3  # approximate width of one character at 13 px


def main(turns_path):
    d = json.load(open(turns_path))
    turns = d["turns"]
    tax = list(csv.DictReader(open(f"{REPO}/results/metric_taxonomy.csv")))
    mapping = {(r["tool"], r["metric_name"]): r["taxonomy_metric"]
               for r in csv.DictReader(open(f"{REPO}/data/inputs/taxonomy_mapping.csv"))}
    lf = langfuse_cells(turns)
    ev = eval_cells(turns_path.replace("turns_", "eval_").replace(".json", ".csv"), mapping)
    assert ev is not None, "evaluation CSV not found"
    # shorten for print: drop the evaluator's own name and write n compactly
    for cols in ev.values():
        for c, t in cols.items():
            cols[c] = re.sub(r"mean (\d\.\d\d) over (\d+) \(\w+\)", r"mean \1 (n=\2)", t)

    rows = []  # (group, metric, {column: text})
    for r in tax:
        m = r["metric"]
        cells = {}
        if m in lf:
            cells["Langfuse"] = lf[m]
        for c in ("Phoenix evals", "DeepEval"):
            if m in ev and c in ev[m]:
                cells[c] = ev[m][c]
        if cells:
            rows.append(("Recorded by the tracer" if "Langfuse" in cells else "Scored by the evaluators", m, cells))
    rows.sort(key=lambda x: x[0] != "Recorded by the tracer")  # stable: keeps the taxonomy order inside each group

    ROW, TOP, LEFT, FS = 21, 106, 24, 13
    w_label = int(max(len(m) for _, m, _ in rows) * CHAR) + 26
    w_cols = [int(max((len(c.get(col, "")) for _, _, c in rows), default=6) * CHAR) + 18 for col in COLS]
    x_cols = [LEFT + 12 + w_label + sum(w_cols[:i]) + 8 * i for i in range(3)]
    WIDTH = x_cols[-1] + w_cols[-1] + LEFT
    groups = list(dict.fromkeys(g for g, _, _ in rows))
    height = TOP + len(rows) * ROW + len(groups) * 26 + 40

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" role="img" '
         f'aria-label="Metrics reported by each tool in one run">',
         "<style>:root{--bg:#fbfaf8;--fg:#1d2328;--muted:#5d666d;--line:#d9d6cf;--obs:#1f6f8b;--ev:#b4582a;--obsf:#dcebf0;--evf:#f4e3d8;--empty:#efede8}",
         "@media (prefers-color-scheme:dark){:root{--bg:#14181b;--fg:#e8ebec;--muted:#98a1a7;--line:#3a444b;--obs:#5cb3d1;--ev:#e08a58;--obsf:#1f3a45;--evf:#47301f;--empty:#22282c}}",
         f"text{{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:var(--fg);font-size:{FS}px}}.mut{{fill:var(--muted)}}",
         ".cap{font-size:12px;letter-spacing:.06em}.cat{font-size:12px;font-weight:600}</style>",
         f'<rect width="{WIDTH}" height="{height}" fill="var(--bg)"/>',
         f'<text x="{LEFT}" y="30" style="font-size:20px;font-family:Georgia,serif">Metrics reported by each tool in one run</text>',
         f'<text class="mut" x="{LEFT}" y="52">{len(turns)} questions to a RAG chatbot running on {escape(d["model"])}. '
         f'A cell shows what the tool reported for that metric; a blank cell means it reported nothing.</text>',
         f'<text class="mut" x="{LEFT}" y="72">LLM judge for the evaluators: {escape(d["model"])}, not validated against human labels. '
         f'Drawn by plot_measured.py from the tools\' output.</text>']
    for i, c in enumerate(COLS):
        o.append(f'<text class="cap mut" x="{x_cols[i]}" y="{TOP - 12}">{c}</text>')
    y, last = TOP, None
    for g, m, cells in rows:
        if g != last:
            colr = "var(--obs)" if g.startswith("Recorded") else "var(--ev)"
            o.append(f'<text class="cat" x="{LEFT}" y="{y + 15}" style="fill:{colr}">{escape(g)}</text>')
            y += 26; last = g
        fillv = "var(--obsf)" if g.startswith("Recorded") else "var(--evf)"
        o.append(f'<text x="{LEFT + 10}" y="{y + 15}">{escape(m)}</text>')
        for i, c in enumerate(COLS):
            txt = cells.get(c)
            x = x_cols[i]
            if txt:
                o.append(f'<rect x="{x}" y="{y + 2}" width="{w_cols[i]}" height="{ROW - 4}" rx="3" fill="{fillv}"/>'
                         f'<text x="{x + 7}" y="{y + 15}">{escape(txt)}</text>')
            else:
                o.append(f'<rect x="{x}" y="{y + 2}" width="{w_cols[i]}" height="{ROW - 4}" rx="3" fill="var(--empty)" opacity=".5"/>')
        y += ROW
    o.append("</svg>")
    out = turns_path.replace("turns_", "metrics_measured_").replace(".json", ".svg")
    open(out, "w", encoding="utf-8").write("\n".join(o))
    print(f"{out}: {len(rows)} measured metrics, {WIDTH} x {height} px")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1])
