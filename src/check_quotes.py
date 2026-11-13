#!/usr/bin/env python3
"""Check that every quote in an evidence table appears word for word in its saved page.

For each row: the snapshot file must exist, the quote must be at least MIN_LEN characters (an empty quote is a
substring of everything and would pass silently) and must occur in the snapshot once whitespace is collapsed on
both sides.

Run:  python3 src/check_quotes.py                      # results/built_in_metrics.csv against data/raw/doc_snapshots/
      python3 src/check_quotes.py <table.csv> <dir>    # any table with snapshot_file and quote columns
Exit status is 1 if any row fails.
"""
import csv
import re
import sys
from pathlib import Path

from paths import RAW, ROOT

MIN_LEN = 8


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def check(table, snapshots):
    failures = []
    with open(table, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pages = {}
    for i, r in enumerate(rows, 2):  # line numbers as a spreadsheet shows them
        label = f"line {i}: {r.get('tool', '')} | {r.get('metric_name', '')}"
        path = Path(snapshots) / r["snapshot_file"]
        if not r["snapshot_file"] or not path.is_file():
            failures.append(f"{label}: snapshot not found ({r['snapshot_file'] or 'empty'})")
            continue
        if path not in pages:
            pages[path] = squash(path.read_text(encoding="utf-8", errors="replace"))
        quote = squash(r["quote"])
        if len(quote) < MIN_LEN:
            failures.append(f"{label}: quote shorter than {MIN_LEN} characters")
        elif quote not in pages[path]:
            failures.append(f"{label}: quote not in {r['snapshot_file']}: {quote[:70]}")
    return len(rows), failures


def main():
    table = sys.argv[1] if len(sys.argv) > 1 else ROOT / "results" / "built_in_metrics.csv"
    snapshots = sys.argv[2] if len(sys.argv) > 2 else RAW / "doc_snapshots"
    n, failures = check(table, snapshots)
    for line in failures:
        print("FAIL", line)
    print(f"{n} rows checked, {len(failures)} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
