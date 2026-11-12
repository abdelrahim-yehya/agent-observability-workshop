#!/usr/bin/env python3
"""Draw the paper's Fig. 1: run S7 of the example (the Kubernetes question), redrawn from Langfuse's agent graph.

Langfuse draws the run as a graph with routed edges that are hard to follow (figures/langfuse_graph_s7.png in the
paper folder). This script draws the same run as one vertical chain with straight arrows: the outer span
answer-course-question covers the whole run; inside it three model calls (generate-response) alternate with two
searches (search_course_content). The node labels and the two search results come from results/turns_*.json (S7).

Output:  results/langfuse_graph_s7.svg   (fixed light colours, print size 252 x 256 pt = one IEEE column wide)
PDF:     wrap the SVG in an HTML page with  @page{size:252pt 256pt;margin:0}  and print it with
         "Brave Browser" --headless --print-to-pdf=../paper/figures/langfuse_graph_s7.pdf --no-pdf-header-footer page.html
Run:     python3 plot_graph.py
"""
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "langfuse_graph_s7.svg"

W, H = 252.0, 256.0
FONT = "Helvetica, Arial, 'Liberation Sans', sans-serif"
INK, MUTED = "#1d2328", "#5d666d"
GREEN, RED, PURPLE, PINK, ORANGE = "#1a8a3a", "#c8202a", "#7a3fc4", "#b5279a", "#d9560f"

NODE_W, NODE_H, GAP = 118.0, 18.0, 13.0  # inner nodes: box size and vertical space between boxes
X = 24.0  # left edge of the inner nodes
NOTE_X = X + NODE_W + 6  # left edge of the grey notes

# The run as Langfuse recorded it (results/turns_20261028-104817.json, scenario S7), top to bottom.
STEPS = [
    ("generate-response", PINK, "model call 1: decides to search"),
    ("search_course_content", ORANGE, "course “MCP”: “No course found matching ‘MCP’”"),
    ("generate-response", PINK, "model call 2: searches again"),
    ("search_course_content", ORANGE, "no course filter: returns course content"),
    ("generate-response", PINK, "model call 3: writes the answer"),
]


def box(x, y, w, h, label, colour, fill="#ffffff", bold=False, text_colour=None):
    weight = ' font-weight="600"' if bold else ""
    tc = text_colour or colour
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="3" ry="3" '
        f'fill="{fill}" stroke="{colour}" stroke-width="1.2"/>'
        f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 3:.1f}" text-anchor="middle" font-size="8.5" '
        f'font-family="{FONT}"{weight} fill="{tc}">{escape(label)}</text>'
    )


def arrow(x, y1, y2):
    return (
        f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2 - 4:.1f}" stroke="{MUTED}" stroke-width="1"/>'
        f'<polygon points="{x - 3:.1f},{y2 - 5:.1f} {x + 3:.1f},{y2 - 5:.1f} {x:.1f},{y2:.1f}" fill="{MUTED}"/>'
    )


def note(y, text):
    # The grey note to the right of a node, wrapped by hand at the quotation marks when it is long.
    return (
        f'<text x="{NOTE_X:.1f}" y="{y:.1f}" font-size="7" font-family="{FONT}" fill="{MUTED}">{escape(text)}</text>'
    )


def main():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
    ]
    cx = X + NODE_W / 2  # the arrows run down the middle of the inner nodes
    y = 6.0
    parts.append(box(X, y, NODE_W, NODE_H, "__start__", GREEN, fill=GREEN, bold=True, text_colour="#ffffff"))
    y += NODE_H

    # Outer span: a dashed frame around the five steps, labelled on its top edge.
    frame_top = y + GAP
    inner_top = frame_top + 20
    inner_h = len(STEPS) * NODE_H + (len(STEPS) - 1) * GAP
    frame_h = 20 + inner_h + 10
    parts.append(arrow(cx, y, frame_top))
    parts.append(
        f'<rect x="{X - 12:.1f}" y="{frame_top:.1f}" width="{W - X + 4:.1f}" height="{frame_h:.1f}" rx="4" ry="4" '
        f'fill="#faf8ff" stroke="{PURPLE}" stroke-width="1.2" stroke-dasharray="3 2"/>'
    )
    parts.append(
        f'<text x="{X - 6:.1f}" y="{frame_top + 12:.1f}" font-size="8.5" font-family="{FONT}" font-weight="600" '
        f'fill="{PURPLE}">answer-course-question</text>'
        f'<text x="{X + 100:.1f}" y="{frame_top + 12:.1f}" font-size="7" font-family="{FONT}" fill="{MUTED}">'
        f'the whole run, one span</text>'
    )

    y = inner_top
    for i, (label, colour, text) in enumerate(STEPS):
        parts.append(box(X, y, NODE_W, NODE_H, label, colour))
        for j, line in enumerate(wrap(text)):
            parts.append(note(y + 8 + j * 8.5, line))
        if i < len(STEPS) - 1:
            parts.append(arrow(cx, y + NODE_H, y + NODE_H + GAP))
        y += NODE_H + GAP

    y = frame_top + frame_h
    parts.append(arrow(cx, y, y + GAP))
    y += GAP
    parts.append(box(X, y, NODE_W, NODE_H, "__end__", RED, fill=RED, bold=True, text_colour="#ffffff"))
    parts.append("</svg>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{OUT} (bottom at {y + NODE_H:.0f} of {H:.0f} pt)")


def wrap(text, width=24):
    """Break a note into lines of at most `width` characters at spaces."""
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}" if cur else w
    lines.append(cur)
    return lines


if __name__ == "__main__":
    main()
