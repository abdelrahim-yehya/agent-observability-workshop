#!/usr/bin/env python3
"""Build results/metric_taxonomy.csv: one row per unique metric, with the tools that support it.

Inputs:  results/built_in_metrics.csv          (evidence rows, one per tool-specific metric; how_measured and delivery are copied into the output as counts)
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
    how = defaultdict(lambda: defaultdict(int))
    delivery = defaultdict(lambda: defaultdict(int))
    attrs = {(r["tool"], r["metric_name"]): (r["how_measured"], r["delivery"]) for r in rows}
    mapped = set()
    for m in read(INPUTS / "taxonomy_mapping.csv"):
        key = (m["tool"], m["metric_name"])
        if key not in known or m["taxonomy_metric"] not in names:
            raise ValueError(f"mapping refers to an unknown metric: {m}")
        mapped.add(key)
        tools[m["taxonomy_metric"]].add(m["tool"])
        natives[m["taxonomy_metric"]].append(f'{m["tool"]}: {m["metric_name"]}')
        how[m["taxonomy_metric"]][attrs[key][0]] += 1
        delivery[m["taxonomy_metric"]][attrs[key][1]] += 1
    if known - mapped:
        raise ValueError(f"unmapped metrics: {sorted(known - mapped)}")

    fields = ["type", "category", "metric", "definition", "n_tools", "tools", "tool_specific_names", "how_measured", "delivery"]
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for d in definitions:
            supporting = sorted(tools[d["taxonomy_metric"]], key=rank.get)
            writer.writerow({
                "type": d["type"], "category": d["category"], "metric": d["taxonomy_metric"], "definition": d["definition"],
                "n_tools": len(supporting), "tools": "; ".join(supporting),
                "tool_specific_names": " | ".join(natives[d["taxonomy_metric"]]),
                "how_measured": "; ".join(f"{k} ({v})" for k, v in sorted(how[d["taxonomy_metric"]].items())),
                "delivery": "; ".join(f"{k} ({v})" for k, v in sorted(delivery[d["taxonomy_metric"]].items())),
            })
    print(f"wrote {OUTPUT}: {len(definitions)} unique metrics from {len(known)} tool-specific metrics")


if __name__ == "__main__":
    main()
