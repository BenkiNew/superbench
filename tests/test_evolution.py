import json
import shutil
import tempfile
import unittest
from pathlib import Path

from superbench.core import BenchError, Incident, add_review, adjudicate, create_run, get_incident, write_json
from superbench.render import leaderboard
from superbench.experiments import prepare_control_pair, record_control_review, control_summary


class EvolutionTests(unittest.TestCase):
    def make_pair(self, root):
        good, bad = root / 'good.md', root / 'bad.md'
        good.write_text('Need fresh evidence before resolution.')
        bad.write_text('Incomplete empty results prove resolution.')
        return prepare_control_pair(get_incident('SB-004'), good, bad, 'premature-resolution', root / 'pair')

    def report(self, usable=True, detect=False):
        finding = [{'defect_id': 'premature-resolution', 'decision': 'confirmed', 'evidence': 'latest_scan.json:3-5 is incomplete'}] if detect else []
        return {'schema_version': 1, 'voices': [
            {'id': 'one', 'transport_status': 'completed', 'review': {'verdict': 'accepted', 'findings': finding}} if usable else {'id': 'one', 'transport_status': 'failed', 'error': 'timeout'},
            {'id': 'two', 'transport_status': 'completed', 'error': 'model unavailable'},
        ], 'cost_usd': None}

    def test_control_bundle_excludes_evaluation_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp))
            for sample in (pair / 'samples').iterdir():
                names = [p.name for p in sample.rglob('*')]
                self.assertNotIn('oracle.json', names)
                self.assertNotIn('evaluation.json', names)
                self.assertEqual(json.loads((sample / 'bundle.json').read_text())['case_version'], '1.0.0')
            with self.assertRaises(BenchError):
                self.make_pair(Path(tmp))

    def test_completed_without_review_is_not_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp)); key = json.loads((pair / 'evaluation.json').read_text())
            sample = next(iter(key['samples']))
            result = record_control_review(pair, sample, self.report())
            self.assertEqual(result['usable_voices'], 1)
            self.assertEqual(result['requested_voices'], 2)
            self.assertEqual(result['panel_status'], 'partial')
            self.assertIsNone(result['cost_usd'])

    def test_no_usable_voice_cannot_be_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp)); sample = next(iter(json.loads((pair / 'evaluation.json').read_text())['samples']))
            result = record_control_review(pair, sample, self.report(False))
            self.assertEqual(result['panel_status'], 'unavailable')
            self.assertIsNone(result['target_detected'])
            self.assertIsNone(result['control_rejected'])

    def test_pair_detects_injected_defect_and_keeps_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp)); key = json.loads((pair / 'evaluation.json').read_text())
            for sample, info in key['samples'].items():
                record_control_review(pair, sample, self.report(detect=info['expected'] == 'incorrect'))
            events = (pair / 'events.jsonl').read_bytes()
            sample = next(iter(key['samples'])); record_control_review(pair, sample, self.report())
            self.assertTrue((pair / 'events.jsonl').read_bytes().startswith(events))
            self.assertEqual(len(list((pair / 'reviews').glob('*.json'))), 3)
            summary = control_summary(pair)
            self.assertEqual(summary['samples_reviewed'], 2)
            self.assertFalse(summary['official_verdict'])

    def test_tampered_sample_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp)); sample = next(iter(json.loads((pair / 'evaluation.json').read_text())['samples']))
            (pair / 'samples' / sample / 'ANSWER.md').write_text('Changed')
            with self.assertRaises(BenchError):
                record_control_review(pair, sample, self.report())

    def test_duplicate_voices_and_failed_review_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp)); sample = next(iter(json.loads((pair / 'evaluation.json').read_text())['samples']))
            report = self.report(); report['voices'][1]['id'] = 'one'
            with self.assertRaises(BenchError): record_control_review(pair, sample, report)
            report = self.report(); report['voices'][0]['transport_status'] = 'failed'
            with self.assertRaises(BenchError): record_control_review(pair, sample, report)

    def test_requested_roster_cannot_hide_failed_voice(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = self.make_pair(Path(tmp))
            sample = next(iter(json.loads((pair / 'evaluation.json').read_text())['samples']))
            report = self.report()
            report['requested_voice_ids'] = ['one', 'two', 'missing']
            with self.assertRaises(BenchError):
                record_control_review(pair, sample, report)
            report['voices'].append({'id': 'missing', 'transport_status': 'failed', 'error': 'timeout'})
            event = record_control_review(pair, sample, report)
            self.assertEqual(event['requested_voices'], 3)
            self.assertEqual(event['usable_voices'], 1)
            self.assertEqual(event['panel_status'], 'partial')
            for roster in [['one', 'two', 'missing', 'one'], 'one', []]:
                report['requested_voice_ids'] = roster
                with self.assertRaises(BenchError):
                    record_control_review(pair, sample, report)

    def test_new_run_pins_case_and_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'source'; shutil.copytree(get_incident('SB-001').root, source)
            incident = Incident(source, json.loads((source / 'incident.json').read_text()))
            run = create_run(incident, 'candidate', 'answer', root / 'results')
            metadata = json.loads((run / 'response.json').read_text())
            self.assertEqual(metadata['case_version'], '1.0.0')
            self.assertTrue((run / 'benchmark' / 'oracle.json').exists())
            (source / 'oracle.json').write_text('{}')
            self.assertNotEqual((source / 'oracle.json').read_bytes(), (run / 'benchmark/oracle.json').read_bytes())

    def test_adjudication_history_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = create_run(get_incident('SB-001'), 'candidate', 'answer', Path(tmp))
            adjudicate(run); first = (run / 'adjudications/000001.json').read_bytes()
            adjudicate(run)
            self.assertEqual((run / 'adjudications/000001.json').read_bytes(), first)
            self.assertTrue((run / 'adjudications/000002.json').exists())

    def test_latest_adjudication_does_not_double_count_leaderboard(self):
        rows = [{'event': 'adjudication_finished', 'response_id': 'r', 'model': 'm', 'verdict': 'rejected'},
                {'event': 'adjudication_finished', 'response_id': 'r', 'model': 'm', 'verdict': 'confirmed'}]
        board = leaderboard(rows)
        self.assertEqual(board[0]['runs'], 1)
        self.assertEqual(board[0]['confirmed'], 1)

class HistoricalIntegrityTests(unittest.TestCase):
    def test_pending_panel_never_implies_successful_reliability(self):
        self.assertEqual(leaderboard([{'event': 'adjudication_finished', 'response_id': 'r',
                                      'model': 'm', 'verdict': 'pending'}]), [])

    def test_different_case_revision_gets_separate_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / 'case'; shutil.copytree(get_incident('SB-001').root, source)
            data = json.loads((source / 'incident.json').read_text())
            first = create_run(Incident(source, data), 'candidate', 'same answer', root / 'results')
            data['version'] = '1.0.1'; write_json(source / 'incident.json', data)
            second = create_run(Incident(source, data), 'candidate', 'same answer', root / 'results')
            self.assertNotEqual(first, second)
            self.assertEqual(json.loads((first / 'registration.json').read_text())['case_version'], '1.0.0')

    def test_reducer_uses_pinned_oracle_after_live_source_changes(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); run = create_run(get_incident('SB-001'), 'm', 'answer', root)
            rid = json.loads((run / 'response.json').read_text())['response_id']
            ids = ['skip-branch', 'log-filter', 'await-present', 'citations']
            for role in ['correctness', 'evidence', 'adversarial']:
                payload = {'challenges': []} if role == 'adversarial' else {'criteria': [
                    {'criterion_id': cid, 'status': 'met' if role == 'correctness' else 'valid'} for cid in ids]}
                review = {'schema_version': 1, 'response_id': rid, 'agent_role': role,
                          'agent_name': role, 'confidence': 1.0, **payload}
                path = root / (role + '.json'); write_json(path, review); add_review(run, path)
            with patch('superbench.core.get_incident', side_effect=BenchError('Live catalog unavailable')):
                self.assertEqual(adjudicate(run)['score'], 100)
            oracle = run / 'benchmark/oracle.json'; oracle.write_text('{}')
            with self.assertRaises(BenchError): adjudicate(run)

    def test_unknown_and_negative_cost_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = EvolutionTests(); pair = helper.make_pair(Path(tmp))
            sample = next(iter(json.loads((pair / 'evaluation.json').read_text())['samples']))
            for cost in [True, -1, float('nan'), float('inf')]:
                report = helper.report(); report['cost_usd'] = cost
                with self.assertRaises(BenchError): record_control_review(pair, sample, report)

    def test_missing_oracle_in_blinded_samples_but_evaluator_snapshot_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            pair = EvolutionTests().make_pair(Path(tmp))
            self.assertTrue((pair / 'benchmark/oracle.json').is_file())
            for sample in (pair / 'samples').iterdir():
                self.assertFalse((sample / 'oracle.json').exists())

    def test_review_output_in_sample_does_not_mutate_pinned_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            helper = EvolutionTests(); pair = helper.make_pair(Path(tmp))
            sample = next(iter(json.loads((pair / 'evaluation.json').read_text())['samples']))
            (pair / 'samples' / sample / 'REVIEW.md').write_text('Result')
            self.assertEqual(record_control_review(pair, sample, helper.report())['usable_voices'], 1)


class ResponseHashTests(unittest.TestCase):
    def test_registered_hash_matches_saved_answer(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            run = create_run(get_incident('SB-001'), 'm', 'answer  \n\n', Path(tmp))
            record = json.loads((run / 'registration.json').read_text())
            self.assertEqual(record['response_sha256'], hashlib.sha256((run / 'response.md').read_bytes()).hexdigest())


class LegacyHistoryTests(unittest.TestCase):
    def test_legacy_adjudication_is_archived_before_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = create_run(get_incident('SB-001'), 'legacy', 'answer', Path(tmp))
            record = json.loads((run / 'response.json').read_text())
            record.pop('benchmark_snapshot'); write_json(run / 'response.json', record)
            previous = {'schema_version': 1, 'verdict': 'confirmed', 'legacy_note': 'original'}
            write_json(run / 'adjudication.json', previous)
            original = (run / 'adjudication.json').read_bytes()
            result = adjudicate(run)
            self.assertEqual((run / 'adjudications/000001.json').read_bytes(), original)
            self.assertEqual(result['revision'], 2)
            self.assertEqual(result['provenance'], 'legacy-unpinned')

class LocaleTests(unittest.TestCase):
    def test_static_languages_share_assets_and_keep_catalog(self):
        from superbench.render import render_site
        from html.parser import HTMLParser
        from urllib.parse import urljoin, urlparse
        class Links(HTMLParser):
            def __init__(self):
                super().__init__(); self.styles = []; self.languages = {}; self.lang = None
            def handle_starttag(self, tag, attrs):
                data = dict(attrs)
                if tag == 'html': self.lang = data.get('lang')
                if tag == 'link' and data.get('rel') == 'stylesheet': self.styles.append(data['href'])
                if tag == 'a' and data.get('hreflang'): self.languages[data['hreflang']] = data['href']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); results = root / 'results'; results.mkdir()
            render_site(root / 'site', results)
            for locale, relative in [('uk', 'index.html'), ('en', 'en/index.html')]:
                html = (root / 'site' / relative).read_text(); links = Links(); links.feed(html)
                self.assertEqual(links.lang, locale)
                self.assertEqual(set(links.languages), {'uk', 'en'})
                base = 'https://example.test/superbench/' + ('en/' if locale == 'en' else '')
                self.assertEqual(urlparse(urljoin(base, links.styles[0])).path, '/superbench/assets/app.css')
                self.assertEqual(urlparse(urljoin(base, links.languages['en'])).path, '/superbench/en/')
                self.assertEqual(urlparse(urljoin(base, links.languages['uk'])).path, '/superbench/')
                self.assertIn('SB-014', html)
            self.assertFalse((root / 'site/en/assets').exists())


if __name__ == '__main__':
    unittest.main()
