#!/usr/bin/env python3
"""Extract reviewable metric candidates from collected documentation."""

import argparse
import csv
import json
import os
from pathlib import Path
import re
import tempfile

from metric_taxonomy import METRIC_SPECS


DEFAULT_INPUT = "metric_source_documents.jsonl"
DEFAULT_OUTPUT = "tool_metric_candidates.csv"
OUTPUT_FIELDS = [
    "tool_key", "tool", "metric_raw", "metric_normalized", "category", "support_type",
    "source_url", "source_path", "evidence", "confidence", "review_status", "checked_date",
]
SUPPORT_SIGNAL = re.compile(
    r"\b(?:metric|measure|track|monitor|record|capture|score|scorer|evaluate|evaluator|evaluation)\w*\b",
    re.I,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    return parser.parse_args()


def alias_pattern(alias):
    escaped = re.escape(alias).replace(r"\ ", r"[\s_-]+")
    return re.compile(r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])", re.I)


PATTERNS = sorted(
    ((normalized, category, definition, alias, alias_pattern(alias))
     for normalized, (category, definition, aliases) in METRIC_SPECS.items()
     for alias in aliases),
    key=lambda item: len(item[3]),
    reverse=True,
)


def classify_support(context, category):
    lowered = context.casefold()
    if re.search(r"\bcustom(?:izable)?\s+(?:metric|score|scorer|evaluator)s?\b", lowered):
        return "custom_only"
    if re.search(r"\b(?:built[ -]?in|predefined|out[ -]?of[ -]?the[ -]?box|native)\b", lowered):
        return "built_in_evaluator" if re.search(r"\b(?:eval|score|scorer|judge)\w*\b", lowered) else "built_in_metric"
    if re.search(r"\b(?:evaluator|scorer|llm.as.a.judge|evaluation score)\b", lowered):
        return "built_in_evaluator"
    if re.search(r"\b(?:opentelemetry|otel|integration|export(?:er)?|import)\b", lowered):
        return "integration"
    if re.search(r"\b(?:dashboard|visuali[sz]e|display|chart)\b", lowered):
        return "dashboard_only"
    if re.search(r"\b(?:trace|span|log|record|capture|instrument|telemetry|monitor|track)\w*\b", lowered):
        return "captured_telemetry"
    if category in {"performance", "usage_cost", "operational"}:
        return "captured_telemetry"
    return "unverified_candidate"


def evidence_for(text, start, end):
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    evidence = re.sub(r"\s+", " ", text[line_start:line_end]).strip(" #*|-\t")
    if len(evidence) < 20:
        evidence = re.sub(r"\s+", " ", text[max(0, start - 180):min(len(text), end + 180)]).strip()
    return evidence[:500]


def confidence_for(context, support_type):
    lowered = context.casefold()
    if re.search(r"\b(?:built[ -]?in|predefined|out[ -]?of[ -]?the[ -]?box|native)\b", lowered):
        return "high"
    if SUPPORT_SIGNAL.search(context) or support_type in {"captured_telemetry", "built_in_evaluator"}:
        return "medium"
    return "low"


def candidate_rows(record):
    if record.get("collection_status") != "ok" or not record.get("content", "").strip():
        return []
    text = record["content"]
    found = {}
    occupied = []
    for normalized, category, definition, alias, pattern in PATTERNS:
        for match in pattern.finditer(text):
            if any(match.start() >= start and match.end() <= end for start, end in occupied):
                continue
            context = text[max(0, match.start() - 240):min(len(text), match.end() + 240)]
            support_type = classify_support(context, category)
            confidence = confidence_for(context, support_type)
            key = (normalized, support_type)
            row = {
                "tool_key": record["tool_key"],
                "tool": record["tool"],
                "metric_raw": match.group(0),
                "metric_normalized": normalized,
                "category": category,
                "support_type": support_type,
                "source_url": record.get("source_url", ""),
                "source_path": record.get("source_path", ""),
                "evidence": evidence_for(text, match.start(), match.end()),
                "confidence": confidence,
                "review_status": "needs_review",
                "checked_date": record.get("collected_date", ""),
            }
            rank = {"low": 0, "medium": 1, "high": 2}
            if key not in found or rank[confidence] > rank[found[key]["confidence"]]:
                found[key] = row
            occupied.append((match.start(), match.end()))
    return list(found.values())


def write_csv_atomic(path, rows):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=destination.parent,
                                     prefix=destination.name + ".", delete=False) as file:
        temporary = Path(file.name)
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, destination)
    os.chmod(destination, 0o644)


def main():
    args = parse_args()
    candidates = []
    with open(args.input, encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON on line {line_number} of {args.input}: {error}") from error
            candidates.extend(candidate_rows(record))

    candidates.sort(key=lambda row: (
        row["tool"].casefold(), row["category"], row["metric_normalized"], row["support_type"]
    ))
    write_csv_atomic(args.output, candidates)
    print(f"wrote {len(candidates)} reviewable metric candidates to {args.output}")


if __name__ == "__main__":
    main()

