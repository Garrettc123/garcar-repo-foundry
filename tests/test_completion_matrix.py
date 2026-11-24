import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'completion_matrix.py'
spec = importlib.util.spec_from_file_location('completion_matrix', MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def example():
    return {'repository_count': 2, 'observed_at_utc': '2026-11-22T00:00:00Z', 'repositories': [
        {'repository': 'Garrettc123/a', 'archived': False, 'candidate_lane': 'control_candidate', 'default_branch': 'main'},
        {'repository': 'Garrettc123/b', 'archived': True, 'candidate_lane': 'unassessed', 'default_branch': 'main'},
    ]}


class CompletionGateTests(unittest.TestCase):
    def test_unknown_repos_never_claim_ready(self):
        report = gate.build_matrix(example())
        self.assertEqual(report['production_ready_count_confirmed'], 0)
        self.assertEqual(report['status_counts']['UNINSPECTED'], 1)
        self.assertEqual(report['status_counts']['ARCHIVED_NOT_CERTIFIED'], 1)

    def test_github_urls_are_review_pointers_not_proof(self):
        evidence = {'Garrettc123/a': {
            'source_review': 'https://github.com/Garrettc123/a/blob/main/README.md',
            'test_run': 'https://github.com/Garrettc123/a/actions/runs/100',
            'runtime_receipt': 'https://github.com/Garrettc123/a/issues/1'}}
        report = gate.build_matrix(example(), evidence)
        self.assertEqual(report['repositories'][0]['status'], 'OPERATOR_REVIEW_REQUIRED')
        self.assertFalse(report['repositories'][0]['production_ready'])

    def test_refuse_count_mismatch_and_duplicates(self):
        item = example()
        item['repository_count'] = 3
        with self.assertRaises(ValueError):
            gate.build_matrix(item)
        item = example()
        item['repositories'][1]['repository'] = 'Garrettc123/a'
        with self.assertRaises(ValueError):
            gate.build_matrix(item)

    def test_refuse_untracked_evidence(self):
        with self.assertRaises(ValueError):
            gate.build_matrix(example(), {'Garrettc123/other': {'test_run': 'https://github.com/a'}})

    def test_write_parseable_report(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'fleet.json'
            gate.write_report(gate.build_matrix(example()), out)
            self.assertEqual(json.loads(out.read_text())['repository_count'], 2)


if __name__ == '__main__':
    unittest.main()
