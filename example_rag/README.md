# Motivating example: course RAG chatbot, traced by Langfuse, scored by Phoenix and DeepEval

One run of 12 scripted questions (2026-10-28) through the "Course Materials RAG" chatbot from the DeepLearning.AI course *Claude Code: A Highly Agentic Coding Assistant* (one LLM with two tools, `search_course_content` and `get_course_outline`, over four course transcripts). The app ran on `gpt-5-mini`; its Langfuse instrumentation is the one in the local working copy of that course project. Langfuse recorded tokens, cost, latency and tool calls. Phoenix evals and DeepEval then scored the recorded turns offline, with `gpt-5-mini` as judge. The picture is `results/metrics_matrix_20261028-104817.svg`.

This is a motivating illustration, not an evaluation of the tools: one run, one model as both app and judge, no human labels.

## Files

| File | What it is |
| --- | --- |
| `questions.py` | The 12 questions in 9 sessions, with expected answers taken from the transcripts and written before the run |
| `run_questions.py` | Runs them through the app (needs the course project, not included) |
| `fetch_observations.py` | Assembles one record per turn from Langfuse (v2 observations API) |
| `evaluate_rag.py` | Phoenix and DeepEval evaluators over those records |
| `plot_matrix.py` | Draws the metric-by-tool matrix from the two files above and `results/metric_taxonomy.csv`; reproduces the SVG exactly |
| `export_measured_table.py` | Writes the paper's table of metrics reported in the run (`paper/tables/example_metrics.tex`), same rows and cells as `plot_measured.py` |
| `plot_graph.py` | Draws the paper's Fig. 1, run S7 (the Kubernetes question) as one straight chain of model calls and searches, redrawn from Langfuse's agent graph; the PDF is printed with headless Brave (steps in the docstring) |
| `results/run_*.json` | Answers and sources per question |
| `results/turns_*.json` | Langfuse numbers per turn (tokens, cost, latency, tool calls) |
| `results/eval_*.csv` | Evaluator labels, scores and judge explanations |
| `results/metrics_matrix_*.svg` | The matrix |

## Not included, and why

- The course project and its transcripts (DeepLearning.AI material), `.env` with API keys, and the vector store.
- The retrieved transcript excerpts: tool outputs in `turns_*.json` are replaced by placeholders. `fetch_observations.py` regenerates them from Langfuse, but `evaluate_rag.py` needs the real outputs, so it cannot be rerun from this folder alone.

## Things to know when quoting the results

- `eval_*_before_friction_fix.csv` keeps the first User Friction results, which were wrong: the current turn was passed twice, so the judge read single questions as repeats (3 false positives). `eval_*_only.csv` is the corrected rerun, merged into `eval_*.csv`.
- DeepEval Task Completion scores plain questions as tasks to pose, so a correct answer can score low (for example 0.35 for "What is the capital of Australia?"). One caveat line in the paper covers this.
- One Phoenix Refusal call (S2) timed out and is excluded, so that cell counts 11 turns, not 12.
- On S7 the two Faithfulness evaluators disagree (Phoenix: unfaithful, DeepEval: 1.0); the matrix shows only their aggregates.
- Counts in the Langfuse column (tool calls, LLM calls, observations, errors) are computed from Langfuse observations; tokens, cost and latency are Langfuse's own values.
- The expected answer for S9 turn 3 was first written on a wrong prediction (that the app would forget); `questions.py` carries the corrected version and a comment.
