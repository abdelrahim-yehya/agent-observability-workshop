#!/usr/bin/env python3
"""Write the paper's table of metrics reported in the example run (replaces the metrics_measured figure).

    python3 export_measured_table.py results/turns_<tag>.json

Same rows and cells as plot_measured.py (only the metrics the three tools actually reported, grouped by who
produced the value), written as a booktabs tabular to ../paper/tables/example_metrics.tex. The paper wraps it in
a table* environment and adds the caption.
"""
import csv
import json
import os
import re
import sys

from plot_matrix import COLS, REPO, eval_cells, langfuse_cells

OUT = os.path.join(REPO, "paper", "tables", "example_metrics.tex")


def tex(s):
    """Escape the few characters the cell texts use that LaTeX treats specially."""
    return s.replace("$", r"\$").replace("%", r"\%").replace(" · ", "; ").replace("·", ";")


def main(turns_path):
    d = json.load(open(turns_path))
    turns = d["turns"]
    tax = list(csv.DictReader(open(f"{REPO}/results/metric_taxonomy.csv")))
    mapping = {(r["tool"], r["metric_name"]): r["taxonomy_metric"]
               for r in csv.DictReader(open(f"{REPO}/data/inputs/taxonomy_mapping.csv"))}
    lf = langfuse_cells(turns)
    ev = eval_cells(turns_path.replace("turns_", "eval_").replace(".json", ".csv"), mapping)
    assert ev is not None, "evaluation CSV not found"
    for cols in ev.values():
        for c, t in cols.items():
            cols[c] = re.sub(r"mean (\d\.\d\d) over (\d+) \(\w+\)", r"mean \1 (n=\2)", t)

    rows = []
    for r in tax:
        m = r["metric"]
        cells = {}
        if m in lf:
            cells["Langfuse"] = lf[m]
        for c in ("Phoenix evals", "DeepEval"):
            if m in ev and c in ev[m]:
                cells[c] = ev[m][c]
        if cells:
            rows.append(("Recorded by the tracer", m, cells) if "Langfuse" in cells else ("Scored by the evaluators", m, cells))
    rows.sort(key=lambda x: x[0] != "Recorded by the tracer")

    o = [r"\begin{tabular}{@{}lp{1.9in}p{1.55in}p{1.55in}@{}}", r"\toprule",
         "Metric & " + " & ".join(COLS) + r" \\", r"\midrule"]
    last = None
    for g, m, cells in rows:
        if g != last:
            if last is not None:
                o.append(r"\addlinespace[2pt]")
            o.append(r"\multicolumn{4}{@{}l}{\textit{" + g + r"}} \\")
            last = g
        o.append(r"\quad " + tex(m) + " & " + " & ".join(tex(cells.get(c, "--")) for c in COLS) + r" \\")
    o += [r"\bottomrule", r"\end{tabular}"]
    open(OUT, "w", encoding="utf-8").write("\n".join(o) + "\n")
    print(f"{OUT}: {len(rows)} rows")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main(sys.argv[1])
