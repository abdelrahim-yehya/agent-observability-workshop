#!/usr/bin/env python3
"""Deduplicate metric candidates and apply persistent human review decisions."""

import argparse
import csv
import json
import os
from pathlib import Path
import tempfile

from metric_taxonomy import METRIC_SPECS


DEFAULT_TOOLS = "combined_tools_no_duplicates.csv"
DEFAULT_CANDIDATES = "tool_metric_candidates.csv"
DEFAULT_SOURCES = "metric_source_documents.jsonl"
DEFAULT_REVIEW = "tool_metrics_review.csv"
DEFAULT_OUTPUT = "tool_metrics.csv"
OUTPUT_FIELDS = [
    "tool_key", "tool", "metric_raw", "metric_normalized", "category", "support_type",
    "definition", "source_url", "source_location", "evidence", "confidence",
    "review_status", "review_notes", "checked_date",
]
REVIEW_FIELDS = [
    "tool_key", "metric_normalized", "support_type", "review_status", "review_notes",
]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", default=DEFAULT_TOOLS)
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    parser.add_argument("--sources", default=DEFAULT_SOURCES)
    parser.add_argument("--review", default=DEFAULT_REVIEW)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_csv(path, required):
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def source_statuses(path):
    statuses = {}
    if not Path(path).exists():
        return statuses
    with open(path, encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            record = json.loads(line)
            status = statuses.setdefault(record["tool_key"], {"ok": 0, "error": 0})
            if record.get("collection_status") == "ok" and record.get("content", "").strip():
                status["ok"] += 1
            else:
                status["error"] += 1
    return statuses


def unique_join(values, limit=None):
    unique = []
    for value in values:
        value = value.strip()
        if value and value not in unique:
            unique.append(value)
    if limit:
        unique = unique[:limit]
    return " | ".join(unique)


def normalized_rows(tools, candidates, statuses):
    grouped = {}
    for row in candidates:
        key = (row["tool_key"], row["metric_normalized"], row["support_type"])
        grouped.setdefault(key, []).append(row)

    output = []
    tools_with_candidates = set()
    confidence_rank = {"low": 0, "medium": 1, "high": 2}
    for (tool_key, normalized, support_type), rows in grouped.items():
        tools_with_candidates.add(tool_key)
        best = max(rows, key=lambda row: confidence_rank.get(row["confidence"], -1))
        category, definition, _ = METRIC_SPECS.get(
            normalized, (best.get("category", "unclassified"), "", ())
        )
        output.append({
            "tool_key": tool_key,
            "tool": best["tool"],
            "metric_raw": unique_join((row["metric_raw"] for row in rows), 5),
            "metric_normalized": normalized,
            "category": category,
            "support_type": support_type,
            "definition": definition,
            "source_url": unique_join((row["source_url"] for row in rows), 5),
            "source_location": unique_join((row["source_path"] for row in rows), 5),
            "evidence": unique_join((row["evidence"] for row in rows), 3),
            "confidence": best["confidence"],
            "review_status": "needs_review",
            "review_notes": "",
            "checked_date": max((row["checked_date"] for row in rows), default=""),
        })

    for tool in tools:
        if tool["tool_key"] in tools_with_candidates:
            continue
        source_status = statuses.get(tool["tool_key"], {"ok": 0, "error": 0})
        review_status = "no_candidate_found" if source_status["ok"] else "source_collection_failed"
        output.append({
            "tool_key": tool["tool_key"], "tool": tool["tool"], "metric_raw": "",
            "metric_normalized": "", "category": "", "support_type": "", "definition": "",
            "source_url": "", "source_location": "", "evidence": "", "confidence": "",
            "review_status": review_status, "review_notes": "", "checked_date": "",
        })
    return output


def apply_reviews(rows, review_rows):
    reviews = {
        (row["tool_key"].strip(), row["metric_normalized"].strip(), row["support_type"].strip()): row
        for row in review_rows
        if row["tool_key"].strip()
    }
    reviewed = []
    for row in rows:
        key = (row["tool_key"], row["metric_normalized"], row["support_type"])
        review = reviews.get(key)
        if review:
            status = review.get("review_status", "").strip()
            if status == "exclude":
                continue
            if status:
                row["review_status"] = status
            row["review_notes"] = review.get("review_notes", "").strip()
        reviewed.append(row)
    return reviewed


def write_csv_atomic(path, rows, fieldnames):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=destination.parent,
                                     prefix=destination.name + ".", delete=False) as file:
        temporary = Path(file.name)
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, destination)
    os.chmod(destination, 0o644)


def synchronize_review_file(path, candidate_rows, review_rows):
    by_key = {
        (row["tool_key"].strip(), row["metric_normalized"].strip(), row["support_type"].strip()): {
            field: row.get(field, "").strip() for field in REVIEW_FIELDS
        }
        for row in review_rows
        if row["tool_key"].strip()
    }
    for row in candidate_rows:
        if not row["metric_normalized"]:
            continue
        key = (row["tool_key"], row["metric_normalized"], row["support_type"])
        by_key.setdefault(key, {
            "tool_key": row["tool_key"],
            "metric_normalized": row["metric_normalized"],
            "support_type": row["support_type"],
            "review_status": "",
            "review_notes": "",
        })
    synchronized = sorted(by_key.values(), key=lambda row: (
        row["tool_key"], row["metric_normalized"], row["support_type"]
    ))
    write_csv_atomic(path, synchronized, REVIEW_FIELDS)


def main():
    args = parse_args()
    tools = read_csv(args.tools, {"tool_key", "tool"})
    candidates = read_csv(args.candidates, {
        "tool_key", "tool", "metric_raw", "metric_normalized", "category", "support_type",
        "source_url", "source_path", "evidence", "confidence", "checked_date",
    })
    review_rows = read_csv(
        args.review, {"tool_key", "metric_normalized", "support_type", "review_status", "review_notes"}
    ) if Path(args.review).exists() else []
    rows = normalized_rows(tools, candidates, source_statuses(args.sources))
    synchronize_review_file(args.review, rows, review_rows)
    rows = apply_reviews(rows, review_rows)
    rows.sort(key=lambda row: (
        row["tool"].casefold(), row["category"], row["metric_normalized"], row["support_type"]
    ))
    write_csv_atomic(args.output, rows, OUTPUT_FIELDS)
    candidate_count = sum(bool(row["metric_normalized"]) for row in rows)
    covered_tools = len({row["tool_key"] for row in rows if row["metric_normalized"]})
    print(f"wrote {candidate_count} metric rows covering {covered_tools}/{len(tools)} tools to {args.output}")


if __name__ == "__main__":
    main()

