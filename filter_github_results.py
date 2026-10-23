#!/usr/bin/env python3
"""Apply exclusion criteria to the GitHub search results.

The classifier uses only the repository name and GitHub description. It writes
retained candidates to one CSV and excluded rows, including the reason, to a
second CSV so that every decision can be audited.

Run:
    python3 filter_github_results.py
    python3 filter_github_results.py --input results.csv --output included.csv --excluded excluded.csv
"""

import argparse
import csv
import re
from collections import Counter


DEFAULT_INPUT = "github_raw_results.csv"
DEFAULT_OUTPUT = "github_filtered_results.csv"
DEFAULT_EXCLUDED = "github_excluded_results.csv"

# These sets provide a narrow escape hatch for decisions that cannot be made
# reliably from a short GitHub description. Values must be lowercase owner/repo.
FORCE_INCLUDE = set()
FORCE_EXCLUDE = {}

E4_PATTERNS = (
    re.compile(r"(?:^|[/_-])awesome(?:$|[/_-])"),
    re.compile(r"(?:^|[/_-])(?:course|courses|tutorial|tutorials|guide|guides|learning|roadmap|roadmaps|"
               r"interview|interviews|cheatsheet|workshop|academy|handbook|docs|from-scratch|"
               r"starter-pack)(?:$|[/_\s-])"),
    re.compile(r"\b(?:curated|hand-picked) (?:list|collection|catalogue|library)\b"),
    re.compile(r"\b(?:tutorials?|courses?|learning resources?|educational resources?|lecture|lectures)\b"),
)

E1_PATTERNS = (
    re.compile(r"(?:^|[/_-])(?:gateway|proxy|router)(?:$|[/_\s-])"),
    re.compile(r"\b(?:llm|ai|model|mcp|agent|api) gateway\b"),
    re.compile(r"\bproxy (?:server|service|tool)\b"),
    re.compile(r"\b(?:route|routing) (?:requests?|traffic|models?|providers?)\b"),
    re.compile(r"\bintercept(?:s|ed|ing)? .*\bapi traffic\b"),
    re.compile(r"网关"),
)

E3_PATTERNS = (
    re.compile(r"(?:^|[/_-])(?:lm-evaluation-harness|opencompass|helm|litgpt|lmms-eval|"
               r"[^/\s]*llm-benchmark|[^/\s]*model-benchmark)(?:$|[/_\s-])"),
    re.compile(r"\b(?:foundation |language |large language )?model evaluation (?:framework|harness|platform|suite)\b"),
    re.compile(r"\b(?:llm|language model|foundation model) benchmark(?:s|ing)?\b"),
    re.compile(r"\bevaluat(?:e|es|ing|ion) .*\bmodels?\b"),
    re.compile(r"\bmodels? .*\b(?:leaderboard|benchmark(?:s|ing)?)\b"),
)
E3_TRAINING_PATTERN = re.compile(r"^(?:easily )?(?:pretrain|pre-train|fine-tune|finetune)\b")

E2_PATTERNS = (
    re.compile(r"\b(?:ai |llm |multi-?agent |agentic )?agent framework\b"),
    re.compile(r"\bframework for (?:building |creating |developing )?(?:ai |llm |agentic )?agents?\b"),
    re.compile(r"\bframework for ai-powered applications and agents\b"),
    re.compile(r"\b(?:build|run|manage|orchestrate) agent platforms?\b"),
    re.compile(r"\bagentic ai framework\b"),
    re.compile(r"\bagent os\b"),
    re.compile(r"\blocal-first .*\bagent harness\b"),
    re.compile(r"\btoolkit for building,? .*\bagents?\b"),
)

SCOPE_PATTERN = re.compile(
    r"\b(?:ai|llms?|large language models?|language models?|generative ai|genai|agents?|agentic|"
    r"rag|prompts?|model context protocol|mcp)\b"
)
STRONG_SCOPE_PATTERN = re.compile(
    r"\b(?:llms?|large language models?|language models?|generative ai|genai|agents?|agentic|"
    r"rag|prompts?|model context protocol|mcp)\b"
)
MEASUREMENT_PATTERN = re.compile(
    r"\b(?:observability|observe|evaluation|evals?|evaluat(?:e|es|ed|ing)|tracing|traces?|"
    r"monitoring|monitor|telemetry|opentelemetry|benchmarking|benchmarks?|experimentation|"
    r"experiments?|quality|debugging|debug|guardrails?|auditing|audit|optimization|"
    r"vulnerability scanner)\b"
)
TESTING_SCOPE_PATTERN = re.compile(
    r"(?:\b(?:test|tests|testing)\b.{0,40}\b(?:llms?|agents?|rag|prompts?|mcp)\b|"
    r"\b(?:llms?|agents?|rag|prompts?|mcp)\b.{0,40}\b(?:test|tests|testing)\b)"
)
GENERAL_ML_PATTERN = re.compile(
    r"\b(?:mlops|machine learning|ai workload|data management|model training)\b"
)
UNRELATED_PATTERNS = (
    re.compile(r"\bpenetration testing\b"),
    re.compile(r"\bstock monitoring\b"),
    re.compile(r"\b(?:persistent )?memory for (?:ai )?(?:coding )?agents?\b"),
    re.compile(r"\brag(?:lite)? is (?:a |an )?.*\b(?:framework|toolkit)\b"),
)


def first_match(patterns, text):
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def classify(row, seen_repos):
    """Return (exclusion_code, reason), or (None, None) when the row is retained."""
    repo = row.get("repo", "").strip()
    repo_key = repo.casefold()
    description = row.get("description", "").strip()
    text = f"{repo} {description}".casefold()
    description_text = description.casefold()

    if repo_key in seen_repos:
        return "E5", "duplicate repository name"
    seen_repos.add(repo_key)

    if repo_key in FORCE_INCLUDE:
        return None, None
    if repo_key in FORCE_EXCLUDE:
        return FORCE_EXCLUDE[repo_key]

    match = first_match(E4_PATTERNS, text)
    if match:
        return "E4", f"tutorial, course, guide, or curated list: {match}"

    match = first_match(E1_PATTERNS, text)
    if match:
        return "E1", f"gateway or proxy: {match}"

    match = first_match(E3_PATTERNS, text)
    if not match:
        training_match = E3_TRAINING_PATTERN.search(description_text)
        match = training_match.group(0) if training_match else None
    if match:
        return "E3", f"model-level evaluation or training harness: {match}"

    match = first_match(E2_PATTERNS, text)
    if match:
        return "E2", f"agent framework or harness: {match}"

    match = first_match(UNRELATED_PATTERNS, text)
    if match:
        return "UNRELATED", f"unrelated application or framework: {match}"

    if GENERAL_ML_PATTERN.search(text) and not STRONG_SCOPE_PATTERN.search(text):
        return "UNRELATED", "general ML platform without explicit LLM or agent measurement scope"

    has_scope = SCOPE_PATTERN.search(text)
    has_measurement = MEASUREMENT_PATTERN.search(text) or TESTING_SCOPE_PATTERN.search(text)
    if not has_scope or not has_measurement:
        return "UNRELATED", "lacks clear LLM/agent scope or tracing/evaluation evidence"

    return None, None


def filter_rows(rows):
    included = []
    excluded = []
    seen_repos = set()

    for row in rows:
        code, reason = classify(row, seen_repos)
        if code is None:
            included.append(row)
        else:
            excluded.append({**row, "exclusion_code": code, "exclusion_reason": reason})

    return included, excluded


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT, help="raw GitHub search CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="retained candidates CSV")
    parser.add_argument("--excluded", default=DEFAULT_EXCLUDED, help="excluded rows audit CSV")
    return parser.parse_args()


def main():
    args = parse_args()
    rows = read_rows(args.input)
    if not rows:
        raise ValueError(f"no rows found in {args.input}")
    if "repo" not in rows[0] or "description" not in rows[0]:
        raise ValueError("input CSV must contain 'repo' and 'description' columns")

    included, excluded = filter_rows(rows)
    source_fields = list(rows[0].keys())
    write_rows(args.output, included, source_fields)
    write_rows(args.excluded, excluded, source_fields + ["exclusion_code", "exclusion_reason"])

    counts = Counter(row["exclusion_code"] for row in excluded)
    summary = ", ".join(f"{code}={counts[code]}" for code in sorted(counts))
    print(f"read {len(rows)} rows from {args.input}")
    print(f"retained {len(included)} rows in {args.output}")
    print(f"excluded {len(excluded)} rows in {args.excluded} ({summary})")


if __name__ == "__main__":
    main()
