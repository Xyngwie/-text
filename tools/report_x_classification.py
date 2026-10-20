#!/usr/bin/env python3
"""Deliver committed stage-2 reports to Issues, retrying an on-disk outbox."""
import json
import os
from pathlib import Path
import tempfile

from publish_issue_payloads import run, already_exists, ensure_label

ROOT = Path(__file__).resolve().parents[1]


def main():
    repo = os.environ['GITHUB_REPOSITORY']
    receipts_path = ROOT / 'data/x_classification_notifications.json'
    receipts = json.loads(receipts_path.read_text()) if receipts_path.exists() else {}
    pending = []
    for path in sorted((ROOT / 'batches/x/auto').glob('XA-*.json')):
        report = json.loads(path.read_text())
        if report['batch_id'] not in receipts:
            pending.append((path, report))
    if not pending:
        print('No pending reports')
        return
    ensure_label(repo, 'x-classification')
    # Bounded delivery; committed reports remain retryable on later runs.
    for path, report in pending[:5]:
        batch = report['batch_id']
        if not already_exists(repo, batch):
            model = report['provenance']['model_version']
            refs = '\n'.join(f'- https://x.com/i/web/status/{pid}' for pid in report['observation_post_ids'])
            body = (f'<!-- candidate-id:{batch} -->\n\n'
                    f"{report['observation']}\n\n{refs}\n\n"
                    f"Gemini `{model}` による第二段階のAI分類案：{report['count']}件。残り{report['remaining']}件。\n"
                    '本人確認済みの分析ではありません。第三段階は本人との壁打ちで進めます。\n\n'
                    f'[実行ログ]({report["provenance"]["workflow_run_url"]}) / '
                    f'[詳細レポート](https://github.com/{repo}/blob/main/{path.relative_to(ROOT).as_posix()})\n\n'
                    '補足はこのIssueにコメントできます。コメントやクローズだけでは分類の全面承認・自動修正にしません。\n')
            with tempfile.TemporaryDirectory() as tmp:
                file = Path(tmp) / 'body.md'
                file.write_text(body)
                result = run('gh', 'issue', 'create', '--repo', repo, '--title', f'[X分類] {batch}',
                             '--label', 'x-classification', '--body-file', str(file))
                receipt = result.stdout.strip()
        else:
            receipt = 'already_exists'
        receipts[batch] = receipt
        receipts_path.write_text(json.dumps(receipts, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
