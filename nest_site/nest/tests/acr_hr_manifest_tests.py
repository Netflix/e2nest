import csv
import tempfile

from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from nest.acr_hr_manifest import build_config, local_media_server_address
from nest.subjective_study_aom import (
    _migrate_study_database,
    create_parser,
    discover_media_layout,
    find_nest_repository,
    local_study_urls,
)


class AcrHrManifestTests(SimpleTestCase):

    def test_public_command_name(self):
        self.assertEqual(create_parser().prog, 'subjective_study_aom')

    def test_run_command_exposes_experiment_and_media_root(self):
        args = create_parser().parse_args([
            'run', '--experiment', 'ai-extension-study',
            '--media-root', '/media', '--study-port', '8001'])
        self.assertEqual(args.command, 'run')
        self.assertEqual(args.experiment, 'ai-extension-study')
        self.assertEqual(args.media_root, '/media')
        self.assertEqual(args.study_port, 8001)

    def test_builds_study_urls_from_configurable_port(self):
        self.assertEqual(
            local_study_urls(8001),
            ('http://127.0.0.1:8001/login/',
             'http://127.0.0.1:8001/logout/?next=/login/'))
        with self.assertRaisesRegex(ValueError, 'between 1 and 65535'):
            local_study_urls(0)

    def test_finds_source_repository_for_experiment_creation(self):
        repository = find_nest_repository(Path(__file__).parent)
        self.assertTrue((repository / 'nest_site' / 'manage.py').is_file())

    def test_fresh_study_syncs_apps_without_migrations(self):
        site_root = self.root / 'repository' / 'nest_site'
        site_root.mkdir(parents=True)
        (site_root / 'manage.py').touch()
        environment = {'DJANGO_SETTINGS_MODULE': 'nest_site.settings'}

        with patch(
                'nest.subjective_study_aom.subprocess.run') as run_command:
            _migrate_study_database(site_root, environment)

        command = run_command.call_args.args[0]
        self.assertEqual(command[-3:], ['migrate', '--noinput',
                                        '--run-syncdb'])
        self.assertEqual(run_command.call_args.kwargs['cwd'], site_root)
        self.assertEqual(run_command.call_args.kwargs['env'], environment)
        self.assertTrue(run_command.call_args.kwargs['check'])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        for filename in ['practice.mp4', 'bridge.mp4', 'test.mp4']:
            (self.root / filename).write_bytes(filename.encode('ascii'))

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_manifest(self, rows, fieldnames=None):
        manifest = self.root / 'manifest.csv'
        with manifest.open('w', newline='', encoding='utf-8') as output:
            writer = csv.DictWriter(
                output,
                fieldnames=fieldnames or [
                    'role', 'path', 'source_id', 'condition_id', 'label',
                    'recommended_rating'])
            writer.writeheader()
            writer.writerows(rows)
        return manifest

    def test_discovers_calibration_bridge_and_actual_directories(self):
        paths = [
            'calibration/2-poor/campfire.mp4',
            'calibration/4-good/knitting.mp4',
            'bridge/face/hidden-reference.mp4',
            'actual/face/anchor-op1.mp4',
            'actual/face/ai-extension-op1.mp4',
        ]
        for relative_path in paths:
            media_path = self.root / relative_path
            media_path.parent.mkdir(parents=True, exist_ok=True)
            media_path.write_bytes(relative_path.encode('ascii'))

        rows = discover_media_layout(self.root)

        self.assertEqual(len(rows), 5)
        self.assertEqual(
            [row['recommended_rating'] for row in rows[:2]], ['2', '4'])
        self.assertEqual(
            {(row['role'], row['source_id'], row['condition_id'])
             for row in rows[2:]},
            {
                ('bridge', 'face', 'hidden-reference'),
                ('test', 'face', 'anchor-op1'),
                ('test', 'face', 'ai-extension-op1'),
            })

    def test_directory_layout_requires_all_three_sets(self):
        (self.root / 'calibration').mkdir()
        (self.root / 'bridge').mkdir()
        with self.assertRaisesRegex(ValueError, 'actual directory'):
            discover_media_layout(self.root)

    def test_builds_config_from_three_roles(self):
        manifest = self._write_manifest([
            {
                'role': 'familiarization', 'path': 'practice.mp4',
                'source_id': 'practice', 'condition_id': '',
                'label': 'Practice clip', 'recommended_rating': '4',
            },
            {
                'role': 'bridge', 'path': 'bridge.mp4',
                'source_id': 'source-a', 'condition_id': 'hidden-reference',
                'label': '', 'recommended_rating': '',
            },
            {
                'role': 'test', 'path': 'test.mp4',
                'source_id': 'source-a', 'condition_id': 'candidate-op1',
                'label': '', 'recommended_rating': '',
            },
        ])

        config = build_config(
            manifest, self.root, 'http://localhost:8093',
            'experiment-a', 'site-a')

        stimuli = config['stimulus_config']['stimuli']
        self.assertEqual(len(stimuli), 2)
        self.assertEqual(
            [stimulus['stimulus_role'] for stimulus in stimuli],
            ['bridge', 'test'])
        self.assertEqual(stimuli[0]['source_id'], 'source-a')
        self.assertEqual(len(stimuli[0]['sha256']), 64)
        self.assertEqual(
            stimuli[0]['path'], 'http://localhost:8093/bridge.mp4')
        self.assertEqual(
            config['experiment_config']['rounds_per_session'], 2)
        self.assertEqual(len(config['experiment_config']['additions']), 2)
        self.assertIn(
            'Practice clip',
            config['experiment_config']['additions'][1]['context']['title'])
        practice_context = \
            config['experiment_config']['additions'][1]['context']
        self.assertIn('familiarization-video-1',
                      practice_context['extrabody_html'])
        self.assertIn('position: fixed',
                      practice_context['extrastyle_html'])
        self.assertIn('Recommended rating: 4 &ndash; Good',
                      practice_context['text_html'])
        self.assertEqual(
            practice_context['text_html'].count('type="radio"'), 5)
        self.assertNotIn('Compare with recommended rating',
                         practice_context['text_html'])
        self.assertIn('recommendation.style.display = "block"',
                      practice_context['script_html'])
        self.assertIn('finishPlayback(true)',
                      practice_context['script_html'])

    def test_requires_condition_for_scored_media(self):
        manifest = self._write_manifest([{
            'role': 'test', 'path': 'test.mp4', 'source_id': 'source-a',
            'condition_id': '', 'label': '', 'recommended_rating': '',
        }])

        with self.assertRaisesRegex(ValueError, 'condition_id is required'):
            build_config(
                manifest, self.root, 'http://localhost:8093',
                'experiment-a', 'site-a')

    def test_requires_calibration_rating_for_familiarization(self):
        manifest = self._write_manifest([{
            'role': 'familiarization', 'path': 'practice.mp4',
            'source_id': 'practice', 'condition_id': '', 'label': '',
            'recommended_rating': '',
        }, {
            'role': 'test', 'path': 'test.mp4', 'source_id': 'source-a',
            'condition_id': 'candidate', 'label': '',
            'recommended_rating': '',
        }])

        with self.assertRaisesRegex(ValueError, 'recommended_rating'):
            build_config(
                manifest, self.root, 'http://localhost:8093',
                'experiment-a', 'site-a')

    def test_rejects_path_outside_media_root(self):
        manifest = self._write_manifest([{
            'role': 'test', 'path': '../outside.mp4',
            'source_id': 'source-a', 'condition_id': 'candidate',
            'label': '', 'recommended_rating': '',
        }])

        with self.assertRaisesRegex(ValueError, 'path leaves media root'):
            build_config(
                manifest, self.root, 'http://localhost:8093',
                'experiment-a', 'site-a')

    def test_allows_explicit_media_symlink(self):
        with tempfile.TemporaryDirectory() as outside_directory:
            outside_media = Path(outside_directory) / 'outside.mp4'
            outside_media.write_bytes(b'video')
            (self.root / 'linked.mp4').symlink_to(outside_media)
            manifest = self._write_manifest([{
                'role': 'test', 'path': 'linked.mp4',
                'source_id': 'source-a', 'condition_id': 'candidate',
                'label': '', 'recommended_rating': '',
            }])

            config = build_config(
                manifest, self.root, 'http://localhost:8093',
                'experiment-a', 'site-a')

        self.assertEqual(
            config['stimulus_config']['stimuli'][0]['path'],
            'http://localhost:8093/linked.mp4')

    def test_local_media_server_is_loopback_only(self):
        self.assertEqual(
            local_media_server_address('http://localhost:8093'),
            ('127.0.0.1', 8093))
        self.assertEqual(
            local_media_server_address('http://127.0.0.1:9000'),
            ('127.0.0.1', 9000))
        with self.assertRaisesRegex(ValueError, 'only supports localhost'):
            local_media_server_address('http://0.0.0.0:8093')
        with self.assertRaisesRegex(ValueError, 'without a path'):
            local_media_server_address('http://localhost:8093/media')
