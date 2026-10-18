"""Check that analysis validation rejects corrupted quotations and leaked evidence."""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('validate_analysis', ROOT / 'tools/validate_analysis.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AnalysisTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # The immutable snapshot is read from the original git object store.
        (self.root / '.git').symlink_to(ROOT / '.git', target_is_directory=True)
        shutil.copytree(ROOT / 'analysis', self.root / 'analysis')

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_snapshot(self):
        result = module.validate(root=self.root)
        self.assertEqual(result['episodes'], 33)
        self.assertEqual(result['findings'], 8)

    def test_expanded_version_preserves_history(self):
        result = module.validate(version='v002', root=self.root)
        self.assertEqual(result['episodes'], 58)
        self.assertEqual(result['reserve_segments'], 45)

    def test_third_version_preserves_history(self):
        result = module.validate(version='v003', root=self.root)
        self.assertEqual(result['episodes'], 83)
        self.assertEqual(result['coded_utterances'], 214)
        self.assertEqual(result['findings'], 10)

    def test_fourth_version_preserves_history(self):
        result = module.validate(version='v004', root=self.root)
        self.assertEqual(result['episodes'], 108)
        self.assertEqual(result['coded_utterances'], 288)
        self.assertEqual(result['findings'], 11)

    def test_fifth_version_preserves_history(self):
        result = module.validate(version='v005', root=self.root)
        self.assertEqual(result['episodes'], 123)
        self.assertEqual(result['coded_utterances'], 328)
        self.assertEqual(result['findings'], 11)

    def test_sixth_version_preserves_history(self):
        result = module.validate(version='v006', root=self.root)
        self.assertEqual(result['episodes'], 135)
        self.assertEqual(result['coded_utterances'], 370)
        self.assertEqual(result['findings'], 11)

    def test_seventh_version_preserves_history(self):
        result = module.validate(version='v007', root=self.root)
        self.assertEqual(result['episodes'], 135)
        self.assertEqual(result['coded_utterances'], 370)
        self.assertEqual(result['findings'], 11)

    def test_eighth_version_preserves_history(self):
        result = module.validate(version='v008', root=self.root)
        self.assertEqual(result['episodes'], 152)
        self.assertEqual(result['coded_utterances'], 407)
        self.assertEqual(result['findings'], 19)

    def test_ninth_version_preserves_history(self):
        result = module.validate(version='v009', root=self.root)
        self.assertEqual(result['episodes'], 152)
        self.assertEqual(result['coded_utterances'], 407)
        self.assertEqual(result['findings'], 19)

    def test_tenth_version_preserves_history(self):
        result = module.validate(version='v010', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_eleventh_version_preserves_history(self):
        result = module.validate(version='v011', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twelfth_version_preserves_history(self):
        result = module.validate(version='v012', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_thirteenth_version_preserves_history(self):
        result = module.validate(version='v013', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_fourteenth_version_preserves_history(self):
        result = module.validate(version='v014', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_fifteenth_version_preserves_history(self):
        result = module.validate(version='v015', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_sixteenth_version_preserves_history(self):
        result = module.validate(version='v016', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_seventeenth_version_preserves_history(self):
        result = module.validate(version='v017', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_eighteenth_version_preserves_history(self):
        result = module.validate(version='v018', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_nineteenth_version_preserves_history(self):
        result = module.validate(version='v019', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twentieth_version_preserves_history(self):
        result = module.validate(version='v020', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_first_version_preserves_history(self):
        result = module.validate(version='v021', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_second_version_preserves_history(self):
        result = module.validate(version='v022', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_third_version_preserves_history(self):
        result = module.validate(version='v023', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_fourth_version_preserves_history(self):
        result = module.validate(version='v024', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_fifth_version_preserves_history(self):
        result = module.validate(version='v025', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_sixth_version_preserves_history(self):
        result = module.validate(version='v026', root=self.root)
        self.assertEqual(result['episodes'], 164)
        self.assertEqual(result['coded_utterances'], 452)
        self.assertEqual(result['findings'], 19)

    def test_twenty_fifth_version_change_is_rejected(self):
        path = self.root / 'analysis/v025/profile.md'
        path.write_text(path.read_text() + '\n第二十五版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v026', root=self.root)

    def test_twenty_fourth_version_change_is_rejected(self):
        path = self.root / 'analysis/v024/profile.md'
        path.write_text(path.read_text() + '\n第二十四版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v025', root=self.root)

    def test_twenty_third_version_change_is_rejected(self):
        path = self.root / 'analysis/v023/profile.md'
        path.write_text(path.read_text() + '\n第二十三版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v024', root=self.root)

    def test_twenty_second_version_change_is_rejected(self):
        path = self.root / 'analysis/v022/profile.md'
        path.write_text(path.read_text() + '\n第二十二版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v023', root=self.root)

    def test_twenty_first_version_change_is_rejected(self):
        path = self.root / 'analysis/v021/profile.md'
        path.write_text(path.read_text() + '\n第二十一版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v022', root=self.root)

    def test_twentieth_version_change_is_rejected(self):
        path = self.root / 'analysis/v020/profile.md'
        path.write_text(path.read_text() + '\n第二十版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v021', root=self.root)

    def test_nineteenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v019/profile.md'
        path.write_text(path.read_text() + '\n第十九版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v020', root=self.root)

    def test_eighteenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v018/profile.md'
        path.write_text(path.read_text() + '\n第十八版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v019', root=self.root)

    def test_seventeenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v017/profile.md'
        path.write_text(path.read_text() + '\n第十七版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v018', root=self.root)

    def test_sixteenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v016/profile.md'
        path.write_text(path.read_text() + '\n第十六版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v017', root=self.root)

    def test_fifteenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v015/profile.md'
        path.write_text(path.read_text() + '\n第十五版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v016', root=self.root)

    def test_fourteenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v014/profile.md'
        path.write_text(path.read_text() + '\n第十四版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v015', root=self.root)

    def test_thirteenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v013/profile.md'
        path.write_text(path.read_text() + '\n第十三版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v014', root=self.root)

    def test_twelfth_version_change_is_rejected(self):
        path = self.root / 'analysis/v012/profile.md'
        path.write_text(path.read_text() + '\n第十二版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v013', root=self.root)

    def test_eleventh_version_change_is_rejected(self):
        path = self.root / 'analysis/v011/profile.md'
        path.write_text(path.read_text() + '\n第十一版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v012', root=self.root)

    def test_tenth_version_change_is_rejected(self):
        path = self.root / 'analysis/v010/profile.md'
        path.write_text(path.read_text() + '\n第十版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v011', root=self.root)

    def test_ninth_version_change_is_rejected(self):
        path = self.root / 'analysis/v009/profile.md'
        path.write_text(path.read_text() + '\n第九版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v010', root=self.root)

    def test_eighth_version_change_is_rejected(self):
        path = self.root / 'analysis/v008/profile.md'
        path.write_text(path.read_text() + '\n第八版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v009', root=self.root)

    def test_seventh_version_change_is_rejected(self):
        path = self.root / 'analysis/v007/profile.md'
        path.write_text(path.read_text() + '\n第七版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v008', root=self.root)

    def test_sixth_version_change_is_rejected(self):
        path = self.root / 'analysis/v006/profile.md'
        path.write_text(path.read_text() + '\n第六版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v007', root=self.root)

    def test_fifth_version_change_is_rejected(self):
        path = self.root / 'analysis/v005/profile.md'
        path.write_text(path.read_text() + '\n第五版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v006', root=self.root)

    def test_fourth_version_change_is_rejected(self):
        path = self.root / 'analysis/v004/profile.md'
        path.write_text(path.read_text() + '\n第四版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v005', root=self.root)

    def test_third_version_change_is_rejected(self):
        path = self.root / 'analysis/v003/profile.md'
        path.write_text(path.read_text() + '\n第三版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v004', root=self.root)

    def test_second_version_change_is_rejected(self):
        path = self.root / 'analysis/v002/profile.md'
        path.write_text(path.read_text() + '\n第二版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v003', root=self.root)

    def test_historical_artifact_change_is_rejected(self):
        path = self.root / 'analysis/v001/profile.md'
        path.write_text(path.read_text() + '\n初版を書き換える操作\n')
        with self.assertRaisesRegex(AssertionError, 'Historical version changed'):
            module.validate(version='v002', root=self.root)

    def test_invented_quote_is_rejected(self):
        path = self.root / 'analysis/v001/episodes.jsonl'
        episodes = [json.loads(line) for line in path.read_text().splitlines()]
        episodes[0]['evidence'][0]['quote'] = 'これは原文に存在しない捏造引用です'
        path.write_text(''.join(json.dumps(e, ensure_ascii=False) + '\n' for e in episodes))
        with self.assertRaisesRegex(AssertionError, 'Quote mismatch'):
            module.validate(root=self.root)

    def test_reserved_evidence_is_rejected(self):
        folder = self.root / 'analysis/v001'
        split = json.loads((folder / 'split.json').read_text())
        episode = json.loads((folder / 'episodes.jsonl').read_text().splitlines()[0])
        group = next(g for g in split['groups'] if g['group_id'] == episode['group_id'])
        count = len(group['segment_ids'])
        group['partition'] = 'reuse_reserve'
        (folder / 'split.json').write_text(json.dumps(split, ensure_ascii=False))
        manifest = json.loads((folder / 'manifest.json').read_text())
        manifest['analysis_pool_segment_count'] -= count
        manifest['reserve_segment_count'] += count
        (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False))
        with self.assertRaisesRegex(AssertionError, 'Reserved evidence'):
            module.validate(root=self.root)

    def test_unknown_evidence_is_rejected(self):
        path = self.root / 'analysis/v001/findings.json'
        findings = json.loads(path.read_text())
        findings['findings'][0]['support_episodes'].append('E999')
        path.write_text(json.dumps(findings, ensure_ascii=False))
        with self.assertRaisesRegex(AssertionError, 'Unknown episode'):
            module.validate(root=self.root)

    def test_excluded_question_cannot_support_finding(self):
        path = self.root / 'analysis/v001/findings.json'
        findings = json.loads(path.read_text())
        findings['findings'][0]['support_episodes'].append('E33')
        path.write_text(json.dumps(findings, ensure_ascii=False))
        with self.assertRaisesRegex(AssertionError, 'Excluded episode'):
            module.validate(root=self.root)


if __name__ == '__main__':
    unittest.main()
