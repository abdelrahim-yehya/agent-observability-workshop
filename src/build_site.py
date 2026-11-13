#!/usr/bin/env python3
"""Build the companion website: the taxonomy, the catalogue of unique metrics with definitions and evidence, the
tool x metric coverage table and the selected tools, as one self-contained page.

Inputs:  results/metric_taxonomy.csv           (the 46 unique metrics: type, category, definition)
         results/standards_only_metrics.csv    (the metric only standards document)
         results/tool_metric_matrix_long.csv   (status of every tool x metric cell)
         results/built_in_metrics.csv          (evidence rows: tool-specific name, description, quote, URL, date)
         data/inputs/taxonomy_mapping.csv      (evidence row -> unique metric)
         results/best_tools.csv + data/outputs/open_source_adoption_candidates.csv  (through build_tool_table.grouped)
Output:  site/index.html   (no build step and no dependencies; the only external request is the web font)
Run:     python3 src/build_taxonomy.py && python3 src/build_matrix.py && python3 src/build_site.py

Everything on the page that is a count, a name, a definition, a quote or a link is read from the data. The prose
(introduction, category glosses, method summary and the selection funnel) is written here and follows the paper;
update it when the paper changes. `render()` returns the page as (head, body) so it can also be embedded elsewhere.
"""
import csv
import re
from datetime import date
from html import escape
from urllib.parse import urlparse

from build_tool_table import OTEL, fmt_dl, grouped
from paths import INPUTS, ROOT

RESULTS = ROOT / "results"
OUT = ROOT / "site" / "index.html"
REPO_URL = "https://github.com/abdelrahim-yehya/agent-observability-workshop"
SNAPSHOT_URL = REPO_URL + "/blob/master/data/raw/doc_snapshots/"
TITLE = "Agent Metrics Catalogue"
PAPER_TITLE = "A Catalogue of Observability and Evaluation Metrics for AI Agents"
ADOPTION_READ = "6 Nov 2026"  # stars and downloads, see build_tool_table.py

LABEL = {"DeepEval": "DeepEval (with Confident AI)"}
SHORT = {"Weights & Biases Weave": "W&B Weave"}
GROUPS = [("Open-source tools", "open", "Open source"), ("Closed-source tools", "closed", "Closed source"),
          ("Standards", "standard", "Standards")]
GROUP_NOTE = {
    "open": "Selected by adoption: at least 5,000 GitHub stars or one million downloads in 30 days. Listed by downloads.",
    "closed": "Selected by corroboration: named by at least two independent sources in the search results. "
              "Listed by number of sources.",
    "standard": "Telemetry conventions and instrumentation libraries. They name what a trace contains; "
                "the tools above are built on them or accept their traces.",
}
ROLE = {
    "platform": "Platform: stores and shows traces, with evaluation or monitoring on top",
    "framework": "Framework: runs evaluations, with no trace storage of its own",
    "standard": "Standard: telemetry conventions or a library that emits them",
}
OTEL_TEXT = {
    "built on": "built on it", "accepts": "accepts its traces", "optional": "optional tracing with it",
    "span-like": "data modelled like its spans", "not found": "no link found in the pages read",
    "defines": "defines the conventions",
}
CAT_GLOSS = {
    ("Observability", "Tool use"): "What happened to the tool calls.",
    ("Observability", "Plan and trajectory"): "The sequence of steps.",
    ("Observability", "Token usage"): "What the model consumed and produced.",
    ("Observability", "Cost"): "What the run cost.",
    ("Observability", "Latency"): "How long the run and its parts took.",
    ("Observability", "Errors and volume"): "How many runs, calls and failures.",
    ("Evaluation", "Tool use"): "Whether the tool calls were the right ones.",
    ("Evaluation", "Task and goal"): "Whether the agent did what was asked.",
    ("Evaluation", "Plan and trajectory"): "Whether the sequence of steps was a good one.",
    ("Evaluation", "Answer quality"): "How good the final answer is.",
    ("Evaluation", "Grounding"): "Whether the answer stays within its sources.",
    ("Evaluation", "Safety and policy"): "Harmful, private or disallowed content.",
    ("Evaluation", "Conversation"): "Properties of a multi-turn exchange.",
}
# The selection funnel, as reported in the paper (Table "From search results to the selected tools").
FUNNEL = [
    ("GitHub repositories returned by 17 queries", "182"),
    ("Tools named in the first 30 results of 6 Google queries", "68"),
    ("Candidates after screening and merging both lists", "42"),
    ("Primary purpose is observability or evaluation of LLM applications or agents", "31"),
    ("Documentation explicitly covers agents, tool calls or multi-step traces", "30"),
    ("Selected by adoption (open source) or corroboration (closed source)", "13 tools, 3 standards"),
]
STATUS_TEXT = {
    "built-in": "Built-in",
    "integration": "Through an integration",
    "community": "Community-contributed",
    "template": "Documented as a template to copy",
    "generic custom": "Not shipped. The tool has user-defined evaluators, so it can be built.",
    "records scores": "Not shipped. The tool stores scores computed elsewhere.",
    "not documented": "Nothing found in the pages read.",
}
STATUS_CLASS = {"built-in": "s-built", "integration": "s-via", "community": "s-via", "template": "s-via",
                "generic custom": "s-diy", "records scores": "s-diy", "not documented": "s-none"}


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def slug(s):
    return "m-" + re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def nice_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {date(y, m, d):%b} {y}"


def e(s):
    return escape(str(s), quote=True)


# ----------------------------------------------------------------------------------------------------------------
# Data
# ----------------------------------------------------------------------------------------------------------------
def load():
    tools = []
    for gname, key, _ in GROUPS:
        for t, b, stars, dl, sources in grouped()[gname]:
            tools.append(dict(name=t, label=LABEL.get(t, t), short=SHORT.get(t, t), group=key, role=b["role"],
                              stars=stars, downloads=dl, sources=sources, otel=OTEL[t], docs=b["a1_url"],
                              repo=b["github_repo"]))
    names = [t["name"] for t in tools]
    cells = {(r["metric"], r["tool"]): r for r in read(RESULTS / "tool_metric_matrix_long.csv")}
    built = {(r["tool"], r["metric_name"]): r for r in read(RESULTS / "built_in_metrics.csv")}
    evidence = {}
    for m in read(INPUTS / "taxonomy_mapping.csv"):
        evidence.setdefault(m["taxonomy_metric"], {}).setdefault(m["tool"], []).append(built[(m["tool"], m["metric_name"])])

    def metric(row, standards_only=False):
        name = row["metric"]
        ev = evidence.get(name, {})
        status = {t: (cells[(name, t)]["status"] if (name, t) in cells else ("built-in" if t in ev else "not documented"))
                  for t in names}
        assert all((status[t] == "built-in") == (t in ev) for t in names), f"evidence and matrix disagree on {name}"
        return dict(name=name, id=slug(name), type=row["type"], category=row["category"], definition=row["definition"],
                    evidence=ev, status=status, cells={t: cells.get((name, t)) for t in names},
                    standards_only=standards_only)

    metrics = [metric(r) for r in read(RESULTS / "metric_taxonomy.csv")]
    extra = [metric(r, standards_only=True) for r in read(RESULTS / "standards_only_metrics.csv")]
    dates = sorted(r["access_date"] for r in built.values())
    return dict(tools=tools, metrics=metrics, extra=extra, n_rows=len(built), first=dates[0], last=dates[-1],
                n_pairs=sum(len(v) for ev in evidence.values() for v in ev.values()))


def supporters(m, tools, standards):
    return [t for t in tools if (t["group"] == "standard") == standards and m["status"][t["name"]] == "built-in"]


# ----------------------------------------------------------------------------------------------------------------
# Sections
# ----------------------------------------------------------------------------------------------------------------
def by_type_and_category(metrics):
    out = {}
    for m in metrics:
        out.setdefault(m["type"], {}).setdefault(m["category"], []).append(m)
    return out


def hero(d):
    n_obs = sum(m["type"] == "Observability" for m in d["metrics"])
    n_tools = sum(t["group"] != "standard" for t in d["tools"])
    n_std = len(d["tools"]) - n_tools
    n_cat = len({(m["type"], m["category"]) for m in d["metrics"]})
    return f"""
<section class="hero" id="intro"><div class="wrap">
  <p class="kicker">Research catalogue. Documentation read between {nice_date(d['first'])} and {nice_date(d['last'])}.</p>
  <h1>{e(PAPER_TITLE)}</h1>
  <p class="lede">Tools that trace and evaluate AI agents each ship their own metrics, under their own names. We read the
  documentation of {n_tools} tools and the {n_std} telemetry standards beneath them, recorded every metric they ship out of
  the box, and merged the equivalent ones into {len(d['metrics'])} unique metrics. Each one is defined here and linked to the
  pages that document it.</p>
  <dl class="facts">
    <div><dt>{len(d['metrics'])}</dt><dd>unique metrics: {n_obs} observability, {len(d['metrics']) - n_obs} evaluation</dd></div>
    <div><dt>{n_cat}</dt><dd>categories, by the part of the run a metric is about</dd></div>
    <div><dt>{n_tools} + {n_std}</dt><dd>tools and the standards beneath them</dd></div>
    <div><dt>{d['n_rows']}</dt><dd>built-in metrics found, each with a quote and a link</dd></div>
  </dl>
</div></section>"""


def taxonomy(d):
    tools = d["tools"]
    n_tools = sum(t["group"] != "standard" for t in tools)
    cols = []
    for typ, cats in by_type_and_category(d["metrics"]).items():
        cls = "obs" if typ == "Observability" else "eval"
        what = ("Values captured from a run, or derived from what was captured." if cls == "obs"
                else "Scores: judgements of the agent's behaviour or output, by a rule, a model or a person.")
        n = sum(len(v) for v in cats.values())
        parts = [f'<div class="{cls}"><h3><span class="sw"></span>{typ} <span class="count">{n} metrics</span></h3>'
                 f'<p class="gloss">{what}</p>']
        for cat, ms in cats.items():
            parts.append(f'<div class="cat"><h4>{e(cat)}</h4><p class="gloss">{e(CAT_GLOSS[(typ, cat)])}</p><ul>')
            for m in ms:
                k = len(supporters(m, tools, False))
                parts.append(
                    f'<li><a href="#{m["id"]}">{e(m["name"])}</a>'
                    f'<span class="bar" role="img" aria-label="{k} of {n_tools} tools"><i style="width:{100 * k / n_tools:.1f}%"></i></span>'
                    f'<span class="num">{k}</span></li>')
            parts.append("</ul></div>")
        parts.append("</div>")
        cols.append("".join(parts))
    return f"""
<section id="taxonomy"><div class="wrap">
  <h2>Taxonomy</h2>
  <p class="intro">Every metric is classified on two levels. The <em>type</em> says where its value comes from: it is
  either recorded during the run or assigned afterwards by a judge. The <em>category</em> says which part of the run it
  is about. Tool use and plan and trajectory appear under both types, because the same part of a run can be counted or
  judged.</p>
  <p class="key">Bars show how many of the {n_tools} tools ship the metric (standards are not counted). Select a metric
  to open its entry.</p>
  <div class="tax">{''.join(cols)}</div>
</div></section>"""


def evidence_block(m, tools):
    parts = []
    for t in tools:
        rows = m["evidence"].get(t["name"])
        if not rows:
            continue
        parts.append(f'<div class="ev-tool"><h5>{e(t["label"])}</h5>')
        for r in rows:
            meta = [e(r["delivery"])]
            if r["how_measured"] not in ("not stated", "telemetry"):
                meta.append("measured by " + e(r["how_measured"]))
            host = urlparse(r["doc_url"]).netloc.removeprefix("www.")
            meta.append(f'<a href="{e(r["doc_url"])}" target="_blank" rel="noopener">{e(host)}</a>, read {nice_date(r["access_date"])}')
            if r["snapshot_file"]:
                meta.append(f'<a href="{e(SNAPSHOT_URL + r["snapshot_file"])}" target="_blank" rel="noopener">saved copy</a>')
            parts.append(
                f'<div class="ev"><div class="ev-name">{e(r["metric_name"])}</div>'
                f'<p class="ev-desc">{e(r["description"])}</p>'
                f'<blockquote>{e(r["quote"])}</blockquote>'
                f'<p class="ev-meta">{" · ".join(meta)}</p></div>')
        parts.append("</div>")
    # What the other tools offer for this metric.
    other = {}
    for t in tools:
        s = m["status"][t["name"]]
        if s != "built-in":
            other.setdefault(s, []).append(t)
    lines = []
    for s in ("integration", "community", "template", "generic custom", "records scores", "not documented"):
        if s not in other:
            continue
        items = []
        for t in other[s]:
            c = m["cells"][t["name"]] or {}
            if c.get("doc_url"):
                items.append(f'{e(t["short"])} (<a href="{e(c["doc_url"])}" target="_blank" rel="noopener">{e(c["tool_specific_names"])}</a>)')
            else:
                items.append(e(t["short"]))
        lines.append(f'<li><span class="st">{e(STATUS_TEXT[s])}</span> {", ".join(items)}</li>')
    if lines:
        parts.append(f'<div class="others"><h5>The other tools</h5><ul>{"".join(lines)}</ul></div>')
    return "".join(parts)


def entry(m, tools, n_tools):
    sup, std = supporters(m, tools, False), supporters(m, tools, True)
    cls = "obs" if m["type"] == "Observability" else "eval"
    chips = "".join(f'<span class="chip">{e(t["short"])}</span>' for t in sup)
    chips += "".join(f'<span class="chip std" title="Standard">{e(t["short"])}</span>' for t in std)
    count = "standards only" if m["standards_only"] else f"{len(sup)} of {n_tools} tools"
    names = " ".join(r["metric_name"] for rows in m["evidence"].values() for r in rows)
    text = " ".join([m["name"], m["definition"], m["category"], m["type"], names] + [t["label"] for t in sup + std]).lower()
    return (
        f'<details class="metric {cls}{" extra" if m["standards_only"] else ""}" id="{m["id"]}" data-type="{m["type"]}" '
        f'data-cat="{e(m["type"] + "|" + m["category"])}" data-tools="{e("|".join(t["name"] for t in sup + std))}" '
        f'data-text="{e(text)}">'
        f'<summary><span class="m-name">{e(m["name"])}</span>'
        f'<span class="m-main"><span class="m-def">{e(m["definition"])}</span><span class="chips">{chips}</span></span>'
        f'<span class="m-n">{count}</span></summary>'
        f'<div class="m-body">{evidence_block(m, tools)}</div></details>')


def catalogue(d):
    tools = d["tools"]
    n_tools = sum(t["group"] != "standard" for t in tools)
    groups = []
    for typ, cats in by_type_and_category(d["metrics"]).items():
        cls = "obs" if typ == "Observability" else "eval"
        parts = [f'<div class="type-group {cls}"><h3><span class="sw"></span>{typ} metrics</h3>']
        for cat, ms in cats.items():
            parts.append(f'<div class="cat-group"><h4>{e(cat)}</h4>' + "".join(entry(m, tools, n_tools) for m in ms) + "</div>")
        parts.append("</div>")
        groups.append("".join(parts))
    extra = "".join(entry(m, tools, n_tools) for m in d["extra"])
    cat_options = "".join(
        f'<optgroup label="{typ}">' + "".join(f'<option value="{e(typ + "|" + c)}">{e(c)}</option>' for c in cats) + "</optgroup>"
        for typ, cats in by_type_and_category(d["metrics"]).items())
    tool_options = "".join(
        f'<optgroup label="{label}">' + "".join(f'<option value="{e(t["name"])}">{e(t["label"])}</option>'
                                                 for t in tools if t["group"] == key) + "</optgroup>"
        for _, key, label in GROUPS)
    return f"""
<section id="catalogue"><div class="wrap">
  <h2>Catalogue</h2>
  <p class="intro">The {len(d['metrics'])} unique metrics, with our definition of each and the tools that ship it. Open an
  entry to see what each tool calls the metric, what it measures there, the sentence of its documentation we rely on
  and the page it comes from.</p>
  <form class="filters" id="filters" role="search" aria-label="Filter the catalogue">
    <div class="field grow"><label for="q">Search</label>
      <input type="search" id="q" placeholder="faithfulness, tokens, gen_ai.usage, tool call" autocomplete="off"></div>
    <div class="field"><span class="lab" id="lab-type">Type</span>
      <div class="seg" role="radiogroup" aria-labelledby="lab-type">
        <label><input type="radio" name="f-type" id="f-type-all" value="" checked><span>All</span></label>
        <label><input type="radio" name="f-type" id="f-type-obs" value="Observability"><span>Observability</span></label>
        <label><input type="radio" name="f-type" id="f-type-eval" value="Evaluation"><span>Evaluation</span></label>
      </div></div>
    <div class="field"><label for="f-cat">Category</label>
      <select id="f-cat"><option value="">All categories</option>{cat_options}</select></div>
    <div class="field"><label for="f-tool">Shipped by</label>
      <select id="f-tool"><option value="">Any tool or standard</option>{tool_options}</select></div>
  </form>
  <p class="result"><span id="count">All {len(d['metrics'])} metrics</span>
    <button type="button" class="link" id="clear" hidden>Clear filters</button></p>
  <p class="empty" id="none" hidden>No metric matches these filters.</p>
  {''.join(groups)}
  <div class="type-group obs" id="standards-only"><h3><span class="sw"></span>Documented only by standards</h3>
    <p class="gloss">Not one of the {len(d['metrics'])}: no studied tool ships it, but the standards define it.</p>
    <div class="cat-group">{extra}</div></div>
</div></section>"""


def matrix(d):
    tools = d["tools"]
    n_tools = sum(t["group"] != "standard" for t in tools)
    first = {}  # first tool of each group gets a separator
    for t in tools:
        first.setdefault(t["group"], t["name"])
    g0 = set(first.values())
    spans = "".join(f'<th class="grp g0" colspan="{sum(t["group"] == key for t in tools)}" scope="colgroup">{label}</th>'
                    for _, key, label in GROUPS)
    heads = "".join(f'<th class="col{" g0" if t["name"] in g0 else ""}" scope="col"><span>{e(t["short"])}</span></th>' for t in tools)
    body, counts = [], {}
    for typ, cats in by_type_and_category(d["metrics"]).items():
        cls = "obs" if typ == "Observability" else "eval"
        for cat, ms in cats.items():
            body.append(f'<tr class="cat {cls}"><th colspan="{len(tools) + 2}" scope="colgroup"><span class="sw"></span>{typ}: {e(cat)}</th></tr>')
            for m in ms:
                tds = []
                for t in tools:
                    s = m["status"][t["name"]]
                    counts[s] = counts.get(s, 0) + 1
                    c = m["cells"][t["name"]] or {}
                    names = c.get("tool_specific_names", "").replace(" | ", ", ")
                    tip = f'{t["label"]}: {m["name"]}\n{STATUS_TEXT[s]}' + (f": {names}" if names else "")
                    tds.append(f'<td class="{STATUS_CLASS[s]}{" g0" if t["name"] in g0 else ""}" data-tip="{e(tip)}">'
                               f'<span class="dot"></span><span class="sr">{e(STATUS_TEXT[s])}</span></td>')
                body.append(f'<tr class="{cls}"><th class="row" scope="row"><a href="#{m["id"]}">{e(m["name"])}</a></th>'
                            f'{"".join(tds)}<td class="n g0">{len(supporters(m, tools, False))}</td></tr>')
    total = sum(counts.values())
    via = counts.get("integration", 0) + counts.get("template", 0) + counts.get("community", 0)
    diy = counts.get("generic custom", 0) + counts.get("records scores", 0)
    return f"""
<section id="matrix"><div class="wrap">
  <h2>Coverage</h2>
  <p class="intro">Every metric against every tool and standard. A filled dot means the tool's documentation presents
  the metric as shipped, with no code to write. Of the {total} cells, {counts.get('built-in', 0)} are built-in, {via} are
  reached through an integration or a template, {diy} can be built or stored but are not shipped, and for
  {counts.get('not documented', 0)} we found nothing.</p>
  <ul class="legend">
    <li class="s-built"><span class="dot"></span>Built-in</li>
    <li class="s-via"><span class="dot"></span>Through an integration or a documented template</li>
    <li class="s-diy"><span class="dot"></span>Not shipped: the tool lets you define it, or stores scores computed elsewhere</li>
    <li class="s-none"><span class="blank"></span>Nothing found in the pages read, which is not proof the tool lacks it</li>
  </ul>
  <div class="mx-wrap" tabindex="0" role="region" aria-label="Coverage table, scrolls sideways">
  <table class="mx">
    <thead>
      <tr><th class="corner" rowspan="2" scope="col">Metric</th>{spans}<th class="grp g0" rowspan="2" scope="col"><span class="of">Tools<br>of {n_tools}</span></th></tr>
      <tr>{heads}</tr>
    </thead>
    <tbody>{''.join(body)}</tbody>
  </table></div>
</div></section>"""


def tools_section(d):
    tools, metrics = d["tools"], d["metrics"]
    n_obs = sum(m["type"] == "Observability" for m in metrics)
    n_eval = len(metrics) - n_obs
    out = []
    for _, key, label in GROUPS:
        cards = []
        for t in (t for t in tools if t["group"] == key):
            obs = sum(m["type"] == "Observability" and m["status"][t["name"]] == "built-in" for m in metrics)
            ev = sum(m["type"] == "Evaluation" and m["status"][t["name"]] == "built-in" for m in metrics)
            facts = []
            if t["stars"]:
                facts.append(("GitHub stars", f'{t["stars"]:,}'))
            if t["downloads"]:
                facts.append(("Downloads, 30 days", fmt_dl(t["downloads"])))
            facts.append(("Independent sources", str(t["sources"])))
            facts.append(("OpenTelemetry", OTEL_TEXT[t["otel"]]))
            links = [f'<a href="{e(t["docs"])}" target="_blank" rel="noopener">Documentation</a>']
            if t["repo"]:
                links.append(f'<a href="https://github.com/{e(t["repo"])}" target="_blank" rel="noopener">GitHub</a>')
            cards.append(
                f'<article class="tool"><div><h4>{e(t["label"])}</h4><p class="role">{e(ROLE[t["role"]])}</p></div>'
                f'<div class="cov">'
                f'<span>Observability</span><span class="bar obs" role="img" aria-label="{obs} of {n_obs}"><i style="width:{100 * obs / n_obs:.1f}%"></i></span><span class="num">{obs} of {n_obs}</span>'
                f'<span>Evaluation</span><span class="bar eval" role="img" aria-label="{ev} of {n_eval}"><i style="width:{100 * ev / n_eval:.1f}%"></i></span><span class="num">{ev} of {n_eval}</span>'
                f'</div>'
                f'<dl>{"".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in facts)}</dl>'
                f'<p class="acts"><button type="button" class="link" data-show-tool="{e(t["name"])}">See its metrics</button>{"".join(links)}</p>'
                f'</article>')
        out.append(f'<div class="tool-group"><h3>{label} <span class="count">{len(cards)}</span></h3>'
                   f'<p class="gloss">{GROUP_NOTE[key]}</p><div class="tools">{"".join(cards)}</div></div>')
    return f"""
<section id="tools"><div class="wrap">
  <h2>Tools</h2>
  <p class="intro">The tools whose documentation we read, and how many of the unique metrics each one ships. The two
  groups of tools rest on different evidence and are not ranked against each other. Stars and downloads were read on
  {ADOPTION_READ}. The number of metrics is not a quality score: some tools document every prompt template, others a
  few broad metrics.</p>
  {''.join(out)}
</div></section>"""


def method(d):
    rows = "".join(f"<tr><td>{e(a)}</td><td class='num'>{e(b)}</td></tr>" for a, b in FUNNEL)
    return f"""
<section id="method"><div class="wrap">
  <h2>Method</h2>
  <div class="cols">
    <div>
      <h3>Choosing the tools</h3>
      <p>Most tools are documented in repositories, vendor pages and blogs, so we searched GitHub and Google with fixed
      queries on 22 Oct 2026 and screened the results by hand against written inclusion and exclusion rules. The
      OpenTelemetry conventions for generative AI were added by hand, since a standard has no product page for such
      queries to rank.</p>
      <table class="funnel"><tbody>{rows}</tbody></table>
    </div>
    <div>
      <h3>Collecting the metrics</h3>
      <p>For each tool we read the official documentation and recorded every built-in metric: one the tool itself
      ships, as opposed to a metric the user writes, a community contribution or one reached through an integration.
      We kept the metrics that describe how an agent run executes or how good its output is. Each of the
      {d['n_rows']} rows stores the page, a verbatim quote, a saved copy of the page and the date, and a script checks
      that every quote appears word for word in the saved copy.</p>
      <h3>Merging them</h3>
      <p>Two metrics from different tools become one unique metric when they measure the same thing about the same
      object, whatever the tools call them. The mapping ({d['n_pairs']} pairs) is made by hand. The definitions on this
      site are ours, not quotations.</p>
    </div>
    <div>
      <h3>Reading the catalogue with care</h3>
      <ul class="care">
        <li>Tools that share a unique metric may compute it differently, and can disagree on the same run.</li>
        <li>An empty cell means we found nothing in the pages we read. It does not prove the tool lacks the metric.</li>
        <li>Documentation changes. Every quote carries the date its page was read.</li>
        <li>Text-match and format checks, retrieval scores, audio, voice and image metrics and task-specific metrics
        are out of scope.</li>
        <li>Closed-source tools that the search results did not name are absent.</li>
      </ul>
    </div>
  </div>
</div></section>"""


# ----------------------------------------------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------------------------------------------
CSS = r"""
/* Layout: a reference work in one centred column. A sticky contents bar, a short statement of what was done,
   then four working views of the same data (taxonomy, catalogue, coverage, tools) and the method. */
:root{
  --bg:#f6f8f9; --surface:#ffffff; --ink:#15212a; --ink-2:#465763; --ink-3:#6c7c87; --rule:#d5dde3; --rule-2:#e7ecef;
  --obs:#0f7a9e; --eval:#b4582a; --obs-tint:#e0eff5; --eval-tint:#f7e9e0; --link:#0b5f7c;
  --display:"IBM Plex Serif", Georgia, "Times New Roman", serif;
  --body:"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0f161b; --surface:#162027; --ink:#e7eef2; --ink-2:#aebcc5; --ink-3:#8494a0; --rule:#2c3b45; --rule-2:#202d35;
    --obs:#2f9cc0; --eval:#d6743f; --obs-tint:#12313d; --eval-tint:#3c2619; --link:#74c4e0; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0f161b; --surface:#162027; --ink:#e7eef2; --ink-2:#aebcc5; --ink-3:#8494a0; --rule:#2c3b45; --rule-2:#202d35;
  --obs:#2f9cc0; --eval:#d6743f; --obs-tint:#12313d; --eval-tint:#3c2619; --link:#74c4e0; color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 var(--body); -webkit-text-size-adjust:100%}
body::before{content:""; position:fixed; inset:0 0 auto; height:env(safe-area-inset-top, 0px); z-index:30; background:var(--bg)}
.wrap{max-width:1120px; margin-inline:auto; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px))}
@media (min-width:720px){ .wrap{padding-left:max(32px, env(safe-area-inset-left, 0px)); padding-right:max(32px, env(safe-area-inset-right, 0px))} }
a{color:var(--link); text-underline-offset:2px}
:focus-visible{outline:2px solid var(--obs); outline-offset:2px; border-radius:2px}
h1,h2,h3,h4,h5,p,ul,dl{margin:0}
.obs{--c:var(--obs); --t:var(--obs-tint)} .eval{--c:var(--eval); --t:var(--eval-tint)}
.sw{display:inline-block; flex:none; width:10px; height:10px; border-radius:2px; background:var(--c)}
.sr{position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap}
.num{font:500 13px var(--mono); font-variant-numeric:tabular-nums; color:var(--ink-2); white-space:nowrap}
.count{font:400 14px var(--body); color:var(--ink-3)}
.gloss{font-size:14px; color:var(--ink-3)}
button.link{font:inherit; color:var(--link); background:none; border:0; padding:0; cursor:pointer; text-decoration:underline; text-underline-offset:2px}

.top{position:sticky; top:env(safe-area-inset-top, 0px); z-index:20; background:var(--bg); border-bottom:1px solid var(--rule)}
.top .wrap{display:flex; align-items:center; gap:28px; min-height:52px}
.brand{font:600 17px var(--display); color:var(--ink); text-decoration:none; white-space:nowrap}
.top nav{display:flex; gap:22px; overflow-x:auto; min-width:0; font-size:14.5px; scrollbar-width:none}
.top nav a{color:var(--ink-2); text-decoration:none; white-space:nowrap; padding:6px 0}
.top nav a:hover{color:var(--ink)}

.hero{padding-block:60px 44px}
.kicker{font-size:14px; color:var(--ink-3); margin-bottom:14px}
.hero h1{font:600 clamp(30px, 4.4vw, 46px)/1.12 var(--display); letter-spacing:-0.012em; max-width:22ch; text-wrap:balance}
.lede{font-size:18px; line-height:1.6; max-width:66ch; color:var(--ink-2); margin-top:22px}
.facts{display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:20px 32px; margin-top:40px; padding-top:20px; border-top:1px solid var(--rule)}
.facts dt{font:500 32px/1.1 var(--display); font-variant-numeric:tabular-nums}
.facts dd{margin:6px 0 0; font-size:14.5px; color:var(--ink-2); max-width:26ch}

section:not(.hero){padding-block:52px; border-top:1px solid var(--rule)}
h2{font:600 30px/1.2 var(--display); letter-spacing:-0.01em}
.intro{max-width:70ch; color:var(--ink-2); margin-top:12px}
.key{font-size:14px; color:var(--ink-3); margin-top:10px}
.bar{display:block; height:6px; background:var(--rule-2); border-radius:3px; overflow:hidden}
.bar i{display:block; height:100%; background:var(--c); border-radius:0 3px 3px 0}

.tax{display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 400px), 1fr)); gap:44px 64px; margin-top:32px}
.tax h3, .type-group > h3{display:flex; align-items:baseline; gap:10px; font:600 21px var(--display)}
.tax h3 + .gloss{margin-top:4px; max-width:46ch}
.tax .cat{margin-top:24px}
h4{font:600 12.5px var(--body); letter-spacing:.07em; text-transform:uppercase; color:var(--ink-2)}
.tax .cat .gloss{margin:2px 0 8px}
.tax ul{list-style:none; padding:0}
.tax li{display:grid; grid-template-columns:minmax(0, 1fr) 104px 2ch; gap:14px; align-items:center; padding:5px 0; border-top:1px solid var(--rule-2)}
.tax li a{color:var(--ink); text-decoration:none}
.tax li a:hover{text-decoration:underline}
.tax .num{text-align:right}

.filters{display:flex; flex-wrap:wrap; gap:14px 18px; align-items:flex-end; margin-top:26px; padding:16px 18px; background:var(--surface); border:1px solid var(--rule); border-radius:8px}
.field{display:flex; flex-direction:column; gap:5px; min-width:0}
.field.grow{flex:1 1 240px}
.field label, .field .lab{font-size:12.5px; font-weight:500; color:var(--ink-2)}
input[type=search], select{font:inherit; font-size:15px; height:38px; padding:0 10px; border:1px solid var(--rule); border-radius:6px; background:var(--bg); color:var(--ink); min-width:0; max-width:100%}
.seg{display:inline-flex; border:1px solid var(--rule); border-radius:6px; overflow:hidden; height:38px; background:var(--bg)}
.seg label{position:relative; display:flex; cursor:pointer}
.seg input{position:absolute; opacity:0; inset:0; margin:0; cursor:pointer}
.seg span{display:flex; align-items:center; padding:0 12px; font-size:14.5px; color:var(--ink-2)}
.seg input:checked + span{background:var(--ink); color:var(--bg)}
.seg input:focus-visible + span{outline:2px solid var(--obs); outline-offset:-2px}
.result{display:flex; gap:16px; align-items:baseline; margin-top:14px; font-size:14px; color:var(--ink-2)}
.empty{margin-top:20px; color:var(--ink-2)}
.type-group{margin-top:36px}
.type-group > .gloss{margin-top:4px}
.cat-group{margin-top:22px}
.cat-group > h4{padding-bottom:8px}
.metric{border-top:1px solid var(--rule); scroll-margin-top:calc(64px + env(safe-area-inset-top, 0px))}
.cat-group .metric:last-child{border-bottom:1px solid var(--rule)}
.metric summary{position:relative; display:grid; grid-template-columns:minmax(0, 1fr); gap:6px; padding:14px 0 14px 24px; cursor:pointer; list-style:none}
.metric summary::-webkit-details-marker{display:none}
.metric summary::before{content:""; position:absolute; left:5px; top:21px; width:7px; height:7px; border-right:2px solid var(--ink-3); border-bottom:2px solid var(--ink-3); transform:rotate(-45deg)}
.metric[open] summary::before{transform:rotate(45deg); top:19px}
.metric summary:hover .m-name{text-decoration:underline; text-underline-offset:3px}
.m-name{font-weight:600; font-size:16.5px; line-height:1.35}
.m-main{display:flex; flex-direction:column; gap:9px; min-width:0}
.m-def{color:var(--ink-2)}
.m-n{font:500 13px var(--mono); color:var(--ink-2); white-space:nowrap}
.chips{display:flex; flex-wrap:wrap; gap:6px}
.chip{font-size:12.5px; line-height:1.5; padding:1px 9px; border-radius:999px; background:var(--t); color:var(--ink); white-space:nowrap; border:1px solid transparent}
.chip.std{background:transparent; border:1px dashed var(--ink-3); color:var(--ink-2)}
.m-body{display:grid; gap:20px; padding:2px 0 24px 24px; min-width:0}
@media (min-width:820px){
  .metric summary{grid-template-columns:minmax(0, 240px) minmax(0, 1fr) 118px; gap:6px 28px}
  .m-n{text-align:right; padding-top:2px}
  .m-body{padding-left:calc(24px + 240px + 28px); padding-right:146px}
}
h5{font:600 15px var(--body)}
.ev{border-left:2px solid var(--rule); padding-left:14px; margin-top:10px; min-width:0}
.ev-name{font:500 13.5px var(--mono); overflow-wrap:anywhere}
.ev-desc{font-size:14.5px; color:var(--ink-2); margin-top:2px}
.ev blockquote{margin:8px 0 6px; padding:7px 11px; font-size:14px; background:var(--surface); border:1px solid var(--rule-2); border-radius:4px; overflow-wrap:anywhere}
.ev blockquote::before{content:"\201C"} .ev blockquote::after{content:"\201D"}
.ev-meta{font-size:12.5px; color:var(--ink-3); overflow-wrap:anywhere}
.others ul{list-style:none; padding:0; margin-top:6px; font-size:14px; color:var(--ink-2); display:grid; gap:4px}
.others .st{color:var(--ink-3)}

.legend{list-style:none; padding:0; display:flex; flex-wrap:wrap; gap:8px 26px; margin-top:20px; font-size:14px; color:var(--ink-2); --c:var(--ink-2)}
.legend li{display:flex; align-items:center; gap:8px}
.legend .blank{width:11px; height:11px; border:1px dashed var(--rule); border-radius:50%}
.dot{display:inline-block; flex:none; width:11px; height:11px; border-radius:50%; vertical-align:middle}
.s-built .dot{background:var(--c)}
.s-via .dot{border:2.5px solid var(--c)}
.s-diy .dot{width:5px; height:5px; background:var(--ink-3)}
.s-none .dot{display:none}
.mx-wrap{position:relative; overflow-x:auto; margin-top:18px; background:var(--surface); border:1px solid var(--rule); border-radius:8px}
.mx{border-collapse:separate; border-spacing:0; width:100%; font-size:14px}
.mx th, .mx td{border-bottom:1px solid var(--rule-2); padding:0}
.mx thead th{font-weight:500; background:var(--surface)}
.mx th.corner{text-align:left; vertical-align:bottom; padding:0 14px 10px; position:sticky; left:0; z-index:2; color:var(--ink-2)}
.mx th.grp{font:600 11.5px var(--body); letter-spacing:.07em; text-transform:uppercase; color:var(--ink-2); text-align:left; padding:12px 8px 0; border-bottom:0; white-space:nowrap}
.mx th.grp .of{display:block; text-align:right; padding:0 6px 10px}
.mx th.grp[rowspan]{vertical-align:bottom; border-bottom:1px solid var(--rule-2); padding-right:8px}
.mx th.col{vertical-align:bottom; height:128px; min-width:32px; padding:10px 0}
.mx th.col span{display:inline-block; writing-mode:vertical-rl; transform:rotate(180deg); white-space:nowrap; font-size:13.5px}
.mx .g0{border-left:1px solid var(--rule)}
.mx tr.cat th{text-align:left; padding:16px 14px 6px; font:600 11.5px var(--body); letter-spacing:.07em; text-transform:uppercase; color:var(--ink-2); background:var(--surface)}
.mx tr.cat .sw{margin-right:8px; width:8px; height:8px}
.mx th.row{position:sticky; left:0; z-index:1; background:var(--surface); text-align:left; font-weight:400; padding:6px 14px; min-width:168px; max-width:260px; line-height:1.3}
.mx th.row a{color:var(--ink); text-decoration:none}
.mx th.row a:hover{text-decoration:underline}
.mx td{text-align:center; height:30px}
.mx td.n{font:500 13px var(--mono); color:var(--ink-2); text-align:right; padding:0 14px 0 10px}
.mx tbody tr:not(.cat):hover > *{background:var(--rule-2)}
#tip{position:fixed; z-index:40; max-width:300px; padding:8px 11px; background:var(--ink); color:var(--bg); font-size:13px; line-height:1.4; border-radius:6px; white-space:pre-line; pointer-events:none}

.tool-group{margin-top:36px}
.tool-group h3{font:600 21px var(--display)}
.tool-group .gloss{margin-top:4px; max-width:80ch}
.tools{display:grid; grid-template-columns:repeat(auto-fill, minmax(min(100%, 310px), 1fr)); gap:16px; margin-top:16px}
.tool{display:flex; flex-direction:column; gap:14px; padding:18px 20px; background:var(--surface); border:1px solid var(--rule); border-radius:8px; min-width:0}
.tool h4{font:600 17px/1.3 var(--body); letter-spacing:0; text-transform:none; color:var(--ink)}
.role{font-size:13px; color:var(--ink-3); margin-top:3px}
.cov{display:grid; grid-template-columns:auto minmax(0, 1fr) auto; gap:6px 12px; align-items:center; font-size:13.5px; color:var(--ink-2)}
.tool dl{display:grid; grid-template-columns:auto minmax(0, 1fr); gap:3px 16px; font-size:13.5px}
.tool dt{color:var(--ink-3)} .tool dd{margin:0; font-variant-numeric:tabular-nums}
.acts{display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:auto; font-size:14px}

.cols{display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap:36px 48px; margin-top:28px}
.cols h3{font:600 19px var(--display); margin-bottom:8px}
.cols h3:not(:first-child){margin-top:24px}
.cols p, .cols li{color:var(--ink-2); font-size:15px}
.funnel{width:100%; border-collapse:collapse; margin-top:14px; font-size:14px}
.funnel td{padding:7px 0; border-top:1px solid var(--rule-2); color:var(--ink-2); vertical-align:top}
.funnel td.num{text-align:right; padding-left:14px; color:var(--ink)}
.care{padding-left:18px; display:grid; gap:8px}
footer{border-top:1px solid var(--rule); padding-block:28px 40px; font-size:14px; color:var(--ink-3)}
footer p + p{margin-top:6px}
@media (prefers-reduced-motion: no-preference){ html{scroll-behavior:smooth} }
"""

JS = r"""
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var q = $('#q'), fTool = $('#f-tool'), fCat = $('#f-cat'), count = $('#count'), clear = $('#clear'), none = $('#none');
  var entries = $$('.metric'), main = entries.filter(function (x) { return !x.classList.contains('extra'); });

  function apply() {
    var text = q.value.trim().toLowerCase(), type = $('input[name="f-type"]:checked').value, tool = fTool.value, cat = fCat.value, n = 0;
    entries.forEach(function (x) {
      var ok = (!text || x.dataset.text.indexOf(text) >= 0) && (!type || x.dataset.type === type) &&
               (!cat || x.dataset.cat === cat) && (!tool || x.dataset.tools.split('|').indexOf(tool) >= 0);
      x.hidden = !ok;
      if (ok && main.indexOf(x) >= 0) n++;
    });
    $$('.cat-group, .type-group').forEach(function (g) {
      g.hidden = !$$('.metric', g).some(function (x) { return !x.hidden; });
    });
    var filtered = !!(text || type || tool || cat);
    count.textContent = filtered ? n + ' of ' + main.length + ' metrics' : 'All ' + main.length + ' metrics';
    clear.hidden = !filtered;
    none.hidden = entries.some(function (x) { return !x.hidden; });
  }
  function reset() {
    q.value = ''; fTool.value = ''; fCat.value = ''; $('#f-type-all').checked = true; apply();
  }
  $('#filters').addEventListener('input', apply);
  $('#filters').addEventListener('change', apply);
  $('#filters').addEventListener('submit', function (ev) { ev.preventDefault(); });
  clear.addEventListener('click', reset);

  // A link to a metric opens its entry, clearing any filter that hides it.
  function openFromHash() {
    var id = location.hash.slice(1);
    if (id.indexOf('m-') !== 0) return;
    var el = document.getElementById(id);
    if (!el) return;
    if (el.hidden) reset();
    el.open = true;
    el.scrollIntoView();
  }
  window.addEventListener('hashchange', openFromHash);
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest('a[href^="#m-"]');
    if (a && a.getAttribute('href') === location.hash) openFromHash();
    var b = ev.target.closest('[data-show-tool]');
    if (b) { reset(); fTool.value = b.dataset.showTool; apply(); $('#catalogue').scrollIntoView(); }
  });
  apply();
  openFromHash();

  // Hover text for the coverage table.
  var tip = $('#tip'), table = $('.mx');
  function show(ev) {
    var c = ev.target.closest('[data-tip]');
    if (!c) { tip.hidden = true; return; }
    tip.textContent = c.dataset.tip;
    tip.hidden = false;
    var r = c.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    var x = Math.max(8, Math.min(window.innerWidth - w - 8, r.left + r.width / 2 - w / 2));
    var y = r.top - h - 8 < 8 ? r.bottom + 8 : r.top - h - 8;
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }
  table.addEventListener('mouseover', show);
  table.addEventListener('click', show);
  table.addEventListener('mouseleave', function () { tip.hidden = true; });
  window.addEventListener('scroll', function () { tip.hidden = true; }, { passive: true });
})();
"""

FONTS = ("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400"
         "&family=IBM+Plex+Serif:wght@500;600&display=swap")


def render():
    """The page as (head, body): head holds the title, the font link and the styles; body the content and the script."""
    d = load()
    head = (f"<title>{TITLE}</title>\n<meta name=\"claude:viewport-fit-sides\" content=\"cover\">\n"
            f"<link rel=\"stylesheet\" href=\"{FONTS}\">\n<style>{CSS}</style>\n")
    body = f"""
<header class="top"><div class="wrap">
  <a class="brand" href="#intro">{TITLE}</a>
  <nav aria-label="Sections"><a href="#taxonomy">Taxonomy</a><a href="#catalogue">Catalogue</a><a href="#matrix">Coverage</a><a href="#tools">Tools</a><a href="#method">Method</a></nav>
</div></header>
<main>
{hero(d)}
{taxonomy(d)}
{catalogue(d)}
{matrix(d)}
{tools_section(d)}
{method(d)}
</main>
<footer><div class="wrap">
  <p>Companion to the paper “{e(PAPER_TITLE)}” (in preparation). The data, the scripts and a saved copy of every cited
  page are in the <a href="{REPO_URL}" target="_blank" rel="noopener">repository</a>.</p>
  <p>Generated from the data on {nice_date(date.today().isoformat())}.</p>
</div></footer>
<div id="tip" role="tooltip" hidden></div>
<script>{JS}</script>
"""
    return head, body


def main():
    head, body = render()
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            f"<meta name=\"description\" content=\"{e(PAPER_TITLE)}: taxonomy, definitions and the tools that ship each metric.\">\n"
            f"{head}</head>\n<body>{body}</body>\n</html>\n")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(page) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
