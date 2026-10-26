#!/usr/bin/env python3
"""Channel 1 of the tool search protocol (see docs/search_protocol.md): GitHub repositories.

Run:   python github_tool_search.py              -> search GitHub and write unique repositories
       python github_tool_search.py --run-date 2026-10-22 -> fix the activity window to a past run date
       python github_tool_search.py --pypi a b c -> latest PyPI release of packages a, b, c
Token: optional. export GITHUB_TOKEN=... raises the search limit from 10 to 30 requests per minute.

Queries: GitHub REST search API (GET /search/repositories), sort=stars, order=desc, per_page=30.
Every query carries: stars:>=1000 archived:false pushed:>=<run date minus 6 months>.
No repository is added by name: every candidate comes from these queries.
"""
import argparse, csv, datetime, json, os, sys, time, urllib.error, urllib.parse, urllib.request

from paths import RAW

OUTPUT = RAW / "github_raw_results.csv"

TOPICS = ["llm-observability", "llm-evaluation", "llmops", "agent-observability", "agent-evaluation",
          "llm-tracing", "ai-observability", "llm-testing", "llm-eval", "evals"]
KEYWORDS = ['"llm observability"', '"agent observability"', '"llm evaluation"', '"agent evaluation"',
            '"llm tracing"', '"opentelemetry" llm', '"semantic conventions" llm']


def qualifiers(today=None):
    today = today or datetime.date.today()
    six_months_ago = today - datetime.timedelta(days=183)
    return f"stars:>=1000 archived:false pushed:>={six_months_ago.isoformat()}"


def search(q):
    url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
        {"q": q, "sort": "stars", "order": "desc", "per_page": 30})
    headers = {"User-Agent": "agent-metrics-survey", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for _ in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                time.sleep(62)          # rate limited: wait for the window to reset
                continue
            raise
    raise RuntimeError("still rate-limited: " + q)


def run_github(run_date):
    qual = qualifiers(run_date)
    queries = [("G1-topic", f"topic:{t} {qual}") for t in TOPICS] + \
              [("G2-keyword", f"{k} in:name,description,readme {qual}") for k in KEYWORDS]
    rows = []
    seen_repos = set()
    duplicate_count = 0
    for group, q in queries:
        d = search(q)
        for i in d.get("items", []):
            repo_key = i["full_name"].strip().casefold()
            if repo_key in seen_repos:
                duplicate_count += 1
                continue
            seen_repos.add(repo_key)
            rows.append({"run_date": run_date.isoformat(), "group": group, "query": q,
                         "repo": i["full_name"], "stars": i["stargazers_count"],
                         "last_push": i["pushed_at"][:10], "license": (i.get("license") or {}).get("spdx_id"),
                         "description": (i.get("description") or "")[:150]})
        print(f"{group:10} {d.get('total_count', 0):>4} hits  {q}")
        time.sleep(6.5)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {OUTPUT}: {len(rows)} unique repositories "
          f"({duplicate_count} duplicate hits skipped)")


def run_pypi(packages):
    """Maintenance check for tools that passed selection: latest release date on PyPI."""
    for p in packages:
        try:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{p}/json", timeout=30) as r:
                d = json.loads(r.read())
            rel = sorted((f["upload_time"][:10], v) for v, fs in d["releases"].items() for f in fs[:1])
            print(f"{p:36} {rel[-1][1]} ({rel[-1][0]})")
        except Exception as e:
            print(f"{p:36} not found ({e})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--pypi":
        run_pypi(sys.argv[2:])
    else:
        parser = argparse.ArgumentParser(description="GitHub channel of the tool search protocol.")
        parser.add_argument("--run-date", type=datetime.date.fromisoformat, default=datetime.date.today(),
                            help="ISO date the six-month activity window is measured from (default: today)")
        run_github(parser.parse_args().run_date)
