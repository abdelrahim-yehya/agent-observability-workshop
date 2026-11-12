#!/usr/bin/env python3
"""Build results/metric_taxonomy.csv: one row per unique metric, with the tools that support it.

Inputs:  results/built_in_metrics.csv          (evidence rows, one per tool-specific metric; how_measured and delivery are copied into the output as counts)
         results/best_tools.csv                 (roles; the standards are not studied tools)
         data/inputs/taxonomy_definitions.csv   (type, category, unique metric, definition)
         data/inputs/taxonomy_mapping.csv       (tool-specific metric -> unique metric; hand-maintained)
         data/inputs/taxonomy_standards_only.csv (unique metrics documented as built-in only by standards, not by any studied tool)
Outputs: results/metric_taxonomy.csv            (unique metrics provided by at least one non-standard tool)
         results/standards_only_metrics.csv     (the metrics listed in taxonomy_standards_only.csv, same columns)
Run:     python3 src/build_taxonomy.py
"""
import csv
from collections import defaultdict

from paths import INPUTS, ROOT

METRICS = ROOT / "results" / "built_in_metrics.csv"
OUTPUT = ROOT / "results" / "metric_taxonomy.csv"
OUTPUT_STANDARDS = ROOT / "results" / "standards_only_metrics.csv"


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = read(METRICS)
    rank = {r["tool"]: int(r["tool_rank"]) for r in rows}
    standards = {r["tool"] for r in read(ROOT / "results" / "best_tools.csv") if r["role"] == "standard"}
    standards_only = {r["taxonomy_metric"] for r in read(INPUTS / "taxonomy_standards_only.csv")}
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

    if standards_only - names:
        raise ValueError(f"taxonomy_standards_only.csv names unknown metrics: {sorted(standards_only - names)}")
    for d in definitions:
        name, providers = d["taxonomy_metric"], tools[d["taxonomy_metric"]]
        if name in standards_only and providers - standards:
            raise ValueError(f"{name} is listed as standards-only but studied tools provide it: {sorted(providers - standards)}")
        if name not in standards_only and not providers - standards:
            raise ValueError(f"{name} is provided only by standards: add it to taxonomy_standards_only.csv")

    fields = ["type", "category", "metric", "definition", "n_tools", "tools", "tool_specific_names", "how_measured", "delivery"]

    def write(path, selected):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for d in selected:
                name = d["taxonomy_metric"]
                supporting = sorted(tools[name], key=rank.get)
                writer.writerow({
                    "type": d["type"], "category": d["category"], "metric": name, "definition": d["definition"],
                    "n_tools": len(supporting), "tools": "; ".join(supporting),
                    "tool_specific_names": " | ".join(natives[name]),
                    "how_measured": "; ".join(f"{k} ({v})" for k, v in sorted(how[name].items())),
                    "delivery": "; ".join(f"{k} ({v})" for k, v in sorted(delivery[name].items())),
                })

    write(OUTPUT, [d for d in definitions if d["taxonomy_metric"] not in standards_only])
    write(OUTPUT_STANDARDS, [d for d in definitions if d["taxonomy_metric"] in standards_only])
    print(f"wrote {OUTPUT}: {len(definitions) - len(standards_only)} unique metrics from {len(known)} tool-specific metrics; "
          f"{OUTPUT_STANDARDS.name}: {len(standards_only)} standards-only")


if __name__ == "__main__":
    main()
