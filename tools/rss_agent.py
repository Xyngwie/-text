#!/usr/bin/env python3
"""Collect RSS/Atom entries with source allowlists and deterministic deduplication."""

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/rss_sources.json"
USER_AGENT = "Xyngwie-text-rss-agent/1.0 (+https://github.com/Xyngwie/-text)"


def text_of(element, names):
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1] in names and child.text:
            return child.text.strip()
    return ""


def clean_markup(value):
    value = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", value).strip()


def normalized_publisher(item, title):
    publisher = text_of(item, {"source", "author"})
    if publisher:
        return clean_markup(publisher)
    if " - " in title:
        return title.rsplit(" - ", 1)[-1].strip()
    return ""


def entry_link(item):
    for child in item.iter():
        if child.tag.rsplit("}", 1)[-1] != "link":
            continue
        if child.attrib.get("href"):
            if child.attrib.get("rel", "alternate") == "alternate":
                return child.attrib["href"].strip()
        elif child.text:
            return child.text.strip()
    return ""


def normalized_date(raw):
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            parsed = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def candidate_id(source_id, guid, link, title):
    # Deliberately exclude source_id so the same syndicated item found by
    # multiple searches keeps one identity.
    material = "\n".join([guid or "", link or "", title])
    return "rss-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:20]


def publisher_allowed(publisher, allowlist):
    if not allowlist:
        return True
    folded = publisher.casefold()
    return any(item.casefold() in folded for item in allowlist)


def fetch(url, timeout):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_feed(payload, source, excluded_terms):
    root = ET.fromstring(payload)
    items = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] in {"item", "entry"}]
    results = []
    for item in items:
        title = clean_markup(text_of(item, {"title"}))
        description = clean_markup(text_of(item, {"description", "summary", "content"}))
        link = entry_link(item)
        guid = text_of(item, {"guid", "id"})
        publisher = normalized_publisher(item, title)
        raw_date = text_of(item, {"pubDate", "published", "updated"})
        if not title or not link or urlparse(link).scheme not in {"http", "https"}:
            continue
        rejected = []
        if not publisher_allowed(publisher, source.get("allowed_publishers", [])):
            rejected.append("publisher_not_allowlisted")
        if source["track"] == "experimental-politics":
            matched = [term for term in excluded_terms if term.casefold() in (title + " " + description).casefold()]
            if matched:
                rejected.append("excluded_term:" + ",".join(matched))
        results.append({
            "candidate_id": candidate_id(source["source_id"], guid, link, title),
            "source_id": source["source_id"],
            "source_name": source["name"],
            "track": source["track"],
            "title": title,
            "description": description,
            "publisher": publisher,
            "link": link,
            "published_at": normalized_date(raw_date),
            "source_claim_status": "fact_candidate_not_verified",
            "rejected_reasons": rejected,
        })
    return results


def collect(config, timeout, include_rejected=False, fetcher=fetch):
    excluded = config.get("experimental_excluded_terms", [])
    candidates = []
    errors = []
    seen = set()
    sources = config["sources"]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(sources)))) as pool:
        futures = {source["source_id"]: pool.submit(fetcher, source["url"], timeout) for source in sources}
        fetched = []
        for source in sources:
            try:
                fetched.append((source, futures[source["source_id"]].result()))
            except Exception as exc:  # report one feed failure without losing all feeds
                errors.append({"source_id": source.get("source_id"), "error": f"{type(exc).__name__}: {exc}"})
    for source, payload in fetched:
        try:
            rows = parse_feed(payload, source, excluded)
        except Exception as exc:
            errors.append({"source_id": source.get("source_id"), "error": f"{type(exc).__name__}: {exc}"})
            continue
        for row in rows:
            if row["candidate_id"] in seen:
                continue
            seen.add(row["candidate_id"])
            if include_rejected or not row["rejected_reasons"]:
                candidates.append(row)
    return {"schema_version": 1, "candidates": candidates, "errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--include-rejected", action="store_true")
    parser.add_argument("--max-items", type=int, default=10)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = collect(config, args.timeout, args.include_rejected)
    result["candidates"] = result["candidates"][:args.max_items]
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    if result["errors"] and not result["candidates"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
