#!/usr/bin/env python3
"""Write paper/tables/tool_table.tex: the selected tools and standards, grouped as the 2026-11-09 amendment selects them.

Groups: open-source tools (ordered by downloads, then stars), closed-source tools (ordered by independent Google sources)
and standards. Stars and downloads are the values read on 2026-11-06 (data/outputs/open_source_adoption_candidates.csv);
downloads are the larger of PyPI and npm for the last 30 days. Closed-source tools and OpenTelemetry have no stars or
download figures in the table because C1 and the standards channel do not use them.
Run: python3 src/build_tool_table.py
"""
import csv

from paths import ROOT

CITE = {"Arize Phoenix": "tool_arize_phoenix", "Langfuse": "tool_langfuse", "LangSmith": "tool_langsmith", "DeepEval": "tool_deepeval",
        "OpenTelemetry": "tool_opentelemetry", "Helicone": "tool_helicone", "Braintrust": "tool_braintrust", "promptfoo": "tool_promptfoo",
        "OpenLLMetry": "tool_openllmetry", "Opik": "tool_opik", "Galileo": "tool_galileo", "OpenInference": "tool_openinference",
        "Weights & Biases Weave": "tool_weights_biases_weave", "MLflow": "tool_mlflow", "Laminar": "tool_laminar", "LangWatch": "tool_langwatch"}
NAME = {"DeepEval": "DeepEval (with Confident AI)", "Weights & Biases Weave": "Weights \\& Biases Weave"}
# How each tool's documentation relates it to OpenTelemetry (evidence: data/outputs/tool_relations.csv)
OTEL = {"Arize Phoenix": "built on", "Langfuse": "built on", "LangSmith": "accepts", "DeepEval": "accepts", "OpenTelemetry": "defines", "Helicone": "not found",
        "Braintrust": "accepts", "promptfoo": "optional", "OpenLLMetry": "built on", "Opik": "accepts", "Galileo": "accepts", "OpenInference": "built on",
        "Weights & Biases Weave": "span-like", "MLflow": "accepts", "Laminar": "built on", "LangWatch": "built on"}
FOUND = {"GitHub": "GitHub", "GitHub + Google": "GitHub + Google", "Google only": "Google only"}


def n(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def fmt_stars(v):
    v = n(v)
    return f"{v:,}".replace(",", "{,}") if v else "--"


def fmt_dl(v):
    v = n(v)
    if not v:
        return "--"
    return f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}k"


def grouped():
    """Tools by group, in table order: open-source by downloads then stars, closed-source by Google sources, standards fixed."""
    best = {r["tool"]: r for r in csv.DictReader(open(ROOT / "results/best_tools.csv", newline="", encoding="utf-8"))}
    adopt = {r["tool"]: r for r in csv.DictReader(open(ROOT / "data/outputs/open_source_adoption_candidates.csv", newline="", encoding="utf-8"))}
    groups = {"Open-source tools": [], "Closed-source tools": [], "Standards": []}
    for t, b in best.items():
        a = adopt.get(t)
        closed = a is None or a["group"].startswith("closed")
        if b["role"] == "standard":
            g = "Standards"
        elif closed:
            g = "Closed-source tools"
        else:
            g = "Open-source tools"
        stars = n(a["stars"]) if a and not (g == "Closed-source tools") else 0
        dl = max(n(a["pypi_downloads_30d"]), n(a["npm_downloads_30d"])) if a and g == "Open-source tools" else (max(n(a["pypi_downloads_30d"]), n(a["npm_downloads_30d"])) if a and g == "Standards" else 0)
        groups[g].append((t, b, stars, dl, n(b["google_independent_sources"])))
    groups["Open-source tools"].sort(key=lambda x: (-x[3], -x[2]))
    groups["Closed-source tools"].sort(key=lambda x: -x[4])
    order = {"OpenTelemetry": 0, "OpenLLMetry": 1, "OpenInference": 2}
    groups["Standards"].sort(key=lambda x: order[x[0]])
    return groups


# Wording used in the paper; the data keeps the role key "standard".
LABEL = {"Standards": "Telemetry conventions", "standard": "conventions"}


def main():
    groups = grouped()
    out = [r"\begin{tabular}{rlllrrrl}", r"\toprule", r"\# & Tool & Role & Found via & Stars & Downloads & Indep.\ sources & OTel link \\", r"\midrule"]
    for gi, (g, items) in enumerate(groups.items()):
        if gi:
            out.append(r"\midrule")
        out.append(rf"\multicolumn{{8}}{{@{{}}l}}{{\textit{{{LABEL.get(g, g)} ({len(items)})}}}} \\")
        for i, (t, b, stars, dl, src) in enumerate(items, 1):
            out.append(f"{i} & {NAME.get(t, t)}~\\cite{{{CITE[t]}}} & {LABEL.get(b['role'], b['role'])} & {FOUND[b['found_via']]} & {fmt_stars(stars)} & {fmt_dl(dl)} & {src} & {OTEL[t]} \\\\")
    out += [r"\bottomrule", r"\end{tabular}", ""]
    (ROOT / "paper/tables/tool_table.tex").write_text("\n".join(out), encoding="utf-8")
    print("wrote paper/tables/tool_table.tex:", {g: len(v) for g, v in groups.items()})


if __name__ == "__main__":
    main()
