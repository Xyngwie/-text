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
from collections import deque
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse
from archive_issue_comments import api

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
        publisher = normalized_publisher(item, title) or source.get('publisher', '')
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
            "category": source.get('category', source['track']),
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
    sources = [source for source in config['sources'] if source.get('enabled', True)]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(sources)))) as pool:
        futures = [(source, pool.submit(fetcher, source['url'], timeout)) for source in sources]
        fetched = []
        for source, future in futures:
            try:
                fetched.append((source, future.result()))
            except Exception as exc:  # report one feed failure without losing all feeds
                errors.append({"source_id": source.get("source_id"), "error": f"{type(exc).__name__}: {exc}"})
    diagnostics = []
    for source, payload in fetched:
        try:
            rows = parse_feed(payload, source, excluded)
        except Exception as exc:
            errors.append({"source_id": source.get("source_id"), "error": f"{type(exc).__name__}: {exc}"})
            continue
        max_age = source.get('max_age_hours', config.get('max_age_hours'))
        if max_age is not None:
            cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max_age)
            for row in rows:
                if row['published_at'] and dt.datetime.fromisoformat(row['published_at']) < cutoff:
                    row['rejected_reasons'].append('stale_item')
        for row in rows:
            if any(re.search(pattern, row['title'], re.IGNORECASE) for pattern in config.get('excluded_title_patterns', [])):
                row['rejected_reasons'].append('non_article_title')
        diagnostics.append(dict(source_id=source['source_id'], fetched=len(rows),
                                accepted=sum(not row['rejected_reasons'] for row in rows),
                                rejected=sum(bool(row['rejected_reasons']) for row in rows)))
        for row in rows:
            if row["candidate_id"] in seen:
                continue
            seen.add(row["candidate_id"])
            if include_rejected or not row["rejected_reasons"]:
                candidates.append(row)
    return {"schema_version": 1, "candidates": candidates, "errors": errors, 'source_diagnostics': diagnostics}


def balanced_candidates(candidates, limit, category_order=(), excluded_ids=(), category_last_seen=None):
    """Round-robin categories and feeds; sort newest first inside each feed."""
    if limit < 0:
        raise ValueError('max-items must be nonnegative')
    excluded = set(excluded_ids)
    groups = {}
    for row in candidates:
        if row['candidate_id'] in excluded:
            continue
        category = row.get('category', row['track'])
        groups.setdefault(category, {}).setdefault(row['source_id'], []).append(row)
    order = [category for category in category_order if category in groups]
    order.extend(category for category in groups if category not in order)
    if category_last_seen is not None:
        # Never-selected categories first, then least recently issued. Stable
        # ties follow configuration order, without resetting priority each run.
        order.sort(key=lambda category: category_last_seen.get(category, ''))
    queues = {}
    for category, sources in groups.items():
        feeds = [sorted(rows, key=lambda r: r['published_at'] or '', reverse=True) for rows in sources.values()]
        feeds.sort(key=lambda rows: rows[0]['published_at'] or '', reverse=True)
        queues[category] = deque(deque(rows) for rows in feeds)
    result = []
    while len(result) < limit:
        advanced = False
        for category in order:
            if not queues[category]:
                continue
            feed = queues[category].popleft()
            result.append(feed.popleft())
            if feed:
                queues[category].append(feed)
            advanced = True
            if len(result) == limit:
                break
        if not advanced:
            break
    return result


def issue_selection_history(issues):
    excluded, last_seen = set(), {}
    for issue in issues:
        if 'pull_request' in issue:
            continue
        body = issue.get('body') or ''
        ids = re.findall(r'<!-- candidate-id:(rss-[0-9a-f]{20}) -->', body)
        if not ids:
            continue
        excluded.update(ids)
        for label in issue.get('labels', []):
            name = label['name']
            if name.startswith('news-'):
                category = name.removeprefix('news-')
                last_seen[category] = max(last_seen.get(category, ''), issue.get('created_at') or '')
    return excluded, last_seen


def existing_candidate_ids(repo):
    return issue_selection_history(api(f'repos/{repo}/issues?state=all&labels=rss-agent&per_page=100'))[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--include-rejected", action="store_true")
    parser.add_argument("--max-items", type=int, default=10)
    parser.add_argument('--exclude-existing-issues', action='store_true')
    parser.add_argument('--repo')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    result = collect(config, args.timeout, args.include_rejected)
    if args.exclude_existing_issues and not args.repo:
        parser.error('--repo is required for Issue deduplication')
    excluded, last_seen = (issue_selection_history(api(
        f'repos/{args.repo}/issues?state=all&labels=rss-agent&per_page=100'))
        if args.exclude_existing_issues else (set(), None))
    result['excluded_existing_count'] = sum(row['candidate_id'] in excluded for row in result['candidates'])
    result['candidates'] = balanced_candidates(result['candidates'], args.max_items,
                                               config.get('category_order', []), excluded, last_seen)
    result['category_last_issued_at'] = last_seen or {}
    result['selection_policy'] = 'least_recently_issued_category_then_feed_round_robin'
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
