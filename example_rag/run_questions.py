"""Run every scripted session through the course RAG app; traces go to Langfuse.

    <course venv python> run_questions.py [S1 S3 ...]

Writes results/run_<tag>.json (answer, sources and the Langfuse session id per turn). Langfuse is the source of
truth for the metrics; this file only links each question to its session.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(os.path.join(HERE, "backend"))
sys.path.insert(0, os.getcwd())

from langfuse import get_client  # noqa: E402

from config import config  # noqa: E402
from rag_system import RAGSystem  # noqa: E402

sys.path.insert(0, HERE)
from questions import SESSIONS  # noqa: E402

MAX_QUERIES = int(os.environ.get("MAX_QUERIES", 20))


def main(wanted):
    tag = time.strftime("%Y%m%d-%H%M%S")
    rag = RAGSystem(config)
    rag.add_course_folder("../docs", clear_existing=False)
    print(f"provider={config.LLM_PROVIDER} model={config.OPENAI_MODEL if config.LLM_PROVIDER == 'openai' else config.OLLAMA_MODEL} tag={tag}")
    rows, n = [], 0
    for sid in wanted:
        session = f"{tag}-{sid}"
        for turn, item in enumerate(SESSIONS[sid], start=1):
            n += 1
            if n > MAX_QUERIES:
                sys.exit(f"query cap reached ({MAX_QUERIES})")
            t0 = time.perf_counter()
            answer, sources, _ = rag.query(item["q"], session_id=session)
            rows.append({"scenario": sid, "turn": turn, "session_id": session, "question": item["q"],
                         "answer": answer, "sources": sources, "seconds": round(time.perf_counter() - t0, 1),
                         "expected": item["expected"], "expected_tools": item["expected_tools"]})
            print(f"[{sid} t{turn}] {item['q']}\n    -> {answer[:160]!r}")
    get_client().flush()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", f"run_{tag}.json")
    json.dump({"tag": tag, "model": config.OPENAI_MODEL, "rows": rows}, open(out, "w"), indent=1)
    print(f"{len(rows)} queries -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:] or list(SESSIONS))
