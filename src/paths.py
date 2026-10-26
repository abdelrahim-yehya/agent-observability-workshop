#!/usr/bin/env python3
"""Single source of truth for pipeline file locations (all relative to the repository root)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUTS = ROOT / "data" / "inputs"      # hand-maintained: Google log/screening, doc registry, human reviews
RAW = ROOT / "data" / "raw"            # unprocessed collection results (GitHub search, downloaded docs)
INTERIM = ROOT / "data" / "interim"    # intermediate, regenerable files
OUTPUTS = ROOT / "data" / "outputs"    # final deliverables

for _directory in (INPUTS, RAW, INTERIM, OUTPUTS):
    _directory.mkdir(parents=True, exist_ok=True)
