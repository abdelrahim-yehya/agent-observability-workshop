#!/usr/bin/env python3
"""Draw results/metrics_matrix_<tag>.svg: the taxonomy metrics against the three tools used in the RAG run.

    python3 plot_matrix.py results/turns_<tag>.json

Inputs  results/turns_<tag>.json   Langfuse numbers per turn (tokens, cost, latency, tool calls)
        results/eval_<tag>.csv     Phoenix / DeepEval verdicts (cells show "pending" until it exists)
        <repo>/results/metric_taxonomy.csv   the taxonomy (rows)
        <repo>/data/inputs/taxonomy_mapping.csv   evaluator name -> taxonomy metric
Every cell value is computed from those files; nothing is typed in. The picture is drawn by this script.
"""
import csv
import json
import os
import statistics as st
import sys
from collections import defaultdict
from html import escape

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root, parent of example_rag/
COLS = ["Langfuse", "Phoenix evals", "DeepEval"]
TOOL_NAME = {"Phoenix evals": "Arize Phoenix", "DeepEval": "DeepEval"}
# per evaluator: label counted as the "event" and the wording of the cell
PHOENIX = {"ToolSelection": ("correct", "{k}/{n} calls correct"), "ToolInvocation": ("correct", "{k}/{n} calls valid"),
           "ToolResponseHandling": ("correct", "{k}/{n} turns correct"), "Completeness": ("complete", "{k}/{n} turns complete"),
           "Conciseness": ("concise", "{k}/{n} turns concise"), "Faithfulness": ("faithful", "{k}/{n} turns faithful"),
           "Toxicity": ("toxic", "{k}/{n} turns toxic"), "PiiDetection": ("pii_detected", "{k}/{n} turns flagged"),
           "Refusal": ("refused", "{k}/{n} turns refused"), "UserFriction": ("friction", "{k}/{n} turns with friction")}
P2NAME = {"ToolSelection": "Tool Selection", "ToolInvocation": "Tool Invocation", "ToolResponseHandling": "Tool Response Handling",
          "Completeness": "Completeness", "Conciseness": "Conciseness", "Faithfulness": "Faithfulness", "Toxicity": "Toxicity",
          "PiiDetection": "PII Detection", "Refusal": "Refusal", "UserFriction": "User Friction"}
D2NAME = {"TaskCompletion": "Task Completion", "AnswerRelevancy": "Answer Relevancy", "Bias": "Bias", "PIILeakage": "PII Leakage",
          "Faithfulness": "Faithfulness", "ArgumentCorrectness": "Argument Correctness", "ToolCorrectness": "Tool Correctness",
          "KnowledgeRetention": "Knowledge Retention"}


def langfuse_cells(turns):
    tools = [x for t in turns for x in t["tools"]]
    tok = {k: sum(t["tokens"][k] for t in turns) for k in turns[0]["tokens"]}
    cost = {k: sum(t["cost"][k] for t in turns) for k in turns[0]["cost"]}
    llm_lat = [x for t in turns for x in t["llm_latency_s"] if x is not None]
    n_llm = sum(t["llm_calls"] for t in turns)
    errs = sum("ERROR" in str(x["level"]).upper() for x in tools)
    lat = [t["latency_s"] for t in turns]
    return {
        "Tool execution errors": f"{errs} of {len(tools)} tool calls",
        "Tool call count": f"{len(tools)} in {len(turns)} turns",
        "Tool execution latency": f"median {st.median(x['latency'] for x in tools) * 1000:.0f} ms",
        "Input tokens": f"{tok['input']:,.0f}", "Output tokens": f"{tok['output']:,.0f}",
        "Total tokens": f"{tok['total']:,.0f}",
        "Cached tokens": f"{tok['input_cached_tokens']:,.0f}", "Reasoning tokens": f"{tok['output_reasoning_tokens']:,.0f}",
        "Estimated cost": f"${cost['total']:.4f}",
        "Cost breakdown by token type": f"in ${cost['input']:.4f} · out ${cost['output']:.4f} · reasoning ${cost['output_reasoning_tokens']:.4f}",
        "Trace / run latency": f"median {st.median(lat):.1f} s per turn",
        "LLM call latency": f"median {st.median(llm_lat):.1f} s",
        "Span duration": "on every observation",
        "Error count / rate": f"{errs} error observations",
        "Trace / span count": f"{len(turns)} traces, {len(turns) + n_llm + len(tools)} observations",
        "LLM call count": f"{n_llm}",
    }


def eval_cells(path, mapping):
    """taxonomy metric -> {column: text}. Returns None when the CSV does not exist yet."""
    if not os.path.exists(path):
        return None
    groups = defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r["label"] == "ERROR":
            continue
        col = "Phoenix evals" if r["tool"] == "Phoenix" else "DeepEval"
        name = P2NAME.get(r["metric"]) if col == "Phoenix evals" else D2NAME.get(r["metric"])
        metric = mapping.get((TOOL_NAME[col], name))
        if metric:
            groups[(metric, col, r["metric"])].append(r)
    out = defaultdict(dict)
    for (metric, col, ev), rs in groups.items():
        if col == "Phoenix evals":
            good, fmt = PHOENIX[ev]
            text = fmt.format(k=sum(r["label"] == good for r in rs), n=len(rs))
        else:
            sc = [float(r["score"]) for r in rs if r["score"] != ""]
            text = f"mean {st.mean(sc):.2f} over {len(sc)} ({ev})" if sc else ""
        out[metric][col] = (out[metric].get(col, "") + " · " if col in out[metric] else "") + text
    return out


def main(turns_path):
    d = json.load(open(turns_path))
    turns = d["turns"]
    tax = list(csv.DictReader(open(f"{REPO}/results/metric_taxonomy.csv")))
    mapping = {(r["tool"], r["metric_name"]): r["taxonomy_metric"]
               for r in csv.DictReader(open(f"{REPO}/data/inputs/taxonomy_mapping.csv"))}
    lf = langfuse_cells(turns)
    ev = eval_cells(turns_path.replace("turns_", "eval_").replace(".json", ".csv"), mapping)

    ROW, TOP, LEFT, X_NAME, X0, CW, WIDTH = 21, 118, 24, 24, 318, 262, 1130
    metrics = [(r["type"], r["category"], r["metric"]) for r in tax]
    cat_breaks = sum(1 for i, m in enumerate(metrics) if i == 0 or metrics[i - 1][:2] != m[:2])
    height = TOP + len(metrics) * ROW + cat_breaks * 22 + 70

    cell = {}
    for typ, cat, m in metrics:
        row = {}
        if m in lf:
            row["Langfuse"] = lf[m]
        for c in ("Phoenix evals", "DeepEval"):
            if ev is None:
                if typ == "Evaluation" and any(mapping.get((TOOL_NAME[c], n)) == m for n in (P2NAME.values() if c == "Phoenix evals" else D2NAME.values())):
                    row[c] = "pending"
            elif m in ev and c in ev[m]:
                row[c] = ev[m][c]
        cell[m] = row
    n_det = {c: sum(1 for m in cell.values() if c in m and m[c] != "pending") for c in COLS}
    total_obs = sum(1 for t, _, _ in metrics if t == "Observability")
    total_ev = len(metrics) - total_obs
    n_obs = sum(1 for t, _, m in metrics if t == "Observability" and any(c in cell[m] for c in COLS))
    n_ev = sum(1 for t, _, m in metrics if t == "Evaluation" and any(v != "pending" for v in cell[m].values()))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}" role="img" '
         f'aria-label="Taxonomy metrics detected by each tool in the RAG run">',
         "<style>:root{--bg:#fbfaf8;--fg:#1d2328;--muted:#5d666d;--line:#d9d6cf;--obs:#1f6f8b;--ev:#b4582a;--obsf:#dcebf0;--evf:#f4e3d8;--empty:#efede8}",
         "@media (prefers-color-scheme:dark){:root{--bg:#14181b;--fg:#e8ebec;--muted:#98a1a7;--line:#3a444b;--obs:#5cb3d1;--ev:#e08a58;--obsf:#1f3a45;--evf:#47301f;--empty:#22282c}}",
         "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:var(--fg);font-size:12px}.mut{fill:var(--muted)}",
         ".cap{font-size:11px;letter-spacing:.06em;text-transform:uppercase}.cat{font-size:11px;font-weight:600}</style>",
         f'<rect width="{WIDTH}" height="{height}" fill="var(--bg)"/>',
         f'<text x="{LEFT}" y="30" font-size="20" font-family="Georgia,serif">Metrics detected in one RAG run</text>',
         f'<text class="mut" x="{LEFT}" y="50">{len(turns)} questions on {escape(d["model"])}; the app is the course RAG chatbot, traced by Langfuse. '
         f'{n_obs} of {total_obs} Observability and {n_ev} of {total_ev} Evaluation metrics have a value.</text>',
         f'<text class="mut" x="{LEFT}" y="68">Cells show what each tool reported in this run. Blank = the tool reported nothing for that metric. '
         f'Judge: {escape(d["model"])}, unvalidated against human labels. Drawn by plot_matrix.py from the tools\' output.</text>']
    if ev is None:
        o.append(f'<text x="{LEFT}" y="86" fill="#c0392b">Evaluation results not available yet: cells marked pending.</text>')
    for i, c in enumerate(COLS):
        o.append(f'<text class="cap mut" x="{X0 + i * CW}" y="{TOP - 12}">{c}</text>')
    y, last = TOP, None
    for typ, cat, m in metrics:
        if (typ, cat) != last:
            colr = "var(--obs)" if typ == "Observability" else "var(--ev)"
            o.append(f'<text class="cat" x="{X_NAME}" y="{y + 15}" fill="{colr}" style="fill:{colr}">{escape(typ)} · {escape(cat)}</text>')
            y += 22
            last = (typ, cat)
        fillv = "var(--obsf)" if typ == "Observability" else "var(--evf)"
        o.append(f'<text x="{X_NAME + 8}" y="{y + 14}">{escape(m)}</text>')
        for i, c in enumerate(COLS):
            x = X0 + i * CW
            txt = cell[m].get(c)
            if txt:
                o.append(f'<rect x="{x}" y="{y + 1}" width="{CW - 6}" height="{ROW - 3}" rx="3" fill="{fillv}"/>'
                         f'<text x="{x + 6}" y="{y + 14}" style="{"opacity:.55" if txt == "pending" else ""}">{escape(txt[:46])}</text>')
            else:
                o.append(f'<rect x="{x}" y="{y + 1}" width="{CW - 6}" height="{ROW - 3}" rx="3" fill="var(--empty)" opacity=".5"/>')
        y += ROW
    o.append("</svg>")
    out = turns_path.replace("turns_", "metrics_matrix_").replace(".json", ".svg")
    open(out, "w", encoding="utf-8").write("\n".join(o))
    print(f"{out}: Observability {n_obs}/{total_obs}, Evaluation {n_ev}/{total_ev}, per-column values {n_det}, eval csv {'found' if ev is not None else 'missing'}")


if __name__ == "__main__":
    main(sys.argv[1])
