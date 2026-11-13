#!/usr/bin/env python3
"""Draw the paper's Fig. 1: run S7 of the example (the Kubernetes question) as an annotated sequence diagram.

The figure replaces the redrawn Langfuse graph (plot_graph.py). It shows who talks to whom, in order: the user's
question reaches the chatbot application; the application calls the model; the model asks for a search; the
application runs the search tool and sends the result back in the next model call; after two rounds the application
offers no more tools and the model writes the answer. The coloured bars on the lanes are the operations Langfuse
recorded (one outer span, three model calls, two searches) with their durations, and the strip at the bottom puts
the same operations on a time axis, to scale.

Every number and argument is read from results/turns_<tag>.json and results/run_<tag>.json (scenario S7). The
tool outputs are not in the repository (course transcripts), so the first search result is written here and
checked against the length recorded in the placeholder. The explanatory sentences are written by hand.

Output:  results/run_s7_sequence.svg   (fixed light colours, print size 516 x 340 pt = both IEEE columns wide)
Run:     python3 plot_run_sequence.py          # SVG only
         python3 plot_run_sequence.py --pdf    # also print ../paper/figures/run_s7_sequence.pdf with headless Brave
"""
import json
import re
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "20261028-104817"
TURNS = HERE / "results" / f"turns_{TAG}.json"
RUN = HERE / "results" / f"run_{TAG}.json"
OUT = HERE / "results" / "run_s7_sequence.svg"
PDF = HERE.parent / "paper" / "figures" / "run_s7_sequence.pdf"
BRAVE = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

# What the first search returned. The output itself is not in turns_*.json; its length is, and is checked in load().
FIRST_RESULT = "No course found matching 'MCP'"
# Shown in the answer bubble: three verbatim pieces of the recorded answer (checked in load()).
ANSWER_PIECES = [
    "The course does not provide Kubernetes-specific deployment instructions.",
    "If you want to deploy an MCP server to Kubernetes",
    "1. Containerize the server",
]

W, H = 516.0, 340.0
SANS = "Helvetica, Arial, 'Liberation Sans', sans-serif"
MONO = "Menlo, 'DejaVu Sans Mono', Consolas, monospace"
INK, MUTED, RULE, BAND = "#1d2328", "#59636b", "#a9b0b6", "#f2f4f6"
BLUE, TEAL, ORANGE = "#1f5fa8", "#0f7b6c", "#c8540a"  # application, model, tool
TINT = {BLUE: "#e9f0f8", TEAL: "#e4f2ef", ORANGE: "#fbede2"}

LEFT_X, LEFT_W = 4.0, 114.0  # the explanation column on the left
X_APP, X_MODEL, X_TOOL = 178.0, 352.0, 468.0  # lane centres
BAR = 3.0  # half width of a bar on a lane
HEAD_TOP, HEAD_BOTTOM = 4.0, 42.0

# Vertical positions of the arrows (pt from the top).
Y_QUESTION = 48.0
ROUND1 = dict(top=58.0, bottom=130.0, rows=[74.0, 90.0, 106.0, 122.0])
ROUND2 = dict(top=134.0, bottom=206.0, rows=[150.0, 166.0, 182.0, 198.0])
FINAL = dict(top=210.0, bottom=260.0, rows=[226.0, 248.0])
Y_ANSWER = 274.0
LANES_BOTTOM = 282.0

# Time strip.
STRIP_X0, STRIP_X1, STRIP_Y = 140.0, 512.0, 290.0


# ----------------------------------------------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------------------------------------------
def load():
    turn = next(t for t in json.loads(TURNS.read_text(encoding="utf-8"))["turns"] if t["scenario"] == "S7")
    row = next(r for r in json.loads(RUN.read_text(encoding="utf-8"))["rows"] if r["scenario"] == "S7")
    tools = turn["tools"]
    assert turn["llm_calls"] == 3 and len(tools) == 2, "the figure is drawn for three model calls and two searches"
    assert all(t["name"] == "search_course_content" for t in tools)
    sizes = [int(re.search(r"omitted: (\d+) chars", t["output"]).group(1)) for t in tools]
    assert sizes[0] == len(FIRST_RESULT), "first search result does not have the recorded length"
    answer = turn["answer"].replace("‑", "-")  # the model wrote a non-breaking hyphen
    assert all(p in answer for p in ANSWER_PIECES), "answer excerpt is not verbatim"
    args = [json.loads(t["args"]) for t in tools]
    assert set(args[0]) == {"query", "course_name"} and set(args[1]) == {"query"}
    return dict(
        question=turn["question"],
        args=args,
        result_chars=sizes[1],
        passages=len(row["sources"]),
        llm_s=turn["llm_latency_s"],
        tool_s=[t["latency"] for t in tools],
        total_s=turn["latency_s"],
        tokens=turn["tokens"],
        cost=turn["cost"]["total"],
    )


def fmt_args(a):
    return ", ".join(f'{k}="{v}"' for k, v in a.items())


# ----------------------------------------------------------------------------------------------------------------
# Text helpers (widths are estimates, good enough to wrap and centre)
# ----------------------------------------------------------------------------------------------------------------
def text_w(s, size, bold=False, mono=False):
    if mono:
        return len(s) * 0.602 * size
    w = 0.0
    for ch in s:
        if ch in "ijl.,:;'|!":
            w += 0.24
        elif ch in " ftrI()[]-\"“”‘’/":
            w += 0.30
        elif ch in "cskvxyzJ":
            w += 0.50
        elif ch in "mMW":
            w += 0.84
        elif ch == "w":
            w += 0.72
        elif ch.isupper():
            w += 0.68
        else:
            w += 0.556
    return w * size * (1.05 if bold else 1.0)


def wrap(s, width, size=7.0):
    lines, cur = [], ""
    for word in s.split(" "):
        trial = f"{cur} {word}" if cur else word
        if cur and text_w(trial, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    lines.append(cur)
    return lines


def text(x, y, runs, size=7.0, fill=INK, anchor="start", bold=False, mono=False, halo=None):
    """One line of text. `runs` is a string, or a list of (string, {fill, bold, mono}) pieces drawn one after another."""
    attrs = [f'x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}"']
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if bold:
        attrs.append('font-weight="700"')
    if mono:
        attrs.append(f'font-family="{MONO}"')
    if halo:  # a background-coloured outline, so text stays readable where it crosses a line
        attrs.append(f'stroke="{halo}" stroke-width="2.6" stroke-linejoin="round" paint-order="stroke"')
    if isinstance(runs, str):
        body = escape(runs)
    else:
        body = ""
        for s, style in runs:
            a = []
            if "fill" in style:
                a.append(f'fill="{style["fill"]}"')
            if style.get("bold"):
                a.append('font-weight="700"')
            if style.get("mono"):
                a.append(f'font-family="{MONO}" font-size="{style.get("size", 6.4)}"')
            body += f'<tspan {" ".join(a)}>{escape(s)}</tspan>'
    return f'<text {" ".join(attrs)}>{body}</text>'


# ----------------------------------------------------------------------------------------------------------------
# Shapes
# ----------------------------------------------------------------------------------------------------------------
def rect(x, y, w, h, fill, stroke=None, rx=0.0, sw=0.8):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{s}/>'


def arrow(x1, x2, y, reply=False):
    """Request: solid line, filled head. Reply: dashed line, open head."""
    d = 1.0 if x2 > x1 else -1.0
    if reply:
        return (
            f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2 - d:.1f}" y2="{y:.1f}" stroke="{INK}" stroke-width="0.9" '
            f'stroke-dasharray="3 2"/>'
            f'<polyline points="{x2 - d * 5.5:.1f},{y - 2.6:.1f} {x2:.1f},{y:.1f} {x2 - d * 5.5:.1f},{y + 2.6:.1f}" '
            f'fill="none" stroke="{INK}" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round"/>'
        )
    return (
        f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2 - d * 4:.1f}" y2="{y:.1f}" stroke="{INK}" stroke-width="0.9"/>'
        f'<polygon points="{x2:.1f},{y:.1f} {x2 - d * 5.5:.1f},{y - 2.5:.1f} {x2 - d * 5.5:.1f},{y + 2.5:.1f}" '
        f'fill="{INK}"/>'
    )


def message(x_from, x_to, y, runs, reply=False, **kw):
    """An arrow between two lanes with its label centred above it."""
    d = 1.0 if x_to > x_from else -1.0
    x1, x2 = x_from + d * BAR, x_to - d * BAR
    return arrow(x1, x2, y, reply) + text((x1 + x2) / 2, y - 3.4, runs, anchor="middle", halo=BAND, **kw)


def lane_bar(x, y1, y2, colour):
    return rect(x - BAR, y1 - 3, 2 * BAR, y2 - y1 + 6, colour, rx=1.2)


def icon(kind, x, y, colour):
    """A 9 x 9 pt pictogram with its top-left corner at (x, y)."""
    cx, cy = x + 4.5, y + 4.5
    if kind == "user":
        return (
            f'<circle cx="{cx:.1f}" cy="{y + 2.4:.1f}" r="2.3" fill="{colour}"/>'
            f'<path d="M{x + 0.2:.1f},{y + 9.4:.1f} a4.3,4.3 0 0 1 8.6,0 Z" fill="{colour}"/>'
        )
    if kind == "app":  # a window
        return (
            f'<rect x="{x + 0.3:.1f}" y="{y + 0.6:.1f}" width="8.6" height="7.8" rx="1.4" fill="none" '
            f'stroke="{colour}" stroke-width="1.1"/>'
            f'<line x1="{x + 0.3:.1f}" y1="{y + 3.2:.1f}" x2="{x + 8.9:.1f}" y2="{y + 3.2:.1f}" stroke="{colour}" '
            f'stroke-width="1.1"/>'
        )
    if kind == "model":  # a four-point spark
        return (
            f'<path d="M{cx:.1f},{cy - 4.8:.1f} Q{cx + 0.9:.1f},{cy - 0.9:.1f} {cx + 4.8:.1f},{cy:.1f} '
            f'Q{cx + 0.9:.1f},{cy + 0.9:.1f} {cx:.1f},{cy + 4.8:.1f} Q{cx - 0.9:.1f},{cy + 0.9:.1f} '
            f'{cx - 4.8:.1f},{cy:.1f} Q{cx - 0.9:.1f},{cy - 0.9:.1f} {cx:.1f},{cy - 4.8:.1f} Z" fill="{colour}"/>'
        )
    # tool: a magnifying glass
    return (
        f'<circle cx="{x + 3.7:.1f}" cy="{y + 3.7:.1f}" r="2.9" fill="none" stroke="{colour}" stroke-width="1.2"/>'
        f'<line x1="{x + 5.9:.1f}" y1="{y + 5.9:.1f}" x2="{x + 8.7:.1f}" y2="{y + 8.7:.1f}" stroke="{colour}" '
        f'stroke-width="1.5" stroke-linecap="round"/>'
    )


def lane_header(cx, x0, x1, colour, kind, title, desc, span):
    """The box at the top of a lane: who it is, what it does, and the name its bars were recorded under."""
    out = [rect(x0, HEAD_TOP, x1 - x0, HEAD_BOTTOM - HEAD_TOP, TINT[colour], stroke=colour, rx=4)]
    mid = (x0 + x1) / 2
    tw = text_w(title, 8, bold=True)
    start = mid - (tw + 12.5) / 2
    out.append(icon(kind, start, HEAD_TOP + 4.2, colour))
    out.append(text(start + 12.5, HEAD_TOP + 12, title, size=8, fill=colour, bold=True))
    out.append(text(mid, HEAD_TOP + 21.5, desc, fill=MUTED, anchor="middle"))
    sw = text_w(span, 6.3, mono=True)
    sx = mid - (sw + 6) / 2
    out.append(rect(sx, HEAD_TOP + 26.3, 2.8, 7.0, colour, rx=0.8))
    out.append(text(sx + 6, HEAD_TOP + 32.3, span, size=6.3, fill=colour, mono=True))
    return "".join(out)


def band(spec, title, sentence):
    """The grey background of one round, with its explanation in the left column."""
    out = [rect(0, spec["top"], W, spec["bottom"] - spec["top"], BAND, rx=4)]
    out.append(text(LEFT_X + 4, spec["top"] + 11.5, title, size=7.5, bold=True))
    for i, line in enumerate(wrap(sentence, LEFT_W - 8)):
        out.append(text(LEFT_X + 4, spec["top"] + 21.5 + i * 8.6, line, fill=MUTED))
    return "".join(out)


def bubble(y, lines, title=None):
    """A white box in the left column holding the question or the answer; returns (svg, bottom)."""
    top_pad = 17.5 if title else 9.0
    h = top_pad + (len(lines) - 1) * 8.5 + 5.5
    out = [rect(LEFT_X, y, LEFT_W, h, "#ffffff", stroke=RULE, rx=4)]
    if title:
        out.append(text(LEFT_X + 5, y + 9.5, title, bold=True))
    for i, line in enumerate(lines):
        out.append(text(LEFT_X + 5, y + top_pad + i * 8.5, line))
    return "".join(out), y + h


# ----------------------------------------------------------------------------------------------------------------
# The figure
# ----------------------------------------------------------------------------------------------------------------
def draw(d):
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}" '
        f'font-family="{SANS}">',
        rect(0, 0, W, H, "#ffffff"),
    ]
    call_s = [f"{s:.1f} s" for s in d["llm_s"]]
    tool_ms = [f"{s * 1000:.0f} ms" for s in d["tool_s"]]

    # Bands with their explanations.
    p.append(band(ROUND1, "Round 1", "The model asks for a search limited to a course called “MCP”. "
                                     "The search tool finds no course by that name."))
    words = {3: "Three", 4: "Four", 5: "Five"}
    p.append(band(ROUND2, "Round 2", "The model searches again, without the course filter. "
                                     f"{words[d['passages']]} transcript passages come back."))
    p.append(band(FINAL, "Final call", "The application allows two rounds, so it offers no tools now. "
                                       "The model writes the answer."))

    # Lifelines, then the recorded operations as bars on them.
    for x in (X_MODEL, X_TOOL):
        p.append(
            f'<line x1="{x}" y1="{HEAD_BOTTOM}" x2="{x}" y2="{LANES_BOTTOM}" stroke="{RULE}" stroke-width="0.8" '
            f'stroke-dasharray="1.5 2.5"/>'
        )
    p.append(f'<line x1="{X_APP}" y1="{HEAD_BOTTOM}" x2="{X_APP}" y2="{Y_QUESTION}" stroke="{BLUE}" stroke-width="0.8"/>')
    p.append(lane_bar(X_APP, Y_QUESTION, Y_ANSWER, BLUE))
    r1, r2, r3 = ROUND1["rows"], ROUND2["rows"], FINAL["rows"]
    for (ya, yb), label in zip(((r1[0], r1[1]), (r2[0], r2[1]), (r3[0], r3[1])), call_s):
        p.append(lane_bar(X_MODEL, ya, yb, TEAL))
        p.append(text(X_MODEL + BAR + 4, (ya + yb) / 2 + 2.5, label, fill=TEAL, bold=True, halo=BAND))
    for (ya, yb), label in zip(((r1[2], r1[3]), (r2[2], r2[3])), tool_ms):
        p.append(lane_bar(X_TOOL, ya, yb, ORANGE))
        p.append(text(X_TOOL + BAR + 4, (ya + yb) / 2 + 2.5, label, fill=ORANGE, bold=True, halo=BAND))

    # Question in, answer out (left column <-> application).
    q_svg, _ = bubble(20, wrap(f"“{d['question']}”", LEFT_W - 10))
    p.append(icon("user", LEFT_X + 2, 6, INK) + text(LEFT_X + 15, 14.6, "User", size=8, bold=True))
    p.append(q_svg)
    p.append(arrow(LEFT_X + LEFT_W, X_APP - BAR, Y_QUESTION))
    excerpt = "“" + " […] ".join(ANSWER_PIECES) + " […]”"
    a_svg, a_bottom = bubble(Y_ANSWER - 10, wrap(excerpt, LEFT_W - 10), title="Answer (excerpt)")
    p.append(a_svg)
    p.append(arrow(X_APP - BAR, LEFT_X + LEFT_W, Y_ANSWER, reply=True))

    # Round 1.
    mono = dict(mono=True)
    grey = dict(fill=MUTED)
    p.append(message(X_APP, X_MODEL, r1[0], [("call 1", dict(bold=True)), (": instructions, question, tool list", {})]))
    p.append(message(X_MODEL, X_APP, r1[1], "asks for a search (tool call request)", reply=True))
    p.append(message(X_APP, X_TOOL, r1[2], [(fmt_args(d["args"][0]), mono)]))
    p.append(message(X_TOOL, X_APP, r1[3], [(f"“{FIRST_RESULT}”", mono)], reply=True))
    # Round 2.
    p.append(message(X_APP, X_MODEL, r2[0], [("call 2", dict(bold=True)), (": the same, plus the search result", {})]))
    p.append(message(X_MODEL, X_APP, r2[1], "asks for another search", reply=True))
    p.append(message(X_APP, X_TOOL, r2[2], [(fmt_args(d["args"][1]), mono), ("   (no course filter)", grey)]))
    p.append(message(X_TOOL, X_APP, r2[3], f"{d['passages']} transcript passages ({d['result_chars']:,} characters)",
                     reply=True))
    # Final call.
    p.append(message(X_APP, X_MODEL, r3[0], [("call 3", dict(bold=True)), (": all of the above, no tools offered", {})]))
    p.append(message(X_MODEL, X_APP, r3[1], "the answer, as text", reply=True))

    # Lane headers.
    p.append(lane_header(X_APP, 124, 232, BLUE, "app", "Chatbot application", "runs the model–tool loop",
                         "answer-course-question"))
    p.append(lane_header(X_MODEL, 300, 404, TEAL, "model", "Language model", "gpt-5-mini", "generate-response"))
    p.append(lane_header(X_TOOL, 415, 515, ORANGE, "tool", "Search tool", "over 4 course transcripts",
                         "search_course_content"))

    p.append(time_strip(d, call_s, tool_ms))
    p.append("</svg>")
    return "\n".join(p), a_bottom


def time_strip(d, call_s, tool_ms):
    """The recorded operations on a time axis, to scale. Start times are the running sum of the durations."""
    x0, x1, y = STRIP_X0, STRIP_X1, STRIP_Y
    scale = (x1 - x0) / d["total_s"]
    tok = d["tokens"]
    out = [
        text(x0, y + 7, "The same run on a time axis, to scale", size=7.5, bold=True),
        text(x1, y + 7, f"{tok['total']:,.0f} tokens ({tok['input']:,.0f} input, {tok['output']:,.0f} output, "
                        f"{tok['output_reasoning_tokens']:,.0f} reasoning) · ${d['cost']:.4f}",
             fill=MUTED, anchor="end"),
    ]
    # Outer operation.
    ya, yb, h = y + 12, y + 24, 10.5
    out.append(rect(x0, ya, x1 - x0, h, BLUE, rx=1.5))
    out.append(text(x0 + 4, ya + 7.6, "answer-course-question", size=6.3, fill="#ffffff", mono=True))
    out.append(text(x1 - 4, ya + 7.7, f"{d['total_s']:.1f} s", size=6.8, fill="#ffffff", anchor="end", bold=True))
    # Model calls and searches, one after the other.
    order = [("llm", 0), ("tool", 0), ("llm", 1), ("tool", 1), ("llm", 2)]
    t, ticks = 0.0, []
    for kind, i in order:
        if kind == "tool":
            ticks.append(x0 + t * scale)
            t += d["tool_s"][i]
            continue
        dur = d["llm_s"][i]
        sx, sw = x0 + t * scale, dur * scale
        out.append(rect(sx + 0.5, yb, sw - 1.0, h, TEAL, rx=1.5))
        label = f"model call {i + 1}: {call_s[i]}" if sw > 120 else call_s[i]
        out.append(text(sx + sw / 2, yb + 7.7, label, size=6.8, fill="#ffffff", anchor="middle", bold=True))
        t += dur
    ly = yb + h + 9.5
    for tx in ticks:
        out.append(f'<line x1="{tx:.1f}" y1="{yb - 1:.1f}" x2="{tx:.1f}" y2="{ly - 2.5:.1f}" stroke="{ORANGE}" '
                   f'stroke-width="1.1"/>')
    out.append(f'<line x1="{ticks[0]:.1f}" y1="{ly - 2.5:.1f}" x2="{ticks[1] + 4:.1f}" y2="{ly - 2.5:.1f}" '
               f'stroke="{ORANGE}" stroke-width="1.1"/>')
    out.append(text(ticks[1] + 7, ly, f"the two searches: {tool_ms[0]} and {tool_ms[1]}", fill=ORANGE, bold=True))
    return "".join(out)


def print_pdf(svg):
    """Print the SVG to a one-page PDF of exactly its size with headless Brave (same route as the other figures)."""
    page = (
        f"<!doctype html><html><head><meta charset='utf-8'><style>@page{{size:{W}pt {H}pt;margin:0}}"
        f"html,body{{margin:0;padding:0}}svg{{display:block}}</style></head><body>{svg}</body></html>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "page.html"
        html.write_text(page, encoding="utf-8")
        subprocess.run(
            [BRAVE, "--headless", "--disable-gpu", f"--print-to-pdf={PDF}", "--no-pdf-header-footer", html.as_uri()],
            check=True, capture_output=True,
        )
    print(PDF)


def main():
    svg, answer_bottom = draw(load())
    assert answer_bottom <= H - 2, f"answer bubble ends at {answer_bottom:.0f}, below the figure ({H:.0f} pt)"
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT} ({W:.0f} x {H:.0f} pt)")
    if "--pdf" in sys.argv[1:]:
        print_pdf(svg)


if __name__ == "__main__":
    main()
