"""Run built-in Phoenix and DeepEval evaluators offline over the turns fetched from Langfuse.

    <example venv python> evaluate_rag.py results/turns_<tag>.json

Writes results/eval_<tag>.csv: one row per tool x metric x turn (or tool call). The judge is gpt-5-mini (OPENAI_API_KEY
from .env next to this file). A judge failure is recorded as a row, not hidden. MAX_EVALS caps metric evaluations.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for line in open(os.path.join(HERE, ".env")):
    k, _, v = line.strip().partition("=")
    if k and v and not k.startswith("#"):
        os.environ.setdefault(k, v.split(" #")[0].strip())

from deepeval.metrics import (AnswerRelevancyMetric, ArgumentCorrectnessMetric, BiasMetric, FaithfulnessMetric,  # noqa: E402
                              KnowledgeRetentionMetric, PIILeakageMetric, TaskCompletionMetric, ToolCorrectnessMetric)
from deepeval.models import OpenAIModel  # noqa: E402
from deepeval.test_case import ConversationalTestCase, LLMTestCase, ToolCall, Turn  # noqa: E402
from phoenix.evals import LLM  # noqa: E402
from phoenix.evals import metrics as pm  # noqa: E402

MODEL = os.environ.get("EXAMPLE_MODEL", "gpt-5-mini")
MAX_EVALS = int(os.environ.get("MAX_EVALS", 300))
ONLY = set(filter(None, os.environ.get("ONLY", "").split(",")))  # e.g. ONLY=UserFriction
rows, n_evals = [], 0


def count():
    global n_evals
    n_evals += 1
    if n_evals > MAX_EVALS:
        raise SystemExit(f"STOPPED: evaluation cap reached ({MAX_EVALS})")


def args_of(t):
    try:
        return json.loads(t["args"]) if isinstance(t["args"], str) else dict(t["args"] or {})
    except Exception:
        return {}


def main(path):
    data = json.load(open(path))
    turns = data["turns"]
    llm = LLM(provider="openai", model=MODEL)
    deep = OpenAIModel(model=MODEL)
    PE = {n: getattr(pm, n + "Evaluator")(llm=llm) for n in [
        "Completeness", "Conciseness", "Faithfulness", "PiiDetection", "Refusal", "ToolInvocation",
        "ToolResponseHandling", "ToolSelection", "Toxicity", "UserFriction"]}

    def phoenix(metric, t, payload):
        if ONLY and metric not in ONLY:
            return
        count()
        try:
            s = PE[metric].evaluate(payload)[0]
            rows.append(["Phoenix", metric, t["scenario"], t["turn"], s.label, s.score, (s.explanation or "")[:300]])
        except Exception as e:
            rows.append(["Phoenix", metric, t["scenario"], t["turn"], "ERROR", "", repr(e)[:300]])

    def deepeval(cls, t, case, **kw):
        if ONLY and cls.__name__.replace("Metric", "") not in ONLY:
            return
        count()
        name = cls.__name__.replace("Metric", "")
        try:
            m = cls(**kw)
            m.measure(case)
            rows.append(["DeepEval", name, t["scenario"], t["turn"], "", m.score, (m.reason or "")[:300]])
        except Exception as e:
            rows.append(["DeepEval", name, t["scenario"], t["turn"], "ERROR", "", repr(e)[:300]])

    history = {}
    for t in turns:
        sid = t["scenario"]
        prev = history.setdefault(sid, [])
        conv = "\n".join(prev + [f"user: {t['question']}", f"assistant: {t['answer']}"])
        context = "\n\n".join(str(x["output"]) for x in t["tools"])
        avail = json.dumps(t["available_tools"])
        phoenix("Refusal", t, {"input": t["question"], "output": t["answer"]})
        phoenix("Toxicity", t, {"text": t["answer"]})
        phoenix("PiiDetection", t, {"conversation": conv})
        prior = "\n".join(prev) or "(no earlier messages)"  # earlier turns only; the latest message is passed separately
        phoenix("UserFriction", t, {"conversation": prior, "user_message": t["question"]})
        phoenix("Completeness", t, {"conversation": conv})
        phoenix("Conciseness", t, {"input": t["question"], "output": t["answer"]})
        if t["tools"]:
            phoenix("Faithfulness", t, {"input": t["question"], "output": t["answer"], "context": context})
            phoenix("ToolResponseHandling", t, {
                "input": t["question"], "output": t["answer"],
                "tool_call": "; ".join(f"{x['name']}({x['args']})" for x in t["tools"]),
                "tool_result": " | ".join(str(x["output"]) for x in t["tools"])})
            for x in t["tools"]:
                call = f"{x['name']}({x['args']})"
                phoenix("ToolSelection", t, {"input": t["question"], "available_tools": avail, "tool_selection": call})
                phoenix("ToolInvocation", t, {"input": t["question"], "available_tools": avail, "tool_selection": call})

        called = [ToolCall(name=x["name"], input_parameters=args_of(x), output=str(x["output"])) for x in t["tools"]]
        case = LLMTestCase(input=t["question"], actual_output=t["answer"], tools_called=called,
                           expected_tools=[ToolCall(name=n) for n in t["expected_tools"]],
                           retrieval_context=[context] if context else None)
        for cls in (TaskCompletionMetric, AnswerRelevancyMetric, BiasMetric, PIILeakageMetric):
            deepeval(cls, t, case, model=deep, async_mode=False, verbose_mode=False)
        if t["tools"]:
            deepeval(FaithfulnessMetric, t, case, model=deep, async_mode=False, verbose_mode=False)
            deepeval(ArgumentCorrectnessMetric, t, case, model=deep, async_mode=False, verbose_mode=False)
        if t["tools"] or t["expected_tools"]:
            deepeval(ToolCorrectnessMetric, t, case)
        prev += [f"user: {t['question']}", f"assistant: {t['answer']}"]

    for sid in dict.fromkeys(t["scenario"] for t in turns):
        ts = [t for t in turns if t["scenario"] == sid]
        if len(ts) >= 3:
            conv = ConversationalTestCase(turns=[Turn(role=r, content=c) for t in ts for r, c in
                                                 (("user", t["question"]), ("assistant", t["answer"]))])
            deepeval(KnowledgeRetentionMetric, {"scenario": sid, "turn": 0}, conv, model=deep, async_mode=False,
                     verbose_mode=False)

    out = path.replace("turns_", "eval_").replace(".json", "_only.csv" if ONLY else ".csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tool", "metric", "scenario", "turn", "label", "score", "explanation"])
        w.writerows(rows)
    print(f"{len(rows)} rows ({sum(r[4] == 'ERROR' for r in rows)} judge errors) -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
