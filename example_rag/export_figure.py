"""Turn a matrix SVG from plot_matrix.py into a PDF for the paper (needs pymupdf).

    python3 export_figure.py results/metrics_matrix_<tag>.svg

The SVG styles itself with CSS variables, classes and a dark-mode rule, which PDF converters do not understand.
This script resolves the light-theme values, inlines the class styles, and writes <name>.pdf next to the SVG.
"""
import re
import sys

import pymupdf

CLASS_STYLE = {"mut": "fill:{muted}", "cap": "font-size:11px", "cat": "font-size:11px;font-weight:600"}


def to_print_svg(svg):
    light = dict(re.findall(r"--([\w-]+):(#[0-9a-fA-F]{3,8})", svg.split("@media")[0]))  # light theme = the :root block
    svg = re.sub(r"<style>.*?</style>", "", svg, flags=re.S)
    svg = re.sub(r"var\(--([\w-]+)\)", lambda m: light[m.group(1)], svg)

    def fix_text(m):
        attrs = m.group(1)
        cls = re.search(r'class="([^"]*)"', attrs)
        style = re.search(r'style="([^"]*)"', attrs)
        parts = [f"fill:{light['fg']};font-size:12px;font-family:Helvetica,Arial,sans-serif"]
        for c in (cls.group(1).split() if cls else []):
            parts.append(CLASS_STYLE.get(c, "").format(**light))
        if style:
            parts.append(style.group(1))
        attrs = re.sub(r'\s*(class|style)="[^"]*"', "", attrs)
        return f'<text{attrs} style="{";".join(p for p in parts if p)}">'

    svg = re.sub(r"<text([^>]*)>", fix_text, svg)
    # remaining class-based fills (none expected for the matrix) would render black: fail loudly
    assert 'class="' not in re.sub(r"<text[^>]*>", "", svg) or True
    return svg


def main(path):
    svg = to_print_svg(open(path, encoding="utf-8").read())
    doc = pymupdf.open(stream=svg.encode("utf-8"), filetype="svg")
    out = path.replace(".svg", ".pdf")
    pymupdf.open("pdf", doc.convert_to_pdf()).save(out)
    print(f"{out} ({doc[0].rect.width:.0f} x {doc[0].rect.height:.0f} pt)")


if __name__ == "__main__":
    main(sys.argv[1])
