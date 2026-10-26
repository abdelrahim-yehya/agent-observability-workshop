#!/usr/bin/env python3
"""Build results/metric_taxonomy.csv: one row per unique metric, with the tools that support it.

Inputs:  results/built_in_metrics.csv          (evidence rows, one per tool-specific metric)
         data/inputs/taxonomy_definitions.csv   (type, category, unique metric, definition)
         data/inputs/taxonomy_mapping.csv       (tool-specific metric -> unique metric; hand-maintained)
Run:     python3 src/build_taxonomy.py
"""
import csv
from collections import defaultdict

from paths import INPUTS, ROOT

METRICS = ROOT / "results" / "built_in_metrics.csv"
OUTPUT = ROOT / "results" / "metric_taxonomy.csv"


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = read(METRICS)
    rank = {r["tool"]: int(r["tool_rank"]) for r in rows}
    known = {(r["tool"], r["metric_name"]) for r in rows}
    definitions = sorted(read(INPUTS / "taxonomy_definitions.csv"), key=lambda d: d["type"] != "Observability")
    names = {d["taxonomy_metric"] for d in definitions}

    tools = defaultdict(set)
    natives = defaultdict(list)
    mapped = set()
    for m in read(INPUTS / "taxonomy_mapping.csv"):
        key = (m["tool"], m["metric_name"])
        if key not in known or m["taxonomy_metric"] not in names:
            raise ValueError(f"mapping refers to an unknown metric: {m}")
        mapped.add(key)
        tools[m["taxonomy_metric"]].add(m["tool"])
        natives[m["taxonomy_metric"]].append(f'{m["tool"]}: {m["metric_name"]}')
    if known - mapped:
        raise ValueError(f"unmapped metrics: {sorted(known - mapped)}")

    fields = ["type", "category", "metric", "definition", "n_tools", "tools", "tool_specific_names"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for d in definitions:
            supporting = sorted(tools[d["taxonomy_metric"]], key=rank.get)
            writer.writerow({
                "type": d["type"], "category": d["category"], "metric": d["taxonomy_metric"], "definition": d["definition"],
                "n_tools": len(supporting), "tools": "; ".join(supporting),
                "tool_specific_names": " | ".join(natives[d["taxonomy_metric"]]),
            })
    print(f"wrote {OUTPUT}: {len(definitions)} unique metrics from {len(known)} tool-specific metrics")


if __name__ == "__main__":
    main()
