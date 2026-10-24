"""Integration checks for adding archives without moving existing evidence."""
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourcesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'repo'
        subprocess.run(['git', 'clone', '-q', '--local', '--no-hardlinks', str(ROOT), str(self.root)], check=True)
        shutil.copytree(ROOT / 'tools', self.root / 'tools', dirs_exist_ok=True)
        # Source registration and the new analysis may be one working change.
        # Keep the fixture's analysis metadata aligned with the working catalog.
        shutil.copytree(ROOT / 'analysis', self.root / 'analysis', dirs_exist_ok=True)
        shutil.copyfile(ROOT / 'data/sources.json', self.root / 'data/sources.json')
        for source in json.loads((ROOT / 'data/sources.json').read_text())['sources']:
            target = self.root / source['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source['path'], target)
        self.original = [json.loads(line) for line in (ROOT / 'data/utterances.jsonl').read_text().splitlines()]

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *args, success=True):
        r = subprocess.run(['python3', *args], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(r.returncode == 0, success, r.stdout + r.stderr)
        return r

    def register(self):
        path = self.root / 'sources/claude.txt'
        path.parent.mkdir(exist_ok=True)
        path.write_text('User\nAIの仕組みを知りたい\nClaude\n説明です\nUser\nありがとう\n')
        subprocess.run(['git', 'add', 'sources'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                        'commit', '-qm', 'fixture'], cwd=self.root, check=True)
        self.run_tool('tools/add_source.py', '--source-id', 'claude-001', '--path', 'sources/claude.txt',
                      '--assistant', 'Claude', '--user-marker', 'User', '--assistant-marker', 'Claude')
        return path

    def test_add_preserves_legacy_and_separates_context(self):
        self.register()
        self.run_tool('tools/build_index.py')
        self.run_tool('tools/validate.py')
        rows = [json.loads(line) for line in (self.root / 'data/utterances.jsonl').read_text().splitlines()]
        self.assertEqual(rows[:len(self.original)], self.original)
        added = rows[len(self.original):]
        self.assertEqual([r['id'] for r in added], ['claude-001:U00001', 'claude-001:U00002', 'claude-001:U00003'])
        self.assertIsNone(rows[len(self.original)-1]['next_id'])
        self.assertIsNone(added[0]['previous_id'])
        self.assertIsNone(added[-1]['next_id'])
        self.assertEqual(added[1]['theme_candidates'], {})
        progress = json.loads((self.root / 'data/progress.json').read_text())
        self.assertFalse(progress['semantic_classification_complete'])
        self.assertTrue(progress['sources']['copilot-001']['semantic_classification_complete'])
        self.assertEqual(progress['next_user_utterance'], 'claude-001:U00001')
        self.assertEqual(progress['total_detected_user_utterances'],
                         sum(row['role'] == 'user' for row in self.original) + 2)
        before = (self.root / 'data/utterances.jsonl').read_bytes()
        self.run_tool('tools/build_index.py')
        self.assertEqual(before, (self.root / 'data/utterances.jsonl').read_bytes())
        candidate = (self.root / 'themes/ai.md').read_text()
        config = json.loads((self.root / 'data/sources.json').read_text())
        self.assertIn(config['sources'][-1]['source_commit'] + '/sources/claude.txt#L1-L2', candidate)

    def test_changed_archive_rejected_without_overwriting_index(self):
        path = self.register()
        self.run_tool('tools/build_index.py')
        before = (self.root / 'data/utterances.jsonl').read_bytes()
        path.write_text(path.read_text() + 'User\n追加\n')
        self.run_tool('tools/build_index.py', success=False)
        self.assertEqual(before, (self.root / 'data/utterances.jsonl').read_bytes())

    def test_move_preserves_ids_hashes_and_original_links(self):
        self.run_tool('tools/build_index.py')
        rows = [json.loads(line) for line in (self.root / 'data/utterances.jsonl').read_text().splitlines()]
        self.assertEqual(rows, self.original)
        original_links = (self.root / 'themes/ai.md').read_text()
        registry = self.root / 'data/sources.json'
        config = json.loads(registry.read_text())
        source = config['sources'][0]
        old_path = source['path']
        moved = self.root / 'sources/relocated/archive.txt'
        moved.parent.mkdir(parents=True)
        (self.root / old_path).rename(moved)
        source['source_commit_path'] = source.get('source_commit_path', old_path)
        source['path'] = moved.relative_to(self.root).as_posix()
        registry.write_text(json.dumps(config, ensure_ascii=False))
        self.run_tool('tools/build_index.py')
        self.run_tool('tools/validate.py')
        self.assertEqual(rows, [json.loads(line) for line in (self.root / 'data/utterances.jsonl').read_text().splitlines()])
        self.assertEqual(original_links, (self.root / 'themes/ai.md').read_text())

    def test_moved_archive_still_rejects_content_changes(self):
        self.run_tool('tools/build_index.py')
        before = (self.root / 'data/utterances.jsonl').read_bytes()
        source = json.loads((self.root / 'data/sources.json').read_text())['sources'][0]
        path = self.root / source['path']
        path.write_bytes(path.read_bytes() + b'changed')
        self.run_tool('tools/build_index.py', success=False)
        self.assertEqual(before, (self.root / 'data/utterances.jsonl').read_bytes())

    def test_analysis_snapshot_reads_pinned_path_after_move(self):
        # A future analysis pins today's registry, whose local and historical paths differ.
        registry = self.root / 'data/sources.json'
        config = json.loads(registry.read_text())
        source = config['sources'][0]
        original_path = source.get('source_commit_path', source['path'])
        moved = self.root / 'sources/analysis-fixture/archive.txt'
        moved.parent.mkdir(parents=True)
        (self.root / source['path']).rename(moved)
        source['source_commit_path'] = original_path
        source['path'] = moved.relative_to(self.root).as_posix()
        registry.write_text(json.dumps(config, ensure_ascii=False))
        subprocess.run(['git', 'add', 'data/sources.json'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                        'commit', '-qm', 'pin relocated registry'], cwd=self.root, check=True)
        version = json.loads((self.root / 'analysis/progress.json').read_text())['current_version']
        manifest_path = self.root / 'analysis' / version / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['sources'] = config['sources']
        manifest['base_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root, text=True).strip()
        manifest['input_files']['data/sources.json'] = hashlib.sha256(registry.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False))
        self.run_tool('tools/validate_analysis.py', '--version', version)

    def test_duplicate_registration_rolls_back(self):
        self.register()
        before = (self.root / 'data/sources.json').read_bytes()
        self.run_tool('tools/add_source.py', '--source-id', 'claude-002', '--path', 'sources/claude.txt',
                      '--assistant', 'Claude', '--user-marker', 'User', '--assistant-marker', 'Claude', success=False)
        self.assertEqual(before, (self.root / 'data/sources.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
