#!/usr/bin/env python3
"""Collect auditable documentation text for every tool in the combined inventory.

GitHub-backed tools use their repository README and relevant documentation links.
Other tools use the maintained URLs in metric_source_urls.csv. Collection errors
are written into the JSONL output so downstream stages can report missing evidence.
"""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import datetime
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_INPUT = "combined_tools_no_duplicates.csv"
DEFAULT_REGISTRY = "metric_source_urls.csv"
DEFAULT_OUTPUT = "metric_source_documents.jsonl"
RELEVANT_TERMS = (
    "metric", "eval", "scorer", "score", "observability", "tracing", "monitoring",
    "token", "cost", "latency", "quality", "rag", "safety", "agent",
)
class TextHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.links = []

    def handle_data(self, data):
        value = data.strip()
        if value:
            self.text.append(value)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--max-documents", type=int, default=6,
                        help="maximum documents collected per tool")
    parser.add_argument("--max-bytes", type=int, default=1_000_000,
                        help="maximum bytes read from one document")
    parser.add_argument("--tool-key", action="append", default=[],
                        help="collect only the selected tool key; may be repeated")
    parser.add_argument("--workers", type=int, default=4,
                        help="number of tools collected concurrently")
    parser.add_argument("--offline", action="store_true",
                        help="use inventory descriptions only; intended for tests")
    return parser.parse_args()


def read_csv(path, required):
    with open(path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def request(url, max_bytes, accept=None):
    headers = {"User-Agent": "agent-observability-metrics-research/1.0"}
    if accept:
        headers["Accept"] = accept
    if os.environ.get("GITHUB_TOKEN") and "api.github.com" in url:
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

    last_error = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read(max_bytes + 1)
                if len(content) > max_bytes:
                    content = content[:max_bytes]
                return content, response.headers.get_content_type(), response.geturl()
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            if attempt < 1:
                time.sleep(2 ** attempt)
    raise last_error


def decode_document(content, content_type):
    text = content.decode("utf-8", errors="replace")
    links = []
    if "html" in content_type or re.search(r"<html\b", text[:1000], re.I):
        parser = TextHTMLParser()
        parser.feed(text)
        text = "\n".join(parser.text)
        links = parser.links
    else:
        links = re.findall(r"\[[^\]]+\]\(([^)\s]+)(?:\s+[^)]*)?\)", text)
    return html.unescape(text), links


def relevant_link(url):
    lowered = urllib.parse.unquote(url).casefold()
    path = urllib.parse.urlparse(lowered).path
    if path.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".zip")):
        return False
    return any(term in lowered for term in RELEVANT_TERMS) or path.endswith(("/readme.md", "/llms.txt"))


def normalize_link(base_url, link):
    link = html.unescape(link.strip()).strip("<>")
    if not link or link.startswith(("#", "mailto:", "javascript:")):
        return ""
    url = urllib.parse.urljoin(base_url, link).split("#", 1)[0]
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return ""
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/blob/([^/]+)/(.*)", url)
    if match:
        repo, branch, path = match.groups()
        return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    return url


def document_record(tool, source_type, source_url, source_path, content, status="ok", error=""):
    return {
        "tool_key": tool["tool_key"],
        "tool": tool["tool"],
        "github_repo": tool.get("github_repo", ""),
        "source_type": source_type,
        "source_url": source_url,
        "source_path": source_path,
        "collected_date": datetime.date.today().isoformat(),
        "collection_status": status,
        "collection_error": error,
        "content": content,
    }


def collect_url(tool, url, source_type, max_bytes):
    content, content_type, final_url = request(url, max_bytes)
    text, links = decode_document(content, content_type)
    path = urllib.parse.urlparse(final_url).path.rsplit("/", 1)[-1] or final_url
    return document_record(tool, source_type, final_url, path, text), links


def collect_github_readme(tool, max_bytes):
    repo = tool["github_repo"]
    api_url = f"https://api.github.com/repos/{repo}/readme"
    api_error = None
    try:
        content, _, _ = request(api_url, max_bytes, "application/vnd.github+json")
        data = json.loads(content)
        text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        links = re.findall(r"\[[^\]]+\]\(([^)\s]+)(?:\s+[^)]*)?\)", text)
        url = data.get("download_url") or data.get("html_url") or api_url
        return document_record(tool, "github_readme", url, data.get("path", "README.md"), text), links
    except Exception as error:
        api_error = error

    for branch in ("main", "master"):
        raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/README.md"
        try:
            content, content_type, final_url = request(raw_url, max_bytes)
            text, links = decode_document(content, content_type)
            return document_record(tool, "github_readme", final_url, "README.md", text), links
        except Exception:
            continue
    raise api_error


def collect_for_tool(tool, registry_urls, max_documents, max_bytes, offline):
    if offline:
        return [document_record(
            tool, "inventory_description", "inventory://combined_tools_no_duplicates.csv",
            "description", tool.get("description", "")
        )]

    documents = []
    queue = []
    if tool.get("github_repo"):
        try:
            readme, links = collect_github_readme(tool, max_bytes)
            documents.append(readme)
            queue.extend(normalize_link(readme["source_url"], link) for link in links)
        except Exception as error:
            documents.append(document_record(
                tool, "github_readme", f"https://github.com/{tool['github_repo']}", "README.md", "",
                "error", str(error)
            ))

    forced_urls = set(registry_urls)
    for url in registry_urls:
        queue.append(url)

    seen = {record["source_url"] for record in documents}
    queue = [url for url in queue if url and (url in forced_urls or relevant_link(url))]
    while queue and len(documents) < max_documents:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            record, links = collect_url(tool, url, "official_or_linked_docs", max_bytes)
            documents.append(record)
            for link in links:
                candidate = normalize_link(record["source_url"], link)
                if candidate and candidate not in seen and relevant_link(candidate):
                    queue.append(candidate)
        except Exception as error:
            documents.append(document_record(
                tool, "official_or_linked_docs", url, urllib.parse.urlparse(url).path, "",
                "error", str(error)
            ))

    if not documents:
        documents.append(document_record(
            tool, "missing_source", "", "", "", "error",
            "no GitHub repository or registered official documentation URL"
        ))
    return documents


def write_jsonl_atomic(path, records):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=destination.parent,
                                     prefix=destination.name + ".", delete=False) as file:
        temporary = Path(file.name)
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    os.replace(temporary, destination)
    os.chmod(destination, 0o644)


def main():
    args = parse_args()
    tools = read_csv(args.input, {"tool_key", "tool", "github_repo", "description"})
    if args.tool_key:
        selected = set(args.tool_key)
        tools = [tool for tool in tools if tool["tool_key"] in selected]
        missing = selected.difference(tool["tool_key"] for tool in tools)
        if missing:
            raise ValueError(f"unknown tool keys: {', '.join(sorted(missing))}")
    registry_rows = read_csv(args.registry, {"tool_key", "source_url"}) if Path(args.registry).exists() else []
    registry = {}
    for row in registry_rows:
        if row["source_url"].strip():
            registry.setdefault(row["tool_key"].strip(), []).append(row["source_url"].strip())

    collected_by_index = [None] * len(tools)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(
                collect_for_tool, tool, registry.get(tool["tool_key"], []),
                args.max_documents, args.max_bytes, args.offline
            ): (index, tool)
            for index, tool in enumerate(tools)
        }
        for completed_number, future in enumerate(as_completed(futures), 1):
            index, tool = futures[future]
            collected = future.result()
            collected_by_index[index] = collected
            ok_count = sum(record["collection_status"] == "ok" for record in collected)
            print(f"[{completed_number:>2}/{len(tools)}] {tool['tool']}: {ok_count} documents", flush=True)

    records = [record for collected in collected_by_index for record in collected]

    write_jsonl_atomic(args.output, records)
    ok_total = sum(record["collection_status"] == "ok" for record in records)
    print(f"wrote {len(records)} source records ({ok_total} successful) to {args.output}")


if __name__ == "__main__":
    main()

