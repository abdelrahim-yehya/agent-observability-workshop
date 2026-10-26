#!/usr/bin/env python3
"""Build the tool x metric matrix from the evidence tables.

Inputs:  results/best_tools.csv                         (tools in rank order)
         results/built_in_metrics.csv                   (built-in evidence rows)
         data/inputs/taxonomy_mapping.csv               (built-in row -> unique metric)
         data/inputs/taxonomy_definitions.csv           (type, category, unique metric)
         data/inputs/taxonomy_mapping_not_built_in.csv  (integration, community and template rows -> unique metric)
         data/interim/metrics_out_of_scope.csv          (evidence rows for the not-built-in mapping)
Outputs: results/tool_metric_matrix.csv       one row per unique metric, one column per tool
         results/tool_metric_matrix_long.csv  one row per tool and metric, with evidence
Run:     python3 src/build_matrix.py

Status of a cell, strongest first:
  built-in         a documented built-in row maps to the metric
  integration      provided only through a third-party library the tool wraps
  community        a community-contributed metric in the tool's docs
  template         a copy-and-run example in the docs, not shipped as a metric
  generic custom   (Evaluation metrics only) no specific metric, but the tool documents a mechanism
                   for user-defined evaluators, so the user could build it
  records scores   (Evaluation metrics only) the tool defines or stores fields for scores produced
                   elsewhere and has no evaluator mechanism of its own (OpenTelemetry, OpenInference, Helicone)
  not documented   nothing found in the pages read (not proof that the tool lacks it)
"""
import csv

from paths import INPUTS, INTERIM, ROOT

RESULTS = ROOT / "results"
ORDER = ["built-in", "integration", "community", "template"]
RECORD_ONLY = {"OpenTelemetry", "OpenInference", "Helicone"}


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    tools = [r["tool"] for r in read(RESULTS / "best_tools.csv")]
    alias = {"Weights & Biases Weave": "Weights & Biases Weave"}
    built = read(RESULTS / "built_in_metrics.csv")
    info = {(r["tool"], r["metric_name"]): r for r in built}
    definitions = sorted(read(INPUTS / "taxonomy_definitions.csv"), key=lambda d: d["type"] != "Observability")
    names = {d["taxonomy_metric"] for d in definitions}

    cells = {}  # (tool, metric) -> {status: [evidence rows]}
    for m in read(INPUTS / "taxonomy_mapping.csv"):
        r = info[(m["tool"], m["metric_name"])]
        cells.setdefault((m["tool"], m["taxonomy_metric"]), {}).setdefault("built-in", []).append(r)
    out_rows = {(r["tool"], r["metric_name"]): r for r in read(INTERIM / "metrics_out_of_scope.csv")}
    for m in read(INPUTS / "taxonomy_mapping_not_built_in.csv"):
        if m["taxonomy_metric"] not in names:
            raise ValueError(f"unknown metric: {m}")
        r = out_rows[(m["tool"], m["metric_name"])]
        cells.setdefault((m["tool"], m["taxonomy_metric"]), {}).setdefault(m["status"], []).append(r)
    custom = {t for (t, _), r in out_rows.items() if r["built_in"] == "custom-only"}
    if set(tools) - custom:
        raise ValueError(f"no custom-only evidence row for: {sorted(set(tools) - custom)}")
    unknown = {t for t, _ in cells} - set(tools)
    if unknown:
        raise ValueError(f"tools not in best_tools.csv: {sorted(unknown)}")

    def status(tool, d):
        found = cells.get((tool, d["taxonomy_metric"]), {})
        for s in ORDER:
            if s in found:
                return s, found[s]
        if d["type"] != "Evaluation":
            return "not documented", []
        return ("records scores" if tool in RECORD_ONLY else "generic custom"), []

    wide, long = [], []
    for d in definitions:
        row = {"type": d["type"], "category": d["category"], "metric": d["taxonomy_metric"]}
        n_built = 0
        for t in tools:
            s, ev = status(t, d)
            row[t] = s
            n_built += s == "built-in"
            long.append({
                "type": d["type"], "category": d["category"], "metric": d["taxonomy_metric"], "tool": t, "status": s,
                "tool_specific_names": " | ".join(r["metric_name"] for r in ev),
                "delivery": "; ".join(sorted({r.get("delivery", "") for r in ev} - {""})),
                "doc_url": ev[0]["doc_url"] if ev else "",
            })
        row["n_built_in"] = n_built
        wide.append(row)

    for name, rows, fields in (
        ("tool_metric_matrix.csv", wide, ["type", "category", "metric"] + tools + ["n_built_in"]),
        ("tool_metric_matrix_long.csv", long, ["type", "category", "metric", "tool", "status", "tool_specific_names", "delivery", "doc_url"]),
    ):
        with open(RESULTS / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print(f"wrote {len(wide)} metrics x {len(tools)} tools to {RESULTS}")


if __name__ == "__main__":
    main()
