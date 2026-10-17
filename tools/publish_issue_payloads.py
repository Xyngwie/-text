#!/usr/bin/env python3
"""Create deduplicated GitHub Issues from generated payload JSON."""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path


def run(*args, check=True):
    return subprocess.run(args, check=check, capture_output=True, text=True)


def ensure_label(repo, label):
    result = run("gh", "label", "create", label, "--repo", repo, "--color", "5319e7", "--force", check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr)


def already_exists(repo, candidate_id):
    result = run(
        "gh", "issue", "list", "--repo", repo, "--state", "all",
        "--search", f'\"candidate-id:{candidate_id}\" in:body',
        "--json", "number", "--limit", "1",
    )
    return bool(json.loads(result.stdout))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    args = parser.parse_args()
    if not args.repo:
        raise SystemExit("--repo or GITHUB_REPOSITORY is required")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    created = []
    skipped = []
    for issue in payload.get("issues", []):
        candidate_id = issue["candidate_id"]
        if already_exists(args.repo, candidate_id):
            skipped.append(candidate_id)
            continue
        for label in issue["labels"]:
            ensure_label(args.repo, label)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(issue["body"])
            body_path = Path(handle.name)
        try:
            command = [
                "gh", "issue", "create", "--repo", args.repo,
                "--title", issue["title"], "--body-file", str(body_path),
            ]
            for label in issue["labels"]:
                command.extend(["--label", label])
            result = run(*command)
            created.append({"candidate_id": candidate_id, "url": result.stdout.strip()})
        finally:
            body_path.unlink(missing_ok=True)
    print(json.dumps({"created": created, "skipped": skipped}, ensure_ascii=False))


if __name__ == "__main__":
    main()
