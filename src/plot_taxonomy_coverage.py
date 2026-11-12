#!/usr/bin/env python3
"""Draw results/metric_taxonomy_coverage.svg: the paper's Fig. 3, the taxonomy against the tools that document each metric.

Two panels (Observability, Evaluation). Rows are the unique metrics grouped by category; columns are the studied
tools grouped by role (Platform, Framework). Standards (OpenTelemetry, OpenLLMetry, OpenInference) are the layer
beneath the tools and are not columns. A dot means the tool documents the metric as built-in. The "Tools" column
and the dagger count only the tools shown (a dagger marks a metric documented as built-in by one shown tool only).

Input:   results/tool_metric_matrix.csv   (from build_matrix.py; status per tool and metric)
         results/best_tools.csv           (roles and rank order)
Output:  results/metric_taxonomy_coverage.svg   (fixed light colours, print size 512.64 x 369 pt)
PDF:     wrap the SVG in an HTML page with  @page{size:512.64pt 369pt;margin:0}  and print it with
         "Brave Browser" --headless --print-to-pdf=paper/figures/metric_taxonomy_coverage.pdf --no-pdf-header-footer page.html
Run:     python3 src/build_matrix.py && python3 src/plot_taxonomy_coverage.py
"""
import csv
from html import escape

from build_tool_table import grouped
from paths import ROOT

RESULTS = ROOT / "results"
W, H = 512.64, 369.0
PANEL_W, GAP = 250.0, 12.64
P = 7.77  # row pitch (pt)
COL = {"Observability": "#1f6f8b", "Evaluation": "#b4582a"}
MUTED, INK, DOT_OFF = "#5d666d", "#1d2328", "#c9c5bc"
FONT = "Helvetica, Arial, 'Liberation Sans', sans-serif"
GROUPS = ["platform", "framework"]  # role -> column group, in this order; "standard" is left out on purpose
GROUP_LABEL = {"platform": "Platform", "framework": "Framework"}
SHORT = {"Weights & Biases Weave": "W&B Weave"}  # the DeepEval column is DeepEval plus its Confident AI platform (E5); the paper caption says so
X_DOT0, PITCH, GROUP_GAP, X_COUNT = 126.0, 8.4, 9.0, 246.0
Y_HEAD = 72.0


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    # same order as the paper's tools table (open-source tools by downloads, then closed-source tools), split by role
    ordered = [(t, b["role"]) for g in ("Open-source tools", "Closed-source tools") for t, b, *_ in grouped()[g]]
    tools = sorted((x for x in ordered if x[1] in GROUPS), key=lambda t: GROUPS.index(t[1]))  # stable: keeps table order inside a role
    matrix = read(RESULTS / "tool_metric_matrix.csv")

    xs, x = {}, X_DOT0
    for i, (t, role) in enumerate(tools):
        if i and role != tools[i - 1][1]:
            x += GROUP_GAP
        xs[t] = x
        x += PITCH
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}pt" height="{H}pt" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']

    def text(x, y, s, size, fill=INK, weight="normal", anchor="start", extra=""):
        return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}"{extra}>{s}</text>'

    legend_y = None
    for k, typ in enumerate(("Observability", "Evaluation")):
        ox, color = k * (PANEL_W + GAP), COL[typ]
        rows = [r for r in matrix if r["type"] == typ]
        cats = {}
        for r in rows:
            cats.setdefault(r["category"], []).append(r)
        out.append(text(ox, 43, typ, 9, color, "bold"))
        out.append(text(ox, 54.6, f"{len(rows)} metrics in {len(cats)} categories", 5.5, MUTED))
        # column headers and role brackets
        for t, role in tools:
            out.append(f'<text transform="translate({ox + xs[t] + 1.8:.2f},59.5) rotate(-90)" font-size="5.5" fill="{INK}">{escape(SHORT.get(t, t))}</text>')
        out.append(f'<text transform="translate({ox + X_COUNT + 1.8:.2f},59.5) rotate(-90)" font-size="5.5" fill="{INK}">Tools</text>')
        for role in GROUPS:
            cols = [xs[t] for t, r in tools if r == role]
            n = len(cols)
            out.append(f'<line x1="{ox + cols[0] - 4:.2f}" y1="16" x2="{ox + cols[-1] + 4:.2f}" y2="16" stroke="{MUTED}" stroke-width="0.7"/>')
            out.append(text(ox + min((cols[0] + cols[-1]) / 2, PANEL_W - 22), 11.5, f"{GROUP_LABEL[role]} ({n})", 5.5, MUTED, anchor="middle"))  # keep the label inside the panel
        y = Y_HEAD
        for cat, ms in cats.items():
            out.append(f'<text x="{ox:.2f}" y="{y + 2.2:.2f}" font-size="6.5" font-weight="bold" fill="{color}">{escape(cat)}'
                       f'<tspan dx="3.5" font-size="5.5" font-weight="normal" fill="{MUTED}">{len(ms)}</tspan></text>')
            out.append(f'<line x1="{ox:.2f}" y1="{y + 0.56 * P:.2f}" x2="{ox + PANEL_W:.2f}" y2="{y + 0.56 * P:.2f}" stroke="{color}" stroke-opacity="0.5" stroke-width="0.9"/>')
            for i, m in enumerate(ms, 1):
                ry = y + i * P
                built = [t for t, _ in tools if m[t] == "built-in"]
                dagger = "†" if len(built) == 1 else ""
                out.append(text(ox + 5, ry + 2, escape(m["metric"].replace(" / ", "/")) + dagger, 5.5))
                for t, _ in tools:
                    if m[t] == "built-in":
                        out.append(f'<circle cx="{ox + xs[t]:.2f}" cy="{ry:.2f}" r="1.5" fill="{color}"/>')
                    else:
                        out.append(f'<circle cx="{ox + xs[t]:.2f}" cy="{ry:.2f}" r="0.55" fill="{DOT_OFF}"/>')
                out.append(text(ox + X_COUNT, ry + 2, str(len(built)), 5.5, INK, anchor="end"))
            y += len(ms) * P + 1.42 * P
        if typ == "Observability":
            legend_y = 298.7
            n_tools = len(tools)
            out.append(f'<circle cx="7" cy="{legend_y}" r="1.5" fill="{COL["Observability"]}"/><circle cx="14" cy="{legend_y}" r="1.5" fill="{COL["Evaluation"]}"/>')
            items = ["documented as built-in", "not documented as built-in (other status or none)", "documented as built-in by one tool only",
                     f"Tools: number of the {n_tools} tools shown that document the metric as built-in", "The number after a category is its number of metrics"]
            for j, s in enumerate(items):
                yy = legend_y + j * 10.8
                if j == 1:
                    out.append(f'<circle cx="10.5" cy="{yy}" r="0.55" fill="{DOT_OFF}"/>')
                if j == 2:
                    out.append(text(7, yy + 2, "†", 5.5, INK, anchor="middle"))
                out.append(text(22, yy + 2, escape(s), 5.5))
            assert y - 1.42 * P < legend_y - 5, "legend would overlap the Observability rows"
        else:
            assert y - 1.42 * P < H - 6, "Evaluation rows would run off the figure"
    out.append("</svg>")
    target = RESULTS / "metric_taxonomy_coverage.svg"
    target.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {target}: {len(matrix)} metrics x {len(tools)} tools")


if __name__ == "__main__":
    main()
