"""Isolated tests for the first scene registry and coverage checks."""
import contextlib
import csv
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from pipeline.scene_validation import parse_csv_sections, validate_scenes
from pipeline.validate import main as validate_repository


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'scenes' / 'coverage' / 'complete'


class SceneValidationTests(unittest.TestCase):
    def test_nonempty_coverage_cannot_substitute_audio_for_video(self):
        scenes = self.read_rows('scenes/index.csv')
        (self.root / 'scenes/index.csv').write_text(
            ','.join(scenes[0].keys()) + '\n', encoding='utf-8')
        media = self.read_rows('source/media.csv')
        self.write_rows('source/media.csv', media + [dict(media[0], id='audio')])
        timing = self.read_rows('source/timing.csv')
        self.write_rows('source/timing.csv', timing + [dict(
            timing[0], source_id='audio', reference_source_id='video', offset='0')])
        row = self.read_rows('scenes/coverage.csv')[0]
        self.write_rows('scenes/coverage.csv', [dict(
            row, source_id='audio', start='00:00:00.000', end='00:02:00.000',
            kind='unresolved', scene_id='')])
        with self.assertRaisesRegex(ValueError, 'video'):
            validate_scenes(self.root)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'fixture-root'
        shutil.copytree(FIXTURE, self.root)
        changes = self.root / 'scenes' / 'changes'
        changes.mkdir(exist_ok=True)
        (changes / 'index.csv').write_text(
            'change_id,type,state,from_scene,from_revision,to_scene,to_revision,record\n',
            encoding='utf-8')

    def read_rows(self, relative_path):
        path = self.root / relative_path
        with path.open(encoding='utf-8-sig', newline='') as handle:
            return list(csv.DictReader(handle))

    def write_rows(self, relative_path, rows):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def test_complete_coverage_reports_unresolved_work(self):
        messages = validate_scenes(self.root)
        self.assertTrue(any('20' in message and 'Нерозібраний' in message
                            for message in messages))
        self.assertFalse(any('покриття не побудовано' in message for message in messages))

    def test_empty_scene_set_may_omit_new_registries(self):
        empty_root = Path(self.temp.name) / 'empty-root'
        empty_root.mkdir()

        messages = validate_scenes(empty_root)

        self.assertTrue(any('покриття не побудовано' in message for message in messages))

    def test_gaps_and_overlaps_are_rejected(self):
        coverage = self.read_rows('scenes/coverage.csv')
        coverage[0]['end'] = '00:00:19.000'
        self.write_rows('scenes/coverage.csv', coverage)
        with self.assertRaisesRegex(ValueError, 'gap|overlap|contiguous|continuous'):
            validate_scenes(self.root)

        coverage = self.read_rows('scenes/coverage.csv')
        coverage[0]['end'] = '00:00:21.000'
        self.write_rows('scenes/coverage.csv', coverage)
        with self.assertRaisesRegex(ValueError, 'gap|overlap|contiguous|continuous'):
            validate_scenes(self.root)

    def test_scene_and_source_references_must_resolve(self):
        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['source_id'] = 'missing-source'
        self.write_rows('scenes/index.csv', scenes)
        with self.assertRaisesRegex(ValueError, 'source|timing'):
            validate_scenes(self.root)

        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['source_id'] = 'video'
        self.write_rows('scenes/index.csv', scenes)
        coverage = self.read_rows('scenes/coverage.csv')
        coverage[1]['scene_id'] = 'S999'
        self.write_rows('scenes/coverage.csv', coverage)
        with self.assertRaisesRegex(ValueError, 'scene|S999'):
            validate_scenes(self.root)

    def test_nonempty_scene_set_requires_coverage_and_timing(self):
        (self.root / 'scenes' / 'coverage.csv').unlink()
        with self.assertRaisesRegex(ValueError, 'coverage'):
            validate_scenes(self.root)

        shutil.copy2(FIXTURE / 'scenes' / 'coverage.csv',
                     self.root / 'scenes' / 'coverage.csv')
        (self.root / 'source' / 'timing.csv').unlink()
        with self.assertRaisesRegex(ValueError, 'timing'):
            validate_scenes(self.root)

    def test_status_lifecycle_revision_and_duration_are_validated(self):
        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['status'] = 'complete'
        self.write_rows('scenes/index.csv', scenes)
        with self.assertRaisesRegex(ValueError, 'status'):
            validate_scenes(self.root)

        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['status'] = 'verified'
        scenes[0]['lifecycle'] = 'retired'
        self.write_rows('scenes/index.csv', scenes)
        with self.assertRaisesRegex(ValueError, 'lifecycle'):
            validate_scenes(self.root)

        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['status'] = 'verified'
        scenes[0]['lifecycle'] = 'active'
        scenes[0]['revision'] = '0'
        self.write_rows('scenes/index.csv', scenes)
        with self.assertRaisesRegex(ValueError, 'revision'):
            validate_scenes(self.root)

        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['status'] = 'verified'
        scenes[0]['lifecycle'] = 'active'
        scenes[0]['revision'] = '1'
        self.write_rows('scenes/index.csv', scenes)
        timing = self.read_rows('source/timing.csv')
        timing[0]['duration'] = '00:01:59.999'
        self.write_rows('source/timing.csv', timing)
        with self.assertRaisesRegex(ValueError, 'duration|end|interval'):
            validate_scenes(self.root)

    def test_active_scene_requires_one_matching_coverage_segment(self):
        coverage = self.read_rows('scenes/coverage.csv')
        duplicate = dict(coverage[1])
        duplicate['id'] = 'C005'
        coverage.append(duplicate)
        self.write_rows('scenes/coverage.csv', coverage)
        with self.assertRaisesRegex(ValueError, 'scene.*coverage|coverage.*scene'):
            validate_scenes(self.root)

    def test_coverage_kind_is_an_explicit_enum(self):
        coverage = self.read_rows('scenes/coverage.csv')
        coverage[0]['kind'] = 'intro'
        self.write_rows('scenes/coverage.csv', coverage)
        with self.assertRaisesRegex(ValueError, 'kind'):
            validate_scenes(self.root)

    def test_exact_registry_headers_are_required(self):
        path = self.root / 'scenes' / 'index.csv'
        text = path.read_text(encoding='utf-8')
        path.write_text(text.replace('id,title,start,end,status,source_id,lifecycle,revision,package',
                                     'id,title,start,end,status'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'header|column'):
            validate_scenes(self.root)


class GeneralValidatorIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.make_root()

    def make_csv(self, relative_path, header, rows=()):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    def make_root(self):
        self.make_csv('glossary.csv', ['id'])
        self.make_csv('characters/index.csv', ['id', 'in_script', 'in_film', 'in_credits',
                                                'credit_id', 'credit_name', 'script_name'])
        self.make_csv('source/cast-credits.csv', ['id', 'character_id', 'kind', 'role', 'timecode'])
        self.make_csv('source/keyframes.csv', ['timecode'])
        self.make_csv('source/credits-evidence.csv', ['id', 'timecode', 'local_file', 'sha256'])
        self.make_csv('pilots/P001/en/exchange.csv', ['start', 'end'])

        # Intentionally malformed fixture files must only be read by isolated tests.
        self.make_csv('tests/fixtures/bad.csv', ['id'], [['duplicate'], ['duplicate']])
        fixture_json = self.root / 'tests' / 'fixtures' / 'bad.json'
        fixture_json.parent.mkdir(parents=True, exist_ok=True)
        fixture_json.write_text('{invalid json', encoding='utf-8')

    def test_general_validation_ignores_only_tests_fixtures(self):
        with contextlib.redirect_stdout(io.StringIO()):
            validate_repository(root=self.root)

        self.make_csv('canonical.csv', ['id'], [['duplicate'], ['duplicate']])
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, 'Duplicate id'):
                validate_repository(root=self.root)

    def test_general_json_scan_still_rejects_invalid_canonical_json(self):
        (self.root / 'tests' / 'fixtures' / 'bad.json').unlink()
        (self.root / 'canonical.json').write_text('{invalid json', encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(json.JSONDecodeError):
                validate_repository(root=self.root)


class ChangeValidationTests(unittest.TestCase):
    setUp = SceneValidationTests.setUp
    read_rows = SceneValidationTests.read_rows
    write_rows = SceneValidationTests.write_rows

    def test_retired_id_cannot_return_through_a_disconnected_root(self):
        old = self.snapshot('S001')
        left = self.snapshot('S003', end='00:00:40.000')
        right = self.snapshot('S004', start='00:00:40.000')
        self.change('CH001', 'split', [old], [left, right])
        forged = self.snapshot('S001', 2, start='00:00:00.000', end='00:00:20.000')
        revived = self.snapshot('S001', 3, start='00:00:00.000', end='00:00:20.000')
        self.change('CH002', 'boundary', [forged], [revived])
        self.current([revived, left, right])
        # The resurrected ID takes the formerly unresolved interval, so coverage
        # is valid and cannot mask the disconnected version history.
        self.write_rows('scenes/coverage.csv', [row for row in self.read_rows(
            'scenes/coverage.csv') if row['kind'] != 'unresolved'])
        with self.assertRaisesRegex(ValueError, 'root|корен|revision'):
            validate_scenes(self.root)

    def snapshot(self, scene_id, revision=1, start='00:00:20.000', end='00:01:00.000'):
        return (scene_id, str(revision), 'video', start, end)

    def change(self, change_id, kind, before, after, state='applied', decision=None):
        directory = self.root / 'scenes' / 'changes'
        directory.mkdir(exist_ok=True)
        path = directory / f'{change_id}.md'
        decision = decision or ('accepted' if state == 'applied' else 'pending')
        parts = ['# Умовна зміна; не факт фільму\n']
        for title, header, rows in [
            ('Change metadata', ['change_id', 'type', 'state', 'decision'],
             [(change_id, kind, state, decision)]),
            ('Before', ['scene_id', 'revision', 'source_id', 'start', 'end'], before),
            ('After', ['scene_id', 'revision', 'source_id', 'start', 'end'], after),
        ]:
            stream = io.StringIO(newline='')
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(header)
            writer.writerows(rows)
            parts.append(f'## {title}\n\n```csv\n{stream.getvalue()}```\n')
        parts.append(
            '## Матеріали та пакети\n\n'
            'Умовний приклад: окремих canonical-реплік і медіа у цьому наборі немає. '
            'Реєстрові межі перенесено зі snapshots; package порожній для всіх сцен. '
            'Новий монтаж і неперевірені результати потребують окремого приймання.\n'
        )
        path.write_text('\n'.join(parts), encoding='utf-8')
        index = directory / 'index.csv'
        edges = self.read_rows('scenes/changes/index.csv') if index.exists() else []
        for old in before:
            for new in after:
                edges.append(dict(zip(
                    ['change_id', 'type', 'state', 'from_scene', 'from_revision',
                     'to_scene', 'to_revision', 'record'],
                    [change_id, kind, state, old[0], old[1], new[0], new[1],
                     f'scenes/changes/{change_id}.md'],
                )))
        self.write_rows('scenes/changes/index.csv', edges)
        return path

    def current(self, snapshots, superseded=()):
        rows = []
        coverage = self.read_rows('scenes/coverage.csv')
        for snapshot in snapshots:
            scene_id, revision, source, start, end = snapshot
            rows.append(dict(zip(
                ['id', 'title', 'start', 'end', 'status', 'source_id',
                 'lifecycle', 'revision', 'package'],
                [scene_id, 'Умовна сцена', start, end, 'draft', source,
                 'superseded' if scene_id in superseded else 'active', revision, ''],
            )))
        # Preserve S002 and the unresolved/credits ranges from the 120 s example.
        rows.append(self.read_rows('scenes/index.csv')[-1])
        self.write_rows('scenes/index.csv', rows)
        segments = [coverage[0]]
        for row in rows:
            if row['lifecycle'] == 'active':
                segments.append(dict(zip(
                    coverage[0].keys(),
                    [f'C{len(segments) + 1:03d}', row['source_id'], row['start'],
                     row['end'], 'scene', row['id'], 'draft', ''],
                )))
        segments.append(dict(coverage[-1], id=f'C{len(segments) + 1:03d}'))
        self.write_rows('scenes/coverage.csv', segments)

    def test_proposed_boundary_split_merge_and_rejected_reservations(self):
        old = self.snapshot('S001')
        self.change('CH001', 'boundary', [old], [self.snapshot('S001', 2)],
                    state='proposed')
        self.change('CH002', 'split', [old],
                    [self.snapshot('S003', end='00:00:40.000'),
                     self.snapshot('S004', start='00:00:40.000')],
                    state='proposed', decision='rejected')
        self.change('CH003', 'merge', [old, self.snapshot(
            'S002', start='00:01:00.000', end='00:01:50.000')],
                    [self.snapshot('S005', end='00:01:50.000')], state='proposed')
        validate_scenes(self.root)
        self.assertEqual([row['id'] for row in self.read_rows('scenes/index.csv')],
                         ['S001', 'S002'])

    def test_split_merge_split_history_uses_historical_snapshots(self):
        a = self.snapshot('S001')
        b = self.snapshot('S003', end='00:00:40.000')
        c = self.snapshot('S004', start='00:00:40.000')
        d = self.snapshot('S005')
        e = self.snapshot('S006', end='00:00:45.000')
        f = self.snapshot('S007', start='00:00:45.000')
        self.change('CH001', 'split', [a], [b, c])
        self.change('CH002', 'merge', [b, c], [d])
        self.change('CH003', 'split', [d], [e, f])
        self.current([a, b, c, d, e, f], superseded=('S001', 'S003', 'S004', 'S005'))
        validate_scenes(self.root)

    def test_boundary_of_both_neighbors_and_stale_pending_warning(self):
        old = self.snapshot('S001')
        next_old = self.snapshot('S002', start='00:01:00.000', end='00:01:50.000')
        new = self.snapshot('S001', 2, end='00:01:05.000')
        next_new = self.snapshot('S002', 2, start='00:01:05.000', end='00:01:50.000')
        self.change('CH001', 'boundary', [old], [new])
        self.change('CH002', 'boundary', [next_old], [next_new])
        self.change('CH003', 'boundary', [old], [self.snapshot('S001', 3)],
                    state='proposed')
        scenes = self.read_rows('scenes/index.csv')
        scenes[0].update(end=new[4], revision='2')
        scenes[1].update(start=next_new[3], revision='2')
        self.write_rows('scenes/index.csv', scenes)
        coverage = self.read_rows('scenes/coverage.csv')
        coverage[1]['end'] = new[4]
        coverage[2]['start'] = next_new[3]
        self.write_rows('scenes/coverage.csv', coverage)
        messages = validate_scenes(self.root)
        self.assertTrue(any('CH003' in message and 'застаріла' in message
                            for message in messages))

    def test_applied_successors_must_be_registered(self):
        self.change('CH001', 'split', [self.snapshot('S001')],
                    [self.snapshot('S003'), self.snapshot('S004')])
        with self.assertRaisesRegex(ValueError, 'registered|реєстр|successor'):
            validate_scenes(self.root)

    def test_rejected_id_cannot_be_reissued(self):
        self.change('CH001', 'split', [self.snapshot('S001')],
                    [self.snapshot('S003'), self.snapshot('S004')],
                    state='proposed', decision='rejected')
        self.change('CH002', 'split', [self.snapshot('S001')],
                    [self.snapshot('S003'), self.snapshot('S005')], state='proposed')
        with self.assertRaisesRegex(ValueError, 'reserv|new ID'):
            validate_scenes(self.root)

    def test_diamond_replacing_and_creating_versions_is_rejected(self):
        for number, old, new in [
            (1, 1, 2), (2, 1, 3), (3, 2, 4), (4, 3, 4),
        ]:
            self.change(f'CH{number:03d}', 'boundary',
                        [self.snapshot('S001', old)], [self.snapshot('S001', new)])
        with self.assertRaisesRegex(ValueError, 'creating|replacing'):
            validate_scenes(self.root)

    def test_two_changes_cannot_create_the_same_version(self):
        self.change('CH001', 'boundary', [self.snapshot('S001', 1)],
                    [self.snapshot('S001', 4)])
        self.change('CH002', 'boundary', [self.snapshot('S001', 2)],
                    [self.snapshot('S001', 4)])
        with self.assertRaisesRegex(ValueError, 'creating'):
            validate_scenes(self.root)

    def test_invalid_change_shapes_and_decisions(self):
        path = self.change('CH001', 'split', [self.snapshot('S001')],
                           [self.snapshot('S003')], state='proposed')
        with self.assertRaisesRegex(ValueError, 'cardinality|split'):
            validate_scenes(self.root)
        path.write_text(path.read_text('utf-8').replace('split,proposed,pending',
                                                      'split,proposed,accepted'),
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'decision'):
            validate_scenes(self.root)

    def test_conflicting_existing_snapshot_and_unknown_before(self):
        self.change('CH001', 'boundary', [self.snapshot('S001', end='00:00:59.000')],
                    [self.snapshot('S001', 2)], state='proposed')
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            validate_scenes(self.root)

    def test_snapshot_sets_and_edge_metadata_must_match(self):
        path = self.change('CH001', 'boundary', [self.snapshot('S001')],
                           [self.snapshot('S001', 2)], state='proposed')
        path.write_text(path.read_text('utf-8').replace('S001,2,video', 'S001,3,video'),
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'snapshot|edges'):
            validate_scenes(self.root)

    def test_duplicate_edges_and_inconsistent_metadata(self):
        self.change('CH001', 'split', [self.snapshot('S001')],
                    [self.snapshot('S003'), self.snapshot('S004')], state='proposed')
        edges = self.read_rows('scenes/changes/index.csv')
        self.write_rows('scenes/changes/index.csv', edges + [dict(edges[0])])
        with self.assertRaisesRegex(ValueError, 'duplicate.*edge'):
            validate_scenes(self.root)
        edges[1]['state'] = 'applied'
        self.write_rows('scenes/changes/index.csv', edges)
        with self.assertRaisesRegex(ValueError, 'metadata'):
            validate_scenes(self.root)

    def test_missing_record_unknown_before_and_duplicate_snapshot(self):
        path = self.change('CH001', 'boundary', [self.snapshot('S999')],
                           [self.snapshot('S999', 2)], state='proposed')
        original = path.read_text('utf-8')
        with self.assertRaisesRegex(ValueError, 'unknown Before'):
            validate_scenes(self.root)
        path.write_text(original.replace(
            'S999,1,video,00:00:20.000,00:01:00.000',
            'S999,1,video,00:00:20.000,00:01:00.000\n'
            'S999,1,video,00:00:20.000,00:01:00.000'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'duplicate snapshot'):
            validate_scenes(self.root)
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'file path'):
            validate_scenes(self.root)

    def test_proposed_after_cannot_establish_another_before(self):
        self.change('CH001', 'boundary', [self.snapshot('S001')],
                    [self.snapshot('S001', 2)], state='proposed')
        self.change('CH002', 'boundary', [self.snapshot('S001', 2)],
                    [self.snapshot('S001', 3)], state='proposed')
        with self.assertRaisesRegex(ValueError, 'unknown Before'):
            validate_scenes(self.root)

    def test_applied_cycle_and_lifecycle_conflict(self):
        old = self.snapshot('S001')
        left = self.snapshot('S003', end='00:00:40.000')
        right = self.snapshot('S004', start='00:00:40.000')
        self.change('CH001', 'split', [old], [left, right])
        self.change('CH002', 'merge', [left, right], [old])
        with self.assertRaisesRegex(ValueError, 'cycle'):
            validate_scenes(self.root)

    def test_registered_proposed_successor_and_invalid_revision(self):
        self.change('CH001', 'split', [self.snapshot('S001')],
                    [self.snapshot('S003', 2), self.snapshot('S004')],
                    state='proposed')
        with self.assertRaisesRegex(ValueError, 'revision'):
            validate_scenes(self.root)

    def test_proposed_successor_cannot_already_be_in_the_registry(self):
        self.change('CH001', 'split', [self.snapshot('S001')],
                    [self.snapshot('S003'), self.snapshot('S002')], state='proposed')
        with self.assertRaisesRegex(ValueError, 'new ID already exists'):
            validate_scenes(self.root)

    def test_superseded_lifecycle_requires_an_applied_replacement(self):
        scenes = self.read_rows('scenes/index.csv')
        scenes[0]['lifecycle'] = 'superseded'
        self.write_rows('scenes/index.csv', scenes)
        coverage = self.read_rows('scenes/coverage.csv')
        coverage[1].update(kind='unresolved', scene_id='')
        self.write_rows('scenes/coverage.csv', coverage)
        with self.assertRaisesRegex(ValueError, 'lifecycle'):
            validate_scenes(self.root)

    def test_applied_boundary_cannot_leave_old_current_revision(self):
        self.change('CH001', 'boundary', [self.snapshot('S001')],
                    [self.snapshot('S001', 2)])
        with self.assertRaisesRegex(ValueError, 'After|revision'):
            validate_scenes(self.root)

    def test_split_cannot_resurrect_a_predecessor_with_an_unlinked_revision(self):
        old = self.snapshot('S001')
        left = self.snapshot('S003', end='00:00:40.000')
        right = self.snapshot('S004', start='00:00:40.000')
        self.change('CH001', 'split', [old], [left, right])
        # Keep the predecessor without coverage but forge a disconnected r10.
        self.current([self.snapshot('S001', 10), left, right], superseded=('S001',))
        with self.assertRaisesRegex(ValueError, 'revision'):
            validate_scenes(self.root)

class MarkdownParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'CH001.md'
        self.original = (
            '# Conditional record\n\n## Change metadata\n\n```csv\n'
            'change_id,type,state,decision\nCH001,boundary,proposed,pending\n```\n'
            '## Before\n```csv\nscene_id,revision,source_id,start,end\n'
            'S001,1,video,00:00:20.000,00:01:00.000\n```\n'
            '## After\n```csv\nscene_id,revision,source_id,start,end\n'
            'S001,2,video,00:00:20.000,00:01:05.000\n```\n'
        )
        self.schemas = {
            'Change metadata': ('change_id', 'type', 'state', 'decision'),
            'Before': ('scene_id', 'revision', 'source_id', 'start', 'end'),
            'After': ('scene_id', 'revision', 'source_id', 'start', 'end'),
        }

    def test_exact_sections_are_read_without_interpreting_other_code(self):
        self.path.write_text(self.original + '\n```text\n## Before\n```\n',
                             encoding='utf-8')
        result = parse_csv_sections(self.path, self.schemas)
        self.assertEqual(result['After'][0]['revision'], '2')

    def test_complete_editorial_fixture_has_exact_structural_blocks(self):
        fixture = ROOT / 'tests' / 'fixtures' / 'scenes' / 'changes' / 'proposed-boundary.md'
        result = parse_csv_sections(fixture, self.schemas)
        self.assertEqual(result['Change metadata'][0]['decision'], 'pending')

    def test_invalid_sections_and_csv_are_rejected(self):
        variants = [
            self.original.replace('## Before', '## Not Before'),
            self.original + '\n## Before\n```csv\nx\n```\n',
            self.original.replace('## Before\n```csv', '## Before\nprose\n```csv'),
            self.original.rsplit('```', 1)[0],
            self.original.replace('S001,2,video', '"S001,2,video'),
            self.original.replace('S001,2,video', ' S001,2,video'),
            self.original.replace('S001,2,video', '\nS001,2,video'),
            self.original.replace('S001,2,video', 'S001,2,video,extra'),
            self.original.replace('S001,2,video', '"S001\ncontinued",2,video'),
        ]
        for text in variants:
            with self.subTest(text=text):
                self.path.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    parse_csv_sections(self.path, self.schemas)


class DialogueAndPackageTests(unittest.TestCase):
    read_rows = SceneValidationTests.read_rows
    write_rows = SceneValidationTests.write_rows

    def setUp(self):
        SceneValidationTests.setUp(self)
        shutil.copytree(ROOT / 'tests' / 'fixtures' / 'scenes' / 'dialogue' / 'relocated',
                        self.root, dirs_exist_ok=True)

    def line(self, **updates):
        relative = 'scenes/S002/dialogue.uk.csv'
        rows = self.read_rows(relative)
        rows[0].update(updates)
        self.write_rows(relative, rows)

    def test_relocated_id_chorus_and_pilot_time_are_preserved(self):
        validate_scenes(self.root)
        self.assertEqual(self.read_rows('scenes/S002/dialogue.uk.csv')[0]['id'], 'S001-L001')

    def test_split_moves_original_id_to_s004_without_breaking_language_refs(self):
        original_rows = self.read_rows('scenes/S002/dialogue.uk.csv')
        original_rows[0].update(start='00:00:40.000', end='00:00:42.000')
        self.write_rows('scenes/S001/dialogue.uk.csv', original_rows)
        (self.root / 'scenes' / 'S002' / 'dialogue.uk.csv').unlink()
        validate_scenes(self.root)
        helper = ChangeValidationTests()
        helper.root = self.root
        old = helper.snapshot('S001')
        left = helper.snapshot('S003', end='00:00:40.000')
        right = helper.snapshot('S004', start='00:00:40.000')
        record = helper.change('CH001', 'split', [old], [left, right])
        helper.current([old, left, right], superseded=('S001',))
        target = self.root / 'scenes' / 'S004' / 'dialogue.uk.csv'
        target.parent.mkdir()
        original = self.root / 'scenes' / 'S001' / 'dialogue.uk.csv'
        rows = self.read_rows('scenes/S001/dialogue.uk.csv')
        self.write_rows('scenes/S004/dialogue.uk.csv', rows)
        original.unlink()
        record.write_text(
            record.read_text('utf-8').replace(
                'окремих canonical-реплік і медіа у цьому наборі немає.',
                'єдина canonical-репліка S001-L001 має долю нижче; медіа немає.'
            ) + '\n## Перенесена репліка\n\n'
            '| old_ref | new_ref | decision | recheck |\n'
            '| --- | --- | --- | --- |\n'
            '| scenes/S001/dialogue.uk.csv#S001-L001 | '
            'scenes/S004/dialogue.uk.csv#S001-L001 | Перенесено без зміни ID | '
            'Новий монтаж не погоджено |\n', encoding='utf-8')
        validate_scenes(self.root)
        self.assertEqual(self.read_rows('languages/en/performed.csv')[0]['source_id'], 'S001-L001')
        self.assertEqual(self.read_rows('scenes/S004/dialogue.uk.csv'), original_rows)

    def test_duplicate_canonical_ids_include_pilots(self):
        rows = self.read_rows('scenes/S002/dialogue.uk.csv')
        rows[0]['id'] = 'P001-L001'
        self.write_rows('scenes/S002/dialogue.uk.csv', rows)
        with self.assertRaisesRegex(ValueError, 'duplicate canonical'):
            validate_scenes(self.root)

    def test_dangling_translation_or_performed_source_is_rejected(self):
        for filename in ('dialogue.csv', 'performed.csv'):
            with self.subTest(filename=filename):
                path = f'languages/en/{filename}'
                rows = self.read_rows(path)
                original = [dict(row) for row in rows]
                rows[0]['source_id'] = 'missing-line'
                self.write_rows(path, rows)
                with self.assertRaisesRegex(ValueError, 'source_id'):
                    validate_scenes(self.root)
                self.write_rows(path, original)

    def test_unknown_needs_note_and_accepted_limitation_for_verified(self):
        self.line(speaker='unknown', note='Мовець за кадром; не встановлений.')
        validate_scenes(self.root)
        self.line(note='')
        with self.assertRaisesRegex(ValueError, 'note'):
            validate_scenes(self.root)
        self.line(note='Мовець не встановлений.', status='verified')
        with self.assertRaisesRegex(ValueError, 'limitation|обмеження'):
            validate_scenes(self.root)
        (self.root / 'scenes' / 'S002' / 'README.md').write_text(
            '# Умовний тест\n\n## Приймання\n\n'
            'S001-L001: прийняте обмеження — текст перевірено, мовець unknown '
            'залишається непевним. Це лише умовний запис тесту.\n', encoding='utf-8')
        validate_scenes(self.root)

    def test_unknown_chorus_member_and_bad_status_are_rejected(self):
        self.line(speaker='pronya+missing')
        with self.assertRaisesRegex(ValueError, 'speaker'):
            validate_scenes(self.root)
        self.line(speaker='pronya', status='ready')
        with self.assertRaisesRegex(ValueError, 'status'):
            validate_scenes(self.root)

    def test_generic_acceptance_table_is_not_an_explicit_limitation(self):
        self.line(speaker='unknown', note='Мовець ще невідомий.', status='verified')
        (self.root / 'scenes' / 'S002' / 'README.md').write_text(
            '# Умовний шаблон приймання\n\n'
            '| ID | Прийняте обмеження / блокер | Стан |\n'
            '| --- | --- | --- |\n'
            '| S001-L001 | Потребує перевірки | draft |\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'limitation|обмеження'):
            validate_scenes(self.root)

    def test_editorial_decisions_are_affirmative_and_bound_to_their_own_id(self):
        owner = self.root / 'scenes' / 'S002' / 'README.md'
        for marker, updates, error in (
                ('прийняте обмеження', dict(speaker='unknown', status='verified',
                                           note='Непевний мовець.'), 'limitation|обмеження'),
                ('виняток часової належності', dict(start='00:00:59.000',
                     end='00:01:02.000'), 'README|boundary')):
            rows = self.read_rows('scenes/S002/dialogue.uk.csv')
            original = [dict(row) for row in rows]
            self.line(**updates)
            neighbor = self.root / 'scenes' / 'S001'
            neighbor.mkdir(exist_ok=True)
            (neighbor / 'README.md').write_text(
                'Контекст: [S001-L001](../S002/dialogue.uk.csv#S001-L001).',
                encoding='utf-8')
            for claim in (
                    f'S001-L001: {marker} — не погоджено; очікуємо рішення.',
                    f'S001-L001: {marker} —\nне погоджено; очікуємо рішення.',
                    f'Приклад, рішення ще не прийнято: `S001-L001: {marker} — причина`.',
                    f'Приклад: ``S001-L001: {marker} — причина з `літералом` ``.',
                    f'Приклад: `S001-L001: {marker} —\nпричина в коді`.',
                    f'<!-- S001-L001: {marker} — прихований приклад -->',
                    f'S001-L002: {marker} — дозволено з причиною. '
                    'S001-L001: обмеження ще не погоджено.'):
                with self.subTest(marker=marker, claim=claim):
                    owner.write_text(claim, encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, error):
                        validate_scenes(self.root)
            owner.write_text(
                'S001-L002: обмеження не погоджено. '
                f'S001-L001: {marker} — явна причина цього запису.', encoding='utf-8')
            validate_scenes(self.root)
            owner.write_text(f'S001-L001: {marker} —\nявна причина з `терміном`.',
                             encoding='utf-8')
            validate_scenes(self.root)
            self.write_rows('scenes/S002/dialogue.uk.csv', original)

    def test_audio_plus_two_requires_verified_timing(self):
        media = self.read_rows('source/media.csv')
        media.append(dict(media[0], id='audio'))
        self.write_rows('source/media.csv', media)
        timing = self.read_rows('source/timing.csv')
        timing.append(dict(timing[0], source_id='audio', reference_source_id='video', offset='2'))
        self.write_rows('source/timing.csv', timing)
        self.line(source_id='audio', start='00:00:58.000', end='00:01:00.000')
        validate_scenes(self.root)
        timing[1]['offset'] = '0'
        self.write_rows('source/timing.csv', timing)
        with self.assertRaisesRegex(ValueError, 'overlap|boundary'):
            validate_scenes(self.root)
        self.write_rows('source/timing.csv', timing[:1])
        with self.assertRaisesRegex(ValueError, 'timing'):
            validate_scenes(self.root)

    def test_crossing_requires_explanation_and_neighbor_context_link(self):
        self.line(start='00:00:59.000', end='00:01:02.000')
        with self.assertRaisesRegex(ValueError, 'cross|належності|boundary'):
            validate_scenes(self.root)
        owner = self.root / 'scenes' / 'S002' / 'README.md'
        owner.write_text(
            '# Умовний тест\n\n## Відкриті питання\n\n'
            'S001-L001: виняток часової належності — початок репліки у S001; '
            'основний власник S002, не розрізаємо виконання.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'context|контекст'):
            validate_scenes(self.root)
        neighbor = self.root / 'scenes' / 'S001'
        neighbor.mkdir(exist_ok=True)
        (neighbor / 'README.md').write_text(
            '# Умовний тест\n\nКонтекст: [S001-L001](../S002/dialogue.uk.csv#S001-L001), '
            'основний власник S002.\n', encoding='utf-8')
        validate_scenes(self.root)

    def test_note_alone_cannot_authorize_a_boundary_exception(self):
        self.line(start='00:00:59.000', end='00:01:02.000',
                  note='Виняток часової належності; дозволено.')
        with self.assertRaisesRegex(ValueError, 'README'):
            validate_scenes(self.root)

    def test_crossing_into_credits_needs_an_explicit_owner_explanation(self):
        self.line(start='00:01:49.000', end='00:01:51.000')
        with self.assertRaisesRegex(ValueError, 'README'):
            validate_scenes(self.root)
        (self.root / 'scenes' / 'S002' / 'README.md').write_text(
            '# Умовний тест\n\nS001-L001: виняток часової належності — '
            'репліка закінчується під час титрів; основний власник S002.\n',
            encoding='utf-8')
        validate_scenes(self.root)

    def test_unaccepted_unknown_limitation_is_not_approval(self):
        self.line(speaker='unknown', status='approved', note='Непевний мовець.')
        for text in (
            'S001-L001: не прийняте обмеження; потрібне рішення.',
            'S001-L001: потрібне явне прийняте обмеження для цього мовця.',
            'S001-L001: прийняте обмеження? Ще очікуємо відповідь.',
        ):
            with self.subTest(text=text):
                (self.root / 'scenes' / 'S002' / 'README.md').write_text(
                    f'# Умовний тест\n\n{text}\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'limitation|обмеження'):
                    validate_scenes(self.root)

    def test_wrong_audio_reference_and_invalid_offset(self):
        media = self.read_rows('source/media.csv')
        media.append(dict(media[0], id='audio'))
        self.write_rows('source/media.csv', media)
        timing = self.read_rows('source/timing.csv')
        timing.append(dict(timing[0], source_id='audio', reference_source_id='audio', offset='0'))
        self.write_rows('source/timing.csv', timing)
        with self.assertRaisesRegex(ValueError, 'reference video'):
            validate_scenes(self.root)
        timing[1].update(reference_source_id='video', offset='nan')
        self.write_rows('source/timing.csv', timing)
        with self.assertRaisesRegex(ValueError, 'offset'):
            validate_scenes(self.root)

    def test_fractional_audio_offset_is_exact_at_the_scene_boundary(self):
        media = self.read_rows('source/media.csv')
        media.append(dict(media[0], id='audio'))
        self.write_rows('source/media.csv', media)
        timing = self.read_rows('source/timing.csv')
        timing.append(dict(timing[0], source_id='audio', reference_source_id='video',
                           offset='+2.001'))
        self.write_rows('source/timing.csv', timing)
        self.line(source_id='audio', start='00:00:57.999', end='00:00:59.999')
        validate_scenes(self.root)

    def test_performed_intervals_are_checked_without_scene_time_binding(self):
        rows = self.read_rows('languages/en/performed.csv')
        rows[0].update(start='02:00:00.000', end='02:00:01.000')
        self.write_rows('languages/en/performed.csv', rows)
        validate_scenes(self.root)
        rows[0]['end'] = rows[0]['start']
        self.write_rows('languages/en/performed.csv', rows)
        with self.assertRaisesRegex(ValueError, 'performed interval'):
            validate_scenes(self.root)

    def test_package_binding_and_empty_package(self):
        validate_scenes(self.root)
        path = self.root / 'specs' / 'scene' / 'spec.md'
        path.parent.mkdir(parents=True)
        path.write_text('## Scene binding\n\n```csv\nscene_id,revision,source_id\n'
                        'S002,1,video\n```\n', encoding='utf-8')
        scenes = self.read_rows('scenes/index.csv')
        scenes[1]['package'] = 'specs/scene/spec.md'
        self.write_rows('scenes/index.csv', scenes)
        validate_scenes(self.root)
        for text in [
            '# No binding\n',
            '## Scene binding\n```csv\nscene_id,revision,source_id\nS001,1,video\n```\n',
            '## Scene binding\n```csv\nscene_id,revision,source_id\nS002,2,video\n```\n',
            '## Scene binding\n```csv\nscene_id,revision,source_id\nS002,1,audio\n```\n',
        ]:
            path.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError):
                validate_scenes(self.root)
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'package|file'):
            validate_scenes(self.root)

    def test_package_paths_cannot_escape_root_or_use_non_spec_files(self):
        scenes = self.read_rows('scenes/index.csv')
        for value in ('../outside/spec.md', 'C:\\outside\\spec.md', 'https://example.org/spec.md'):
            with self.subTest(value=value):
                scenes[1]['package'] = value
                self.write_rows('scenes/index.csv', scenes)
                with self.assertRaisesRegex(ValueError, 'relative file'):
                    validate_scenes(self.root)
        path = self.root / 'notes.md'
        path.write_text('# Not a spec', encoding='utf-8')
        scenes[1]['package'] = 'notes.md'
        self.write_rows('scenes/index.csv', scenes)
        with self.assertRaisesRegex(ValueError, 'spec.md'):
            validate_scenes(self.root)

    def test_supplied_package_examples_bind_to_the_two_current_scenes(self):
        scenes = self.read_rows('scenes/index.csv')
        for row, name in zip(scenes, ('ordinary', 'complex')):
            source = ROOT / 'tests' / 'fixtures' / 'scenes' / 'packages' / name / 'spec.md'
            target = self.root / 'specs' / name / 'spec.md'
            target.parent.mkdir(parents=True)
            shutil.copy2(source, target)
            row['package'] = f'specs/{name}/spec.md'
        self.write_rows('scenes/index.csv', scenes)
        validate_scenes(self.root)

    def test_general_validator_accepts_unknown_scene_but_rejects_unknown_pilot(self):
        # Add the existing general validator's non-scene inputs, all synthetic.
        helper = GeneralValidatorIsolationTests()
        helper.root = self.root
        helper.make_root()
        helper.make_csv(
            'characters/index.csv',
            ['id', 'in_script', 'in_film', 'in_credits', 'credit_id', 'credit_name', 'script_name'],
            [['pronya', 'no', 'yes', 'no', '', '', ''],
             ['khymka', 'no', 'yes', 'no', '', '', '']],
        )
        self.line(speaker='unknown', note='Непевний закадровий мовець.')
        with contextlib.redirect_stdout(io.StringIO()):
            validate_repository(root=self.root)
        self.line(speaker='missing')
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, 'speaker'):
            validate_repository(root=self.root)
        self.line(speaker='pronya')
        rows = self.read_rows('pilots/P001/dialogue.uk.csv')
        rows[0]['speaker'] = 'unknown'
        rows[0]['note'] = 'Пілот зберігає попередні правила.'
        self.write_rows('pilots/P001/dialogue.uk.csv', rows)
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, 'Unknown speaker'):
            validate_repository(root=self.root)


if __name__ == '__main__':
    unittest.main()
