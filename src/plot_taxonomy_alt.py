#!/usr/bin/env python3
"""Draw two alternative tool-free views of the metric taxonomy.

Input:   results/metric_taxonomy.csv   (from build_taxonomy.py)
Output:  results/metric_taxonomy_cards.svg    landscape cards, one panel per type
         results/metric_taxonomy_radial.svg   radial tree (sunburst-style)
Run:     python3 src/plot_taxonomy_alt.py
Neither view shows tools or tool counts. The default tree with tool pips is src/plot_taxonomy.py.
"""
import csv
import math
from html import escape

from paths import ROOT

RESULTS = ROOT / "results"
NOTES = {"Observability": "what happened, measured from the run", "Evaluation": "how good it was, judged"}
STYLE = """<style>
:root{--bg:#fbfaf8;--fg:#1d2328;--muted:#5d666d;--line:#c9c5bc;--panel:#ffffff;--obs:#1f6f8b;--ev:#b4582a}
@media (prefers-color-scheme:dark){:root{--bg:#14181b;--fg:#e8ebec;--muted:#98a1a7;--line:#3a444b;--panel:#1a1f23;--obs:#5cb3d1;--ev:#e08a58}}
text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:var(--fg)}
.bg{fill:var(--bg)}.mut{fill:var(--muted)}.white{fill:#fff}
.t-Observability{--c:var(--obs)}.t-Evaluation{--c:var(--ev)}
.solid{fill:var(--c)}.tint{fill:var(--c);fill-opacity:.16}.wash{fill:var(--c);fill-opacity:.06}
.card{fill:var(--panel);stroke:var(--c);stroke-width:1.4}.dot{fill:var(--c)}.rule{stroke:var(--c);stroke-opacity:.35;stroke-width:1}
</style>"""


def read_taxonomy():
    with open(RESULTS / "metric_taxonomy.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    types = {}
    for r in rows:
        types.setdefault(r["type"], {}).setdefault(r["category"], []).append(r["metric"])
    return rows, types


def cards(rows, types):
    W, M, GAP, PAD = 1400, 32, 32, 14
    PW = (W - 2 * M - GAP) / 2
    CW = (PW - 3 * PAD) / 2
    HEAD, ROW, TOPY = 66, 21, 96

    def card_h(n):
        return 46 + n * ROW + 8

    panels = []
    for t, cs in types.items():
        items = list(cs.items())
        heights = [card_h(len(ms)) + 12 for _, ms in items]
        total, run, split, best = sum(heights), 0, 1, None
        for i, h in enumerate(heights[:-1], 1):  # split in reading order so both columns are about as tall
            run += h
            d = abs(total / 2 - run)
            if best is None or d < best:
                best, split = d, i
        cols = [items[:split], items[split:]]
        col_h = [sum(card_h(len(ms)) + 12 for _, ms in c) for c in cols]
        panels.append((t, cols, max(col_h)))
    body = max(p[2] for p in panels)
    H = TOPY + HEAD + PAD + body + 44

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Taxonomy of agent metrics">',
           STYLE, f'<rect class="bg" width="{W}" height="{H}"/>',
           f'<text x="{M}" y="40" font-size="22" font-family="Georgia,serif">Taxonomy of agent metrics</text>',
           f'<text class="mut" x="{M}" y="64" font-size="13">{len(rows)} metrics in {sum(len(c) for c in types.values())} categories, in two types: '
           f'observability metrics are measured from a run, evaluation metrics are judgements of behaviour or output.</text>']
    for k, (t, cols, _) in enumerate(panels):
        px = M + k * (PW + GAP)
        n_t = sum(len(ms) for c in cols for _, ms in c)
        out.append(f'<g class="t-{t}"><rect class="wash" x="{px}" y="{TOPY}" width="{PW}" height="{HEAD + PAD + body}" rx="12"/>'
                   f'<rect class="solid" x="{px}" y="{TOPY}" width="{PW}" height="{HEAD}" rx="12"/>'
                   f'<rect class="solid" x="{px}" y="{TOPY + HEAD - 12}" width="{PW}" height="12"/>'
                   f'<text class="white" x="{px + 20}" y="{TOPY + 30}" font-size="21" font-weight="700">{t}</text>'
                   f'<text class="white" x="{px + 20}" y="{TOPY + 51}" font-size="12.5" fill-opacity=".9">{NOTES[t]}</text>'
                   f'<text class="white" x="{px + PW - 20}" y="{TOPY + 42}" font-size="15" font-weight="600" text-anchor="end">{n_t} metrics</text></g>')
        for ci, col in enumerate(cols):
            x = px + PAD + ci * (CW + PAD)
            y = TOPY + HEAD + PAD
            for cat, ms in col:
                h = card_h(len(ms))
                out.append(f'<g class="t-{t}"><rect class="card" x="{x}" y="{y}" width="{CW}" height="{h}" rx="9"/>'
                           f'<text x="{x + 14}" y="{y + 26}" font-size="14" font-weight="700">{escape(cat)}</text>'
                           f'<text class="mut" x="{x + CW - 14}" y="{y + 26}" font-size="12" text-anchor="end">{len(ms)}</text>'
                           f'<line class="rule" x1="{x + 14}" y1="{y + 36}" x2="{x + CW - 14}" y2="{y + 36}"/>')
                for i, m in enumerate(ms):
                    ly = y + 56 + i * ROW
                    out.append(f'<circle class="dot" cx="{x + 18}" cy="{ly - 4}" r="3.2"/><text x="{x + 30}" y="{ly}" font-size="12.5">{escape(m)}</text>')
                out.append("</g>")
                y += h + 12
    out.append(f'<text class="mut" x="{M}" y="{H - 16}" font-size="11.5">Source: results/metric_taxonomy.csv.</text></svg>')
    return "\n".join(out), W, H


def radial(rows, types):
    R, R_HOLE, R_TYPE, R_CAT, R_BAR, R_LABEL = 540, 64, 132, 250, 258, 270
    GAP_T, GAP_C = 7.0, 1.6
    n_cats = sum(len(c) for c in types.values())
    slot = (360 - len(types) * GAP_T - (n_cats - len(types)) * GAP_C) / len(rows)
    cx = cy = R

    def pt(r, a):
        a = math.radians(a)
        return cx + r * math.sin(a), cy - r * math.cos(a)

    def sector(r0, r1, a0, a1):
        large = 1 if a1 - a0 > 180 else 0
        x0, y0, x1, y1 = *pt(r1, a0), *pt(r1, a1)
        x2, y2, x3, y3 = *pt(r0, a1), *pt(r0, a0)
        return f"M{x0:.1f},{y0:.1f} A{r1},{r1} 0 {large} 1 {x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f} A{r0},{r0} 0 {large} 0 {x3:.1f},{y3:.1f} Z"

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {2 * R} {2 * R}" width="{2 * R}" height="{2 * R}" role="img" aria-label="Radial taxonomy of agent metrics">',
           STYLE, f'<rect class="bg" width="{2 * R}" height="{2 * R}"/>',
           '<text x="28" y="44" font-size="22" font-family="Georgia,serif">Taxonomy of agent metrics</text>',
           f'<text class="mut" x="28" y="66" font-size="13">{len(rows)} metrics in {n_cats} categories.</text>',
           '<text class="mut" x="28" y="84" font-size="13">Observability: measured from a run.</text>',
           '<text class="mut" x="28" y="102" font-size="13">Evaluation: judged behaviour or output.</text>']
    a = GAP_T / 2
    defs, body = [], []
    for ti, (t, cs) in enumerate(types.items()):
        t_start = a
        for cat, ms in cs.items():
            c0 = a
            for m in ms:
                m0, m1 = a, a + slot
                mid = (m0 + m1) / 2
                body.append(f'<path class="solid t-{t}" d="{sector(R_CAT + 2, R_BAR, m0 + .35, m1 - .35)}"/>')
                x, y = pt(R_LABEL, mid)
                flip = mid > 180
                rot, anchor = (mid + 90, "end") if flip else (mid - 90, "start")
                body.append(f'<text transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})" text-anchor="{anchor}" dy="4.3" font-size="12.5">{escape(m)}</text>')
                a = m1
            c1 = a
            body.append(f'<path class="tint t-{t}" d="{sector(R_TYPE + 3, R_CAT, c0, c1)}"/>')
            cm = (c0 + c1) / 2
            x, y = pt((R_TYPE + R_CAT) / 2 + 2, cm)
            flip = cm > 180
            rot = cm + 90 if flip else cm - 90
            body.append(f'<text transform="translate({x:.1f},{y:.1f}) rotate({rot:.2f})" text-anchor="middle" dy="4" font-size="12" font-weight="700">{escape(cat)}</text>')
            a += GAP_C
        a -= GAP_C
        t_end = a
        body.append(f'<path class="solid t-{t}" d="{sector(R_HOLE + 6, R_TYPE, t_start, t_end)}"/>')
        # type name on an arc, reversed on the lower half so it reads left to right
        r_mid, tm = (R_HOLE + 6 + R_TYPE) / 2, (t_start + t_end) / 2
        lower = 90 < tm < 270
        s0, s1 = (t_end, t_start) if lower else (t_start, t_end)
        x0, y0, x1, y1 = *pt(r_mid, s0), *pt(r_mid, s1)
        large = 1 if t_end - t_start > 180 else 0
        defs.append(f'<path id="arc{ti}" fill="none" d="M{x0:.1f},{y0:.1f} A{r_mid},{r_mid} 0 {large} {0 if lower else 1} {x1:.1f},{y1:.1f}"/>')
        n_t = sum(len(ms) for ms in cs.values())
        body.append(f'<text class="white" font-size="17" font-weight="700" dy="{-4 if lower else 6}"><textPath href="#arc{ti}" startOffset="50%" text-anchor="middle">{t} · {n_t}</textPath></text>')
        a += GAP_T
    out.append("<defs>" + "".join(defs) + "</defs>")
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R_HOLE}" fill="none" stroke="var(--line)" stroke-width="1.5"/>')
    out.append(f'<text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="15" font-weight="700">Agent</text>'
               f'<text x="{cx}" y="{cy + 16}" text-anchor="middle" font-size="15" font-weight="700">metrics</text>')
    out.extend(body)
    out.append(f'<text class="mut" x="{2 * R - 28}" y="{2 * R - 20}" text-anchor="end" font-size="11.5">Source: results/metric_taxonomy.csv.</text></svg>')
    return "\n".join(out), 2 * R, 2 * R


def main():
    rows, types = read_taxonomy()
    for name, fn in (("metric_taxonomy_cards", cards), ("metric_taxonomy_radial", radial)):
        svg, w, h = fn(rows, types)
        (RESULTS / f"{name}.svg").write_text(svg, encoding="utf-8")
        print(f"wrote results/{name}.svg ({w}x{h})")


if __name__ == "__main__":
    main()
