#!/usr/bin/env python3
"""Merge filtered GitHub tools with the included Google-screened tools.

The output contains one row per canonical tool. GitHub metadata is retained,
Google screening evidence is retained, and source provenance is recorded.

Run:
    python3 merge_tool_sources.py
    python3 merge_tool_sources.py --github github.csv --google google.csv --output tools.csv
"""

import argparse
import csv
import re
import unicodedata


DEFAULT_GITHUB = "github_filtered_results.csv"
DEFAULT_GOOGLE = "tool_screening_google.csv"
DEFAULT_OUTPUT = "combined_tools_no_duplicates.csv"


# Repository names do not always match the public tool name. Only exceptions
# need to be listed; all other names are derived from the repository slug.
REPO_TOOL_NAMES = {
    "agentops-ai/agentops": "AgentOps",
    "arize-ai/openinference": "OpenInference",
    "arize-ai/phoenix": "Arize Phoenix",
    "confident-ai/deepeval": "DeepEval",
    "failproofai/failproofai": "FailproofAI",
    "giskard-ai/giskard-oss": "Giskard",
    "googlecloudplatform/agent-starter-pack": "Google Cloud Agent Starter Pack",
    "jwuthri-cloud/tracely-ai": "Tracely AI",
    "latitude-dev/latitude-llm": "Latitude",
    "lmnr-ai/lmnr": "Laminar",
    "mlflow/mlflow": "MLflow",
    "mcpjam/inspector": "MCP Inspector",
    "mozilla-ai/any-agent": "Any Agent",
    "nvidia/garak": "garak",
    "openlit/openlit": "OpenLIT",
    "openobserve/openobserve": "OpenObserve",
    "promptfoo/promptfoo": "promptfoo",
    "pydantic/logfire": "Pydantic Logfire",
    "ricky-7-yan/intelligent-audit-system": "Intelligent Audit System",
    "tencent/ai-infra-guard": "AI Infra Guard",
    "tiger-ai-lab/clawbench": "ClawBench",
    "traceloop/openllmetry": "OpenLLMetry",
    "truera/trulens": "TruLens",
    "signoz/signoz": "SigNoz",
    "langwatch/langwatch": "LangWatch",
    "future-agi/future-agi": "Future AGI",
}


def basic_key(value):
    """Return a case- and punctuation-insensitive identity key."""
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


# These are branding variants of the same tool, not merely related products.
NAME_ALIASES = {
    basic_key("Arize AX"): basic_key("Arize"),
    basic_key("Datadog Agent Observability"): basic_key("Datadog"),
    basic_key("Datadog LLM Observability"): basic_key("Datadog"),
    basic_key("Grafana Cloud Agent Observability"): basic_key("Grafana"),
    basic_key("Splunk Agent Observability"): basic_key("Splunk"),
    basic_key("Splunk AI Agent Monitoring"): basic_key("Splunk"),
}

OUTPUT_FIELDS = [
    "tool_key",
    "tool",
    "sources",
    "github_repo",
    "stars",
    "last_push",
    "license",
    "description",
    "google_independent_sources",
    "google_query_count",
    "google_rule",
    "google_reason",
]


def canonical_key(tool_name):
    key = basic_key(tool_name)
    return NAME_ALIASES.get(key, key)


def repo_tool_name(repo):
    repo_key = repo.strip().casefold()
    if repo_key in REPO_TOOL_NAMES:
        return REPO_TOOL_NAMES[repo_key]

    slug = repo.strip().rstrip("/").split("/")[-1]
    words = [word for word in re.split(r"[-_]+", slug) if word]
    return " ".join(word if any(char.isupper() for char in word) else word.title() for word in words)


def read_csv(path, required_fields):
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = required_fields.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def empty_record(key, label):
    return {
        "tool_key": key,
        "tool": label,
        "github_repo": "",
        "stars": "",
        "last_push": "",
        "license": "",
        "description": "",
        "_sources": set(),
        "_google_included": False,
        "_google_independent_sources": "",
        "_google_query_count": "",
        "_google_rule": [],
        "_google_reason": [],
    }


def append_unique(values, value):
    if value and value not in values:
        values.append(value)


def merge_sources(github_rows, google_rows):
    records = {}

    for row in github_rows:
        repo = row["repo"].strip()
        tool = repo_tool_name(repo)
        key = canonical_key(tool)
        record = records.setdefault(key, empty_record(key, tool))

        if record["github_repo"] and record["github_repo"].casefold() != repo.casefold():
            raise ValueError(
                f"canonical key collision between {record['github_repo']} and {repo}; "
                "add a more specific repository name mapping"
            )

        record["tool"] = tool
        record["github_repo"] = repo
        record["stars"] = row.get("stars", "")
        record["last_push"] = row.get("last_push", "")
        record["license"] = row.get("license", "")
        record["description"] = row.get("description", "")
        record["_sources"].add("github")

    for row in google_rows:
        if row.get("decision", "").strip().casefold() != "include":
            continue

        tool = row["tool"].strip()
        key = canonical_key(tool)
        if not key:
            continue

        record = records.setdefault(key, empty_record(key, tool))
        record["_sources"].add("google")
        record["_google_included"] = True

        independent_sources = row.get("independent_sources", "").strip()
        query_count = row.get("queries", "").strip()
        if independent_sources.isdigit():
            current = record["_google_independent_sources"]
            record["_google_independent_sources"] = str(max(int(current or 0), int(independent_sources)))
        if query_count.isdigit():
            current = record["_google_query_count"]
            record["_google_query_count"] = str(max(int(current or 0), int(query_count)))

        append_unique(record["_google_rule"], row.get("rule", "").strip())
        append_unique(record["_google_reason"], row.get("reason", "").strip())

    output_rows = []
    for record in records.values():
        output_rows.append({
            "tool_key": record["tool_key"],
            "tool": record["tool"],
            "sources": ";".join(sorted(record["_sources"])),
            "github_repo": record["github_repo"],
            "stars": record["stars"],
            "last_push": record["last_push"],
            "license": record["license"],
            "description": record["description"],
            "google_independent_sources": record["_google_independent_sources"],
            "google_query_count": record["_google_query_count"],
            "google_rule": " | ".join(record["_google_rule"]),
            "google_reason": " | ".join(record["_google_reason"]),
        })

    return output_rows


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github", default=DEFAULT_GITHUB, help="filtered GitHub CSV")
    parser.add_argument("--google", default=DEFAULT_GOOGLE, help="screened Google tools CSV")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="combined output CSV")
    return parser.parse_args()


def main():
    args = parse_args()
    github_rows = read_csv(args.github, {"repo"})
    google_rows = read_csv(
        args.google,
        {"tool", "independent_sources", "queries", "decision", "rule", "reason"},
    )
    output_rows = merge_sources(github_rows, google_rows)

    with open(args.output, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(output_rows)

    source_counts = {"github": 0, "google": 0, "github;google": 0}
    for row in output_rows:
        source_counts[row["sources"]] = source_counts.get(row["sources"], 0) + 1

    included_google = sum(row["decision"].strip().casefold() == "include" for row in google_rows)
    print(f"read {len(github_rows)} filtered GitHub rows and {len(google_rows)} screened Google rows")
    print(f"used {included_google} Google rows with decision=include")
    print(f"wrote {len(output_rows)} unique tools to {args.output}")
    print(
        "sources: "
        f"GitHub only={source_counts.get('github', 0)}, "
        f"Google only={source_counts.get('google', 0)}, "
        f"both={source_counts.get('github;google', 0)}"
    )


if __name__ == "__main__":
    main()
