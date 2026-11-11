"""Assemble one record per conversation turn from Langfuse (v2 observations API).

    <course venv python> fetch_observations.py results/run_<tag>.json

Writes results/turns_<tag>.json: question, answer, tool calls (name, args, output, level), per-turn usage/cost/latency
as Langfuse computed them, and our expected answer. Evaluators read this file, never the app's own return values.
"""
import json
import os
import sys

from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(HERE, ".env"))
sys.path.insert(0, HERE)
from langfuse import get_client  # noqa: E402

from questions import SESSIONS  # noqa: E402


def num(d, k):
    return float((d or {}).get(k) or 0)


def main(run_path):
    run = json.load(open(run_path))
    lf = get_client()
    turns = []
    for session in dict.fromkeys(r["session_id"] for r in run["rows"]):
        obs = lf.api.observations.get_many(session_id=session, limit=200, fields="core,basic,io,usage,time").data
        by_trace = {}
        for o in obs:
            by_trace.setdefault(o.trace_id, []).append(o)
        roots = sorted((o for o in obs if o.type == "AGENT"), key=lambda o: o.start_time)
        rows = [r for r in run["rows"] if r["session_id"] == session]
        assert len(roots) == len(rows), f"{session}: {len(roots)} traces in Langfuse, {len(rows)} asked"
        for turn, (root, row) in enumerate(zip(roots, rows), start=1):
            kids = sorted((o for o in by_trace[root.trace_id] if o.id != root.id), key=lambda o: o.start_time)
            gens = [o for o in kids if o.type == "GENERATION"]
            tools = [{"name": o.name, "args": o.input, "output": o.output, "level": str(o.level), "latency": o.latency}
                     for o in kids if o.type == "TOOL"]
            avail = []
            if gens and isinstance(gens[0].input, (str, dict)):
                g = json.loads(gens[0].input) if isinstance(gens[0].input, str) else gens[0].input
                avail = [t["function"] for t in g.get("tools", [])] if isinstance(g, dict) else []
            u = [g.usage_details or {} for g in gens]
            c = [g.cost_details or {} for g in gens]
            turns.append({
                "scenario": row["scenario"], "turn": turn, "session_id": session, "trace_id": root.trace_id,
                "question": root.input, "answer": root.output,
                "expected": SESSIONS[row["scenario"]][turn - 1]["expected"],
                "expected_tools": SESSIONS[row["scenario"]][turn - 1]["expected_tools"],
                "available_tools": avail, "tools": tools,
                "latency_s": root.latency, "llm_calls": len(gens), "llm_latency_s": [g.latency for g in gens],
                "tokens": {k: sum(num(x, k) for x in u) for k in
                           ("input", "output", "total", "input_cached_tokens", "output_reasoning_tokens")},
                "cost": {k: sum(num(x, k) for x in c) for k in
                         ("input", "output", "total", "input_cached_tokens", "output_reasoning_tokens")},
            })
    out = run_path.replace("run_", "turns_")
    json.dump({"tag": run["tag"], "model": run["model"], "turns": turns}, open(out, "w"), indent=1, default=str)
    print(f"{len(turns)} turns -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
