import json

from django.test import TestCase
from nest.config import ExperimentConfig, NestConfig, StimulusConfig


class TestStimulusConfig(TestCase):

    def test_stim_config(self):
        scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4",  # noqa E501
                    "stimulus_id": 1,
                    "type": "video/mp4",
                    "content_id": 0,
                }
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
                {
                    "stimulus_ids": [
                        1
                    ],
                    "stimulusvotegroup_id": 1
                }
            ],
            'stimulusgroups': [
                {'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0], 'text_color': '#FF0000'},
                {'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [1]},
                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0], 'video_display_percentage': 30,
                 'pre_message': 'hello', 'start_end_seconds': (2, 3.6), 'super_stimulusgroup_id': 1, 'text_color': '#FF0000', 'overlay_on_video_js': """alert("hello")"""},
                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 5, 'stimulusvotegroup_ids': [0]},
            ],
        })
        self.assertEqual(len(scfg.stimulusgroups), 5)
        self.assertEqual(scfg.stimulusgroup_ids, [0, 4, 2, 3, 5])
        self.assertEqual(scfg.get_video_display_percentage(3), 30)
        self.assertEqual(scfg.get_pre_message(3), 'hello')
        self.assertEqual(scfg.get_start_end_seconds(3), (2, 3.6))
        self.assertEqual(scfg.get_text_color(3), '#FF0000')
        self.assertEqual(scfg.get_overlay_on_video_js(3), """alert("hello")""")
        self.assertEqual(scfg.get_super_stimulusgroup_id(3), 1)
        self.assertEqual(scfg.get_video_display_percentage(4), 100)
        self.assertEqual(scfg.get_video_display_percentage(5), 100)
        self.assertEqual(scfg.get_video_display_percentage(6), None)
        self.assertEqual(scfg.get_pre_message(6), None)
        self.assertEqual(scfg.get_start_end_seconds(6), None)
        self.assertEqual(scfg.get_text_color(6), None)
        self.assertEqual(scfg.get_overlay_on_video_js(6), None)
        self.assertEqual(scfg.get_super_stimulusgroup_id(6), None)
        with self.assertRaises(AssertionError) as e:
            _ = scfg.super_stimulusgroup_ids
        self.assertTrue('super_stimulusgroup_id must be all-present or all-absent' in str(e.exception))

    def test_stim_config_with_public_path(self):
        scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "http://media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
                {
                    "path": "https://media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4",  # noqa E501
                    "stimulus_id": 1,
                    "type": "video/mp4",
                    "content_id": 0,
                }
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
                {
                    "stimulus_ids": [
                        1
                    ],
                    "stimulusvotegroup_id": 1
                }
            ],
            'stimulusgroups': [
                {'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0], 'super_stimulusgroup_id': 0},
                {'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [1], 'super_stimulusgroup_id': 0},
                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0], 'super_stimulusgroup_id': 0},
                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0], 'video_display_percentage': 30, 'super_stimulusgroup_id': 1},
                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 5, 'stimulusvotegroup_ids': [0], 'super_stimulusgroup_id': 1},
            ],
        })
        self.assertEqual(len(scfg.stimulusgroups), 5)
        self.assertEqual(scfg.get_video_display_percentage(3), 30)
        self.assertEqual(scfg.get_video_display_percentage(4), 100)
        self.assertEqual(scfg.get_video_display_percentage(5), 100)
        self.assertEqual(scfg.get_video_display_percentage(6), None)
        self.assertEqual(scfg.super_stimulusgroup_ids, [0, 0, 0, 1, 1])


class TestExperimentConfig(TestCase):

    def setUp(self) -> None:
        self.scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4",  # noqa E501
                    "stimulus_id": 1,
                    "type": "video/mp4",
                    "content_id": 0,
                }
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
                {
                    "stimulus_ids": [
                        1
                    ],
                    "stimulusvotegroup_id": 1
                }
            ],
            'stimulusgroups': [
                {'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [1]},
                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0]},
                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 5, 'stimulusvotegroup_ids': [0]},
            ],
        })

    def test_exp_config_0(self):
        ecfg = ExperimentConfig(
            stimulus_config=self.scfg,
            config={
                'title': 'test',
                'description': 'test',
                'methodology': 'acr',
                'vote_scale': 'FIVE_POINT',
                'rounds_per_session': 10,
            }
        )
        self.assertEqual(ecfg.rounds_per_session, 10)
        self.assertEqual(ecfg.random_seed, None)
        self.assertEqual(len(ecfg.prioritized), 0)
        self.assertEqual(ecfg.vote_scale, 'FIVE_POINT')

    def test_exp_config_known_vote_scale(self):
        with self.assertRaises(AssertionError):
            ExperimentConfig(stimulus_config=self.scfg,
                             config={'vote_scale': 'FIVE_POINT_XXX'})

    def test_exp_config(self):
        ecfg = ExperimentConfig(
            stimulus_config=self.scfg,
            config={
                'title': 'test',
                'description': 'test',
                'rounds_per_session': 8,
                'random_seed': 3,
                'prioritized': [
                    {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
                    {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
                    {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 4},
                    {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 4},
                    {'session_idx': 2, 'round_id': None, 'stimulusgroup_id': 2},
                ],
                'blocklist_stimulusgroup_ids': [0],
                'training_round_ids': [0],
                'vote_scale': '0_TO_100',
                'methodology': 'acr5c',
            })
        self.assertEqual(ecfg.rounds_per_session, 8)
        self.assertEqual(ecfg.random_seed, 3)
        self.assertEqual(len(ecfg.prioritized), 5)
        self.assertEqual(len(ecfg.blocklist_stimulusgroup_ids), 1)
        self.assertEqual(len(ecfg.training_round_ids), 1)
        self.assertEqual(ecfg.vote_scale, '0_TO_100')

    def test_exp_order_sgid_outofbound(self):
        scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4",  # noqa E501
                    "stimulus_id": 1,
                    "type": "video/mp4",
                    "content_id": 0,
                }
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
                {
                    "stimulus_ids": [
                        1
                    ],
                    "stimulusvotegroup_id": 1
                }
            ],
            'stimulusgroups': [
                {'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 1, 'stimulusvotegroup_ids': [1]},
                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0]},
                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [0]},
            ],
        })
        with self.assertRaises(AssertionError):
            ExperimentConfig(
                stimulus_config=scfg,
                config={
                    'title': 'test',
                    'description': 'test',
                    'rounds_per_session': 8,
                    'random_seed': 3,
                    'prioritized': [
                        {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
                        {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 5},
                        {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 5},
                        {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 5},
                    ]
                })

    def test_exp_additions(self):
        config_filepath = NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json')
        with open(config_filepath, 'rt') as fp:
            config = json.load(fp)
        scfg = StimulusConfig(config['stimulus_config'])
        ExperimentConfig(stimulus_config=scfg,
                         config=config['experiment_config'])

    def test_exp_additions_dcr(self):
        config_filepath = NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr.json')
        with open(config_filepath, 'rt') as fp:
            config = json.load(fp)
        scfg = StimulusConfig(config['stimulus_config'])
        ExperimentConfig(stimulus_config=scfg,
                         config=config['experiment_config'])

    def test_exp_additions_mlds(self):
        config_filepath = NestConfig.tests_resource_path('cvxhull_subjexp_toy_mlds.json')
        with open(config_filepath, 'rt') as fp:
            config = json.load(fp)
        # currently does not support svg involving 4 stimuli (e.g. MLDS)
        with self.assertRaises(AssertionError):
            StimulusConfig(config['stimulus_config'])

    def test_validate_html(self):
        config_filepath = NestConfig.tests_resource_path('cvxhull_subjexp_toy_w_invalid_done_context.json')
        with open(config_filepath, 'rt') as fp:
            config = json.load(fp)
        scfg = StimulusConfig(config['stimulus_config'])
        with self.assertRaises(AssertionError):
            ExperimentConfig(stimulus_config=scfg,
                             config=config['experiment_config'])
