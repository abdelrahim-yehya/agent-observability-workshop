#!/usr/bin/env python3
"""Draw results/metric_taxonomy_diagram.svg: the metric taxonomy as a left-to-right tree.

Input:   results/metric_taxonomy.csv    (from build_taxonomy.py)
         results/best_tools.csv         (number of tools, for the pip scale)
Output:  results/metric_taxonomy_diagram.svg   (self-contained, light and dark themes)
Run:     python3 src/build_taxonomy.py && python3 src/plot_taxonomy.py
Each metric shows one pip per tool that documents it as built-in; a dagger marks a metric only one tool provides.
"""
import csv
from html import escape

from paths import ROOT

RESULTS = ROOT / "results"
ROW, GAP, TOP, LEFT = 21, 12, 78, 24
X_ROOT, W_ROOT = LEFT, 104
X_TYPE, W_TYPE = 176, 148
X_CAT, W_CAT = 372, 192
X_LEAF = 640
X_PIPS, PIP = 928, 10
CAT_H, TYPE_H = 40, 64


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = read(RESULTS / "metric_taxonomy.csv")
    n_tools_total = len(read(RESULTS / "best_tools.csv"))
    types = {}
    for r in rows:
        types.setdefault(r["type"], {}).setdefault(r["category"], []).append(r)

    y = TOP
    cats = []  # (type, category, metrics, block_top, block_h)
    for t, cs in types.items():
        for c, ms in cs.items():
            h = max(CAT_H, len(ms) * ROW)
            cats.append((t, c, ms, y, h))
            y += h + GAP
    height = y + 56
    width = X_PIPS + n_tools_total * PIP + 60

    def mid(top, h):
        return top + h / 2

    def curve(x1, y1, x2, y2):
        xm = (x1 + x2) / 2
        return f"M{x1},{y1} C{xm},{y1} {xm},{y2} {x2},{y2}"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="Taxonomy of agent observability and evaluation metrics">',
        "<style>",
        ":root{--bg:#fbfaf8;--fg:#1d2328;--muted:#5d666d;--line:#c9c5bc;--panel:#ffffff;--obs:#1f6f8b;--ev:#b4582a;--empty:#d9d6cf}",
        "@media (prefers-color-scheme:dark){:root{--bg:#14181b;--fg:#e8ebec;--muted:#98a1a7;--line:#3a444b;--panel:#1a1f23;--obs:#5cb3d1;--ev:#e08a58;--empty:#343c42}}",
        "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:var(--fg)}",
        ".bg{fill:var(--bg)}.mut{fill:var(--muted)}.ln{fill:none;stroke:var(--line);stroke-width:1.4}",
        ".box{fill:var(--panel);stroke-width:1.6}.t-Observability .box,.t-Observability .fillc{stroke:var(--obs)}.t-Evaluation .box,.t-Evaluation .fillc{stroke:var(--ev)}",
        ".t-Observability .on{fill:var(--obs)}.t-Evaluation .on{fill:var(--ev)}.off{fill:var(--empty)}",
        ".typebox{stroke-width:0}.t-Observability .typebox{fill:var(--obs)}.t-Evaluation .typebox{fill:var(--ev)}",
        ".white{fill:#fff}.cap{font-size:11px;letter-spacing:.06em;text-transform:uppercase}",
        "</style>",
        f'<rect class="bg" width="{width}" height="{height}"/>',
        f'<text x="{LEFT}" y="30" font-size="20" font-family="Georgia,serif">Taxonomy of agent metrics</text>',
        f'<text class="mut" x="{LEFT}" y="50" font-size="12.5">{len(rows)} metrics in {len(cats)} categories, built from the documentation of {n_tools_total} tools. Only metrics the tools document as built-in are included.</text>',
    ]
    for x, label in ((X_ROOT, "Agent metrics"), (X_TYPE, "Type"), (X_CAT, "Category"), (X_LEAF, "Metric"), (X_PIPS, f"Built-in in (of {n_tools_total} tools)")):
        out.append(f'<text class="mut cap" x="{x}" y="{TOP - 14}" font-size="11">{escape(label)}</text>')

    # connectors first so boxes sit on top
    type_centers, cat_centers = {}, []
    for t, c, ms, top, h in cats:
        cat_centers.append((t, mid(top, h)))
    for t in types:
        ys = [cy for tt, cy in cat_centers if tt == t]
        type_centers[t] = (min(ys) + max(ys)) / 2
    root_y = (min(type_centers.values()) + max(type_centers.values())) / 2
    for t, ty in type_centers.items():
        out.append(f'<path class="ln" d="{curve(X_ROOT + W_ROOT, root_y, X_TYPE, ty)}"/>')
    for t, c, ms, top, h in cats:
        cy = mid(top, h)
        out.append(f'<path class="ln" d="{curve(X_TYPE + W_TYPE, type_centers[t], X_CAT, cy)}"/>')
        first = top + (h - len(ms) * ROW) / 2 + ROW / 2
        for i, m in enumerate(ms):
            out.append(f'<path class="ln" d="{curve(X_CAT + W_CAT, cy, X_LEAF - 4, first + i * ROW)}"/>')

    out.append(f'<g><rect class="box" x="{X_ROOT}" y="{root_y - TYPE_H / 2}" width="{W_ROOT}" height="{TYPE_H}" rx="8" style="stroke:var(--fg)"/>'
               f'<text x="{X_ROOT + W_ROOT / 2}" y="{root_y - 3}" text-anchor="middle" font-size="14" font-weight="600">Agent</text>'
               f'<text x="{X_ROOT + W_ROOT / 2}" y="{root_y + 14}" text-anchor="middle" font-size="14" font-weight="600">metrics</text></g>')
    notes = {"Observability": "what happened, measured", "Evaluation": "how good, judged"}
    for t, ty in type_centers.items():
        n = sum(len(ms) for tt, cc, ms, _, _ in cats if tt == t)
        out.append(f'<g class="t-{t}"><rect class="typebox" x="{X_TYPE}" y="{ty - TYPE_H / 2}" width="{W_TYPE}" height="{TYPE_H}" rx="8"/>'
                   f'<text class="white" x="{X_TYPE + W_TYPE / 2}" y="{ty - 8}" text-anchor="middle" font-size="14" font-weight="600">{t}</text>'
                   f'<text class="white" x="{X_TYPE + W_TYPE / 2}" y="{ty + 8}" text-anchor="middle" font-size="11">{notes.get(t, "")}</text>'
                   f'<text class="white" x="{X_TYPE + W_TYPE / 2}" y="{ty + 22}" text-anchor="middle" font-size="11">{n} metrics</text></g>')
    for t, c, ms, top, h in cats:
        cy = mid(top, h)
        out.append(f'<g class="t-{t}"><rect class="box" x="{X_CAT}" y="{cy - CAT_H / 2}" width="{W_CAT}" height="{CAT_H}" rx="7"/>'
                   f'<text x="{X_CAT + 12}" y="{cy - 3}" font-size="13" font-weight="600">{escape(c)}</text>'
                   f'<text class="mut" x="{X_CAT + 12}" y="{cy + 13}" font-size="11">{len(ms)} metric{"s" if len(ms) != 1 else ""}</text></g>')
        first = top + (h - len(ms) * ROW) / 2 + ROW / 2
        for i, m in enumerate(ms):
            ly = first + i * ROW
            n = int(m["n_tools"])
            dagger = "†" if n == 1 else ""
            tip = f'{m["metric"]}: {m["definition"]} Built-in in: {m["tools"]}.'
            out.append(f'<g class="t-{t}"><title>{escape(tip)}</title><circle class="on" cx="{X_LEAF}" cy="{ly}" r="3.5"/>'
                       f'<text x="{X_LEAF + 12}" y="{ly + 4}" font-size="12.5">{escape(m["metric"])}{dagger}</text>')
            for k in range(n_tools_total):
                out.append(f'<circle class="{"on" if k < n else "off"}" cx="{X_PIPS + k * PIP + PIP / 2}" cy="{ly}" r="3.4"/>')
            out.append(f'<text class="mut" x="{X_PIPS + n_tools_total * PIP + 8}" y="{ly + 4}" font-size="11.5">{n}</text></g>')
    out.append(f'<text class="mut" x="{LEFT}" y="{height - 22}" font-size="11.5">† Documented as built-in by one tool only.   '
               f'Source: results/metric_taxonomy.csv, built from official documentation (quotes in results/built_in_metrics.csv).</text>')
    out.append("</svg>")
    (RESULTS / "metric_taxonomy_diagram.svg").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {RESULTS / 'metric_taxonomy_diagram.svg'}: {len(rows)} metrics, {len(cats)} categories, {width}x{height}")


if __name__ == "__main__":
    main()
