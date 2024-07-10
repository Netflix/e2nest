import glob
import json
import os
import random
import shutil

from django.contrib.auth.models import User
from django.test import TestCase
from nest.config import ExperimentConfig, NestConfig, StimulusConfig
from nest.control import ExperimentController, SessionStatus
from nest.helpers import import_python_file
from nest.io import ESUtilities, ExperimentUtils, \
    export_sureal_dataset, import_sureal_dataset, \
    SurealPairedCompDatasetReaderPlus, SurealRawDatasetReaderPlus, UserUtils
from nest.io_utils import ExperimentConfigFileUtils
from nest.models import Condition, Content, Experiment, Experimenter, \
    ExperimentRegister, FivePointVote, Round, Session, Stimulus, \
    StimulusGroup, StimulusVoteGroup, Subject, TafcVote, Vote, VoteRegister, \
    Zero2HundredVote
from nest.sites import NestSite
from nest_site.settings import map_media_local_to_url


class TestDatasetReader(TestCase):

    def test_populate_nest_nflx_public(self):
        dataset_path = NestConfig.tests_resource_path(
            'NFLX_dataset_public_raw_last4outliers_tiny.py')
        scale = 'FIVE_POINT'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)

        self.assertEqual(Experiment.objects.count(), 1)
        self.assertEqual(Content.objects.count(), 3)
        self.assertEqual(Subject.objects.count(), 30)
        self.assertEqual(Session.objects.count(), 30)
        self.assertEqual(Stimulus.objects.count(), 28)
        self.assertEqual(Round.objects.count(), 840)
        self.assertEqual(Vote.objects.count(), 840)
        self.assertEqual(FivePointVote.objects.count(), 840)
        self.assertEqual(VoteRegister.objects.count(), 28)
        svg = StimulusVoteGroup.objects.get(id=1)
        self.assertEqual(VoteRegister.objects.get(stimulusvotegroup=svg).stimulus_order, 1)
        self.assertEqual(StimulusGroup.objects.get(id=1).round_set.count(), 30)
        self.assertEqual(StimulusGroup.objects.get(id=1).stimulusgroup_id, 9)

        reader = SurealRawDatasetReaderPlus(dataset)
        self.assertEqual(len(reader._retrieve_or_create_stimuli()), 28)
        sd = reader.get_stimulus_dict()
        self.assertEqual(len(sd['stimulusgroups']), 28)
        self.assertEqual(sd['stimulusgroups'][0]['stimulusgroup_id'], 9)
        self.assertEqual(sd['stimulusgroups'][10]['stimulusgroup_id'], 0)
        self.assertEqual(sd['stimulusgroups'][20]['stimulusgroup_id'], 27)

        self.assertEqual(Round.objects.get(id=1).round_id, 0)
        self.assertEqual(Round.objects.get(id=150).round_id, 4)
        self.assertEqual(Round.objects.get(id=250).round_id, 8)

    def test_populate_nest_os_style_dict(self):
        dataset_path = NestConfig.tests_resource_path(
            'vmafplusstudy_laptop_raw_tiny.py')
        scale = '0_TO_100'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)

        self.assertEqual(Experiment.objects.count(), 1)
        self.assertEqual(Content.objects.count(), 3)
        self.assertEqual(Subject.objects.count(), 41)
        self.assertEqual(Session.objects.count(), 41)
        self.assertEqual(Stimulus.objects.count(), 32)
        self.assertEqual(Round.objects.count(), 1312)
        self.assertEqual(Vote.objects.count(), 653)
        self.assertEqual(Zero2HundredVote.objects.count(), 653)
        self.assertEqual(VoteRegister.objects.count(), 32)
        self.assertEqual(StimulusGroup.objects.get(id=1).round_set.count(), 41)
        self.assertEqual(StimulusGroup.objects.get(id=1).stimulusgroup_id, 1000)

        reader = SurealRawDatasetReaderPlus(dataset)
        self.assertEqual(len(reader._retrieve_or_create_stimuli()), 32)
        sd = reader.get_stimulus_dict()
        self.assertEqual(len(sd['stimulusgroups']), 32)
        self.assertEqual(sd['stimulusgroups'][0]['stimulusgroup_id'], 1000)
        self.assertEqual(sd['stimulusgroups'][10]['stimulusgroup_id'], 17)
        self.assertEqual(sd['stimulusgroups'][20]['stimulusgroup_id'], 34)

        self.assertEqual(Round.objects.get(id=1).round_id, 0)
        self.assertEqual(Round.objects.get(id=150).round_id, 3)
        self.assertEqual(Round.objects.get(id=250).round_id, 6)

    def test_populate_nest_mismatched_vote_class(self):
        dataset_path = NestConfig.tests_resource_path(
            'vmafplusstudy_laptop_raw_tiny.py')
        scale = 'FIVE_POINT'
        dataset = import_python_file(dataset_path)
        with self.assertRaises(AssertionError):
            import_sureal_dataset(dataset, scale)

    def test_populate_nest_pc(self):
        dataset_path = NestConfig.tests_resource_path(
            'lukas_pc_dataset_tiny.py')
        scale = '2AFC'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)

        self.assertEqual(Experiment.objects.count(), 1)
        self.assertEqual(Content.objects.count(), 2)
        self.assertEqual(Subject.objects.count(), 15)
        self.assertEqual(Session.objects.count(), 15)
        self.assertEqual(Stimulus.objects.count(), 16)
        self.assertEqual(Round.objects.count(), 840)
        self.assertEqual(Vote.objects.count(), 840)
        self.assertEqual(TafcVote.objects.count(), 840)
        self.assertEqual(VoteRegister.objects.count(), 206)
        svg = StimulusVoteGroup.objects.get(id=1)
        self.assertEqual(VoteRegister.objects.
                         filter(stimulusvotegroup=svg)[0].stimulus_order, 1)
        self.assertEqual(VoteRegister.objects.
                         filter(stimulusvotegroup=svg)[1].stimulus_order, 2)
        self.assertEqual(StimulusGroup.objects.get(id=1).round_set.count(), 2)
        self.assertEqual(StimulusGroup.objects.get(id=2).round_set.count(), 12)
        self.assertEqual(StimulusGroup.objects.get(id=3).round_set.count(), 8)
        self.assertEqual(StimulusGroup.objects.get(id=4).round_set.count(), 12)
        self.assertEqual(StimulusGroup.objects.get(id=5).round_set.count(), 13)
        self.assertEqual(StimulusGroup.objects.get(id=1).stimulusgroup_id, 0)
        self.assertEqual(StimulusGroup.objects.get(id=2).stimulusgroup_id, 1)
        self.assertEqual(StimulusGroup.objects.get(id=3).stimulusgroup_id, 2)
        self.assertEqual(StimulusGroup.objects.get(id=4).stimulusgroup_id, 3)
        self.assertEqual(StimulusGroup.objects.get(id=5).stimulusgroup_id, 4)

        reader = SurealPairedCompDatasetReaderPlus(dataset)
        self.assertEqual(len(reader._retrieve_or_create_stimuli()), 16)
        with self.assertRaises(NotImplementedError):
            reader.get_stimulusgroups()

    def test_populate_nest_linear_repeat(self):
        dataset_path = NestConfig.tests_resource_path(
            'NFLX_dataset_public_raw_last4outliers_tiny.py')
        scale = 'FIVE_POINT'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)
        with self.assertRaises(AssertionError):
            import_sureal_dataset(dataset, scale)

    def test_populate_nest_pc_repeat(self):
        dataset_path = NestConfig.tests_resource_path(
            'lukas_pc_dataset_tiny.py')
        scale = '2AFC'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)
        with self.assertRaises(AssertionError):
            import_sureal_dataset(dataset, scale)

    def test_export_dataset_single(self):
        dataset_path = NestConfig.tests_resource_path(
            'NFLX_dataset_public_raw_last4outliers_tiny.py')
        import_sureal_dataset(import_python_file(dataset_path), 'FIVE_POINT')
        dataset = export_sureal_dataset('NFLX_public')
        self.assertEqual(dataset.dataset_name, 'NFLX_public')
        self.assertEqual(len(dataset.ref_videos), 3)
        self.assertEqual(len(dataset.dis_videos), 28)
        self.assertEqual(len(dataset.dis_videos[0]['os']), 30)
        self.assertEqual(len(dataset.dis_videos[1]['os']), 30)
        self.assertEqual(len(dataset.dis_videos[2]['os']), 30)
        self.assertEqual(list(dataset.dis_videos[2]['os'].keys())[0], 'NFLX_public-#0')

    def test_export_dataset_single2(self):
        dataset_path = NestConfig.tests_resource_path(
            'vmafplusstudy_laptop_raw_tiny.py')
        import_sureal_dataset(import_python_file(dataset_path), '0_TO_100')
        dataset = export_sureal_dataset('VMAF_Plus_DB')
        self.assertEqual(dataset.dataset_name, 'VMAF_Plus_DB')
        self.assertEqual(len(dataset.ref_videos), 3)
        self.assertEqual(len(dataset.dis_videos), 32)
        self.assertEqual(len(dataset.dis_videos[0]['os']), 19)
        self.assertEqual(len(dataset.dis_videos[1]['os']), 19)
        self.assertEqual(len(dataset.dis_videos[2]['os']), 19)
        self.assertEqual(list(dataset.dis_videos[2]['os'].keys())[0], 'VMAF_Plus_DB-aschuler')

    def test_export_dataset_double(self):
        dataset_path = NestConfig.tests_resource_path(
            'lukas_pc_dataset_tiny.py')
        dataset = import_python_file(dataset_path)
        dataset.dataset_name = 'Lukas_SPIE14_tiny'
        import_sureal_dataset(dataset, '2AFC')
        dataset = export_sureal_dataset('Lukas_SPIE14_tiny')
        self.assertEqual(dataset.dataset_name, 'Lukas_SPIE14_tiny')
        self.assertEqual(len(dataset.ref_videos), 2)
        self.assertEqual(len(dataset.dis_videos), 16)
        self.assertEqual(len(dataset.dis_videos[0]['os']), 65)
        self.assertEqual(len(dataset.dis_videos[1]['os']), 86)
        self.assertEqual(len(dataset.dis_videos[2]['os']), 82)
        self.assertEqual(len(dataset.dis_videos[3]['os']), 61)
        self.assertEqual(len(dataset.dis_videos[4]['os']), 54)
        self.assertEqual(len(dataset.dis_videos[14]['os']), 22)
        self.assertEqual(len(dataset.dis_videos[15]['os']), 8)
        self.assertEqual(list(dataset.dis_videos[2]['os'].keys())[0], ('Lukas_SPIE14_tiny-David R.', 4))

    def test_export_dataset_double_ignore_against(self):
        # meant for DCR but could only find dataset of PC to create the test
        dataset_path = NestConfig.tests_resource_path(
            'lukas_pc_dataset_tiny.py')
        dataset = import_python_file(dataset_path)
        dataset.dataset_name = 'Lukas_SPIE14_tiny'
        import_sureal_dataset(dataset, '2AFC')
        dataset = export_sureal_dataset('Lukas_SPIE14_tiny', ignore_against=True)
        self.assertEqual(dataset.dataset_name, 'Lukas_SPIE14_tiny')
        self.assertEqual(len(dataset.ref_videos), 2)
        self.assertEqual(len(dataset.dis_videos), 16)
        self.assertEqual(len(dataset.dis_videos[0]['os']), 14)
        self.assertEqual(len(dataset.dis_videos[1]['os']), 15)
        self.assertEqual(len(dataset.dis_videos[2]['os']), 15)
        self.assertEqual(len(dataset.dis_videos[3]['os']), 15)
        self.assertEqual(len(dataset.dis_videos[4]['os']), 15)
        self.assertEqual(len(dataset.dis_videos[5]['os']), 15)
        self.assertEqual(len(dataset.dis_videos[15]['os']), 5)
        self.assertEqual(dataset.dis_videos[0]['os']['Lukas_SPIE14_tiny-David R.'], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual(dataset.dis_videos[0]['os']['Lukas_SPIE14_tiny-dingo'], [1.0, 1.0, 1.0, 1.0])


class TestExperimentController(TestCase):

    @staticmethod
    def create_config_from_sureal_dataset(dataset, seed):
        try:
            dataset_reader = SurealPairedCompDatasetReaderPlus(dataset)
        except AssertionError:
            dataset_reader = SurealRawDatasetReaderPlus(dataset)
        sd = dataset_reader.get_stimulus_dict()
        return dataset_reader.make_experiment_config_dict(
            sd['contents'],
            sd['stimuli'],
            sd['stimulusvotegroups'],
            sd['stimulusgroups'],
            seed)

    def test_populate_nest_nflx_public(self):
        dataset_path = NestConfig.tests_resource_path(
            'NFLX_dataset_public_raw_last4outliers_tiny.py')
        scale = 'FIVE_POINT'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)

        config = self.create_config_from_sureal_dataset(dataset, seed=1)
        scfg = StimulusConfig(config['stimulus_config'], skip_path_check=True)
        ecfg = ExperimentConfig(stimulus_config=scfg,
                                config=config['experiment_config'])
        exp = Experiment.objects.get(title=dataset.dataset_name)
        ec = ExperimentController(experiment=exp, experiment_config=ecfg)

        sess = exp.session_set.first()
        self.assertEqual(ec.get_session_status(sess), SessionStatus.FINISHED)

        sinfo: dict = ec.get_session_info(sess)
        self.assertEqual(sinfo['subject'], 'NFLX_public-#0')
        self.assertEqual(sinfo['session_id'], 1)
        self.assertEqual(sinfo['rounds'][-1]['round_id'], 27)
        self.assertEqual(sinfo['rounds'][-1]['stimulusgroup_id'], 2)
        self.assertEqual(sinfo['rounds'][-1]['stimulusvotegroups'][0]['stimulusvotegroup_id'], 2)
        self.assertEqual(sinfo['rounds'][-1]['stimulusvotegroups'][0]['vote'], 5.0)

        einfo: dict = ec.get_experiment_info()
        self.assertEqual(einfo['title'], 'NFLX_public')
        self.assertEqual(einfo['description'], None)
        self.assertEqual(len(einfo['sessions']), 30)
        self.assertEqual(len(einfo['sessions'][0]['rounds']), 28)
        self.assertEqual(len(einfo['stimuli_info']['contents']), 3)
        self.assertEqual(len(einfo['stimuli_info']['stimuli']), 28)
        self.assertEqual(len(einfo['stimuli_info']['stimulusvotegroups']), 28)
        self.assertEqual(len(einfo['stimuli_info']['stimulusgroups']), 28)

        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (840, 8))
        self.assertEqual(df.iloc[0].subject, 'NFLX_public-#0')
        self.assertEqual(df.iloc[0].session_id, 1)
        self.assertEqual(df.iloc[0].round_id, 0)
        self.assertEqual(df.iloc[0].sg_id, 9)
        self.assertEqual(df.iloc[0].svg_id, 9)
        self.assertEqual(df.iloc[0].vote, 1.0)
        self.assertEqual(df.iloc[0].sid, 9)
        self.assertEqual(df.iloc[0].path, '[path to dataset videos]/dis/BigBuckBunny_20_288_375.yuv')

        sess.round_set.first().vote_set.first().delete()
        self.assertEqual(ec.get_session_status(sess), SessionStatus.PARTIALLY_FINISHED)

        sess2 = ExperimentUtils.add_session_to_experiment(
            exp.title, 'zli', config=config, skip_path_check=True)
        self.assertEqual(sess2.round_set.count(), 28)
        self.assertEqual(sess2.subject.user.username, 'zli')

        ExperimentUtils.delete_session_by_id(
            sess2.id, exp.title, config=config, skip_path_check=True)
        with self.assertRaises(Session.DoesNotExist):
            Session.objects.get(id=sess2.id)

        subj = Subject()
        subj.save()
        ec.add_session(subj)
        sess2 = exp.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)

        ExperimentUtils.update_subject_for_session(
            exp.title, exp.session_set.all()[3].id,
            'zli', config=config, skip_path_check=True)
        sess_3rd = exp.session_set.all()[3]
        self.assertEqual(sess_3rd.subject.user.username, 'zli')
        self.assertEqual(ec.get_session_status(sess_3rd), SessionStatus.FINISHED)

        ExperimentUtils.reset_unfinished_session(exp.title, sess.id,
                                                 config=config,
                                                 skip_path_check=True)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.INITIALIZED)

        steps = ec.get_session_steps(sess)
        self.assertEqual(len(steps), 29)
        self.assertEqual(steps[1], {'context': {'stimulusgroup_id': 9}, 'position': {'round_id': 0}})
        self.assertEqual(steps[-1], {'context': {'stimulusgroup_id': 2}, 'position': {'round_id': 27}})

        # test delete session
        self.assertEqual(Session.objects.count(), 31)
        self.assertEqual(Round.objects.count(), 868)
        self.assertEqual(Vote.objects.count(), 812)
        for sess in exp.session_set.all():
            ec.delete_session(sess.id)
        self.assertEqual(Session.objects.count(), 0)
        self.assertEqual(Round.objects.count(), 0)
        self.assertEqual(Vote.objects.count(), 0)

    def test_populate_nest_os_style_dict(self):
        dataset_path = NestConfig.tests_resource_path(
            'vmafplusstudy_laptop_raw_tiny.py')
        scale = '0_TO_100'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale)

        config = self.create_config_from_sureal_dataset(dataset, seed=1)
        scfg = StimulusConfig(config['stimulus_config'], skip_path_check=True)
        ecfg = ExperimentConfig(stimulus_config=scfg,
                                config=config['experiment_config'])
        exp = Experiment.objects.get(title=dataset.dataset_name)
        ec = ExperimentController(experiment=exp, experiment_config=ecfg)

        sess = exp.session_set.first()
        # the session will appear as unfinished because in the dataset
        # imported, there are missing entries (not all subjects voted on all
        # stimuli), and it was assumed that a subject should have voted
        # for all stimuli in one session (which is not a practical assumption
        # in practice)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.PARTIALLY_FINISHED)

        sinfo: dict = ec.get_session_info(sess)
        self.assertEqual(sinfo['subject'], 'VMAF_Plus_DB-andrewp')
        self.assertEqual(sinfo['session_id'], 1)
        self.assertEqual(sinfo['rounds'][-1]['round_id'], 31)
        self.assertEqual(sinfo['rounds'][-1]['stimulusgroup_id'], 52)
        self.assertEqual(sinfo['rounds'][-1]['stimulusvotegroups'][0]['stimulusvotegroup_id'], 52)
        self.assertEqual(sinfo['rounds'][-2]['round_id'], 30)
        self.assertEqual(sinfo['rounds'][-2]['stimulusgroup_id'], 51)
        self.assertEqual(sinfo['rounds'][-2]['stimulusvotegroups'][0]['stimulusvotegroup_id'], 51)
        self.assertEqual(sinfo['rounds'][-2]['stimulusvotegroups'][0]['vote'], 47.0)

        einfo: dict = ec.get_experiment_info()
        self.assertEqual(einfo['title'], 'VMAF_Plus_DB')
        self.assertEqual(einfo['description'], None)
        self.assertEqual(len(einfo['sessions']), 41)
        self.assertEqual(len(einfo['sessions'][0]['rounds']), 32)
        self.assertEqual(len(einfo['stimuli_info']['contents']), 3)
        self.assertEqual(len(einfo['stimuli_info']['stimuli']), 32)
        self.assertEqual(len(einfo['stimuli_info']['stimulusvotegroups']), 32)
        self.assertEqual(len(einfo['stimuli_info']['stimulusgroups']), 32)

        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (1312, 8))

        sess2 = ExperimentUtils.add_session_to_experiment(
            exp.title, 'zli', config=config, skip_path_check=True)
        self.assertEqual(sess2.round_set.count(), 32)
        self.assertEqual(sess2.subject.user.username, 'zli')

        subj = Subject()
        subj.save()
        ec.add_session(subj)
        sess2 = exp.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)

        ExperimentUtils.update_subject_for_session(
            exp.title, exp.session_set.all()[3].id, 'zli',
            config=config, skip_path_check=True)
        sess_3rd = exp.session_set.all()[3]
        self.assertEqual(sess_3rd.subject.user.username, 'zli')
        self.assertEqual(ec.get_session_status(sess_3rd), SessionStatus.PARTIALLY_FINISHED)

        ExperimentUtils.reset_unfinished_session(exp.title, sess_3rd.id,
                                                 config=config,
                                                 skip_path_check=True)
        self.assertEqual(ec.get_session_status(sess_3rd), SessionStatus.INITIALIZED)

        steps = ec.get_session_steps(sess)
        self.assertEqual(len(steps), 33)
        self.assertEqual(steps[1], {'context': {'stimulusgroup_id': 1000}, 'position': {'round_id': 0}})
        self.assertEqual(steps[-1], {'context': {'stimulusgroup_id': 52}, 'position': {'round_id': 31}})


class TestWriteExperimentConfigFile(TestCase):

    def setUp(self) -> None:
        self.config_filedir = NestConfig.tests_workdir_path(
            'test_write_experiment_config_file')

    def tearDown(self):
        shutil.rmtree(self.config_filedir)

    def test_populate_nest_nflx_public(self):
        dataset_path = NestConfig.tests_resource_path(
            'NFLX_dataset_public_raw_last4outliers_tiny.py')
        scale = 'FIVE_POINT'
        dataset = import_python_file(dataset_path)
        import_sureal_dataset(dataset, scale,
                              write_config=True,
                              config_filedir=self.config_filedir)

        # verify
        with open(os.path.join(self.config_filedir, "NFLX_public.json")) as fp:
            cfg = json.load(fp)
            self.assertEqual(len(cfg['stimulus_config']['stimulusgroups']), 28)


class TestCreateExperiment(TestCase):
    def setUp(self) -> None:
        self.config_filedir = os.path.dirname(NestSite.get_experiment_config_filepath("xxx", is_test=True))

    def tearDown(self):
        shutil.rmtree(self.config_filedir)

    def test_create_experiment(self):
        ec: ExperimentController = ExperimentUtils.create_experiment(
            experiment_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'),
            experimenter_username='lukas@catflix.com',
            is_test=True,
            random_seed=1,
            experiment_title='io_tests.TestCreateExperiment.test_create_experiment')
        self.assertEqual(ec.experiment.title, 'io_tests.TestCreateExperiment.test_create_experiment')
        self.assertEqual(ec.experiment_config.random_seed, 1)
        self.assertEqual(ec.experiment.experimenters.first(),
                         Experimenter.find_by_username('lukas@catflix.com'))
        config_filepath = NestSite.get_experiment_config_filepath(ec.experiment_config.title, is_test=True)
        self.assertTrue(os.path.exists(config_filepath))
        with open(config_filepath, 'rt') as fp:
            config = json.load(fp)
        self.assertEqual(config['experiment_config']['random_seed'], 1)
        self.assertEqual(config['experiment_config']['title'],
                         'io_tests.TestCreateExperiment.test_create_experiment')

        subj = Subject.objects.create(name='Netflix_Noise_1')
        ec.add_session(subj)
        sess = ec.experiment.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.INITIALIZED)

        subj2 = Subject.objects.create(name='Netflix_Noise_2')
        ec.add_session(subj2)
        sess2 = ec.experiment.session_set.get(subject=subj2)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': 'Netflix_Noise_1', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1}]},
                {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0}]}
            ]})

        sinfo2 = ec.get_session_info(sess2)
        self.assertEqual(
            sinfo2,
            {'session_id': 2, 'subject': 'Netflix_Noise_2', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0}]},
                {'round_id': 1, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1}]}
            ]})

        df = ESUtilities.export_playlist_ES_noise_study_style(ec)
        self.assertEqual(df.columns.to_list(),
                         ['participant_id', 'content', 'noise_level', 'interval', 'trial', 'Filename'])
        self.assertEqual(df.iloc[0].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'A', 0, '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4'])  # noqa E501
        self.assertEqual(df.iloc[1].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'A', 1, '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4'])  # noqa E501
        self.assertEqual(df.iloc[2].to_list(),
                         ['Netflix_Noise_2', 0, -1, 'A', 0, '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4'])  # noqa E501
        self.assertEqual(df.iloc[3].to_list(),
                         ['Netflix_Noise_2', 0, -1, 'A', 1, '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4'])  # noqa E501

        self.assertEqual(Experiment.objects.count(), 1)
        self.assertEqual(Session.objects.count(), 2)
        self.assertEqual(Round.objects.count(), 4)
        self.assertEqual(Vote.objects.count(), 0)
        self.assertEqual(ExperimentRegister.objects.count(), 1)
        self.assertEqual(StimulusGroup.objects.count(), 2)
        self.assertEqual(StimulusVoteGroup.objects.count(), 2)
        self.assertEqual(VoteRegister.objects.count(), 2)
        self.assertEqual(Stimulus.objects.count(), 2)
        self.assertEqual(Content.objects.count(), 1)
        self.assertEqual(Condition.objects.count(), 0)

        ExperimentUtils.delete_experiment_by_title(
            experiment_title='io_tests.TestCreateExperiment.test_create_experiment',
            is_test=True)

        self.assertEqual(Experiment.objects.count(), 0)
        self.assertEqual(Session.objects.count(), 0)
        self.assertEqual(Round.objects.count(), 0)
        self.assertEqual(Vote.objects.count(), 0)
        self.assertEqual(ExperimentRegister.objects.count(), 0)
        self.assertEqual(StimulusGroup.objects.count(), 0)
        self.assertEqual(StimulusVoteGroup.objects.count(), 0)
        self.assertEqual(VoteRegister.objects.count(), 0)
        self.assertEqual(Stimulus.objects.count(), 0)
        self.assertEqual(Content.objects.count(), 0)
        self.assertEqual(Condition.objects.count(), 0)

    def test_create_experiment_es_noise_study(self):
        ec: ExperimentController = ExperimentUtils.create_experiment(
            experiment_config_filepath=NestConfig.tests_resource_path('es_noise_study_test1a1b_dcr_with_training_and_reliability.json'),
            experimenter_username='lukas@catflix.com',
            is_test=True,
            random_seed=1,
            experiment_title='io_tests.TestCreateExperiment.test_create_experiment_es_noise_study')

        subj = Subject.objects.create(name='Netflix_Noise_1')
        ec.add_session(subj)
        sess = ec.experiment.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.INITIALIZED)

        subj2 = Subject.objects.create(name='Netflix_Noise_2')
        ec.add_session(subj2)
        sess2 = ec.experiment.session_set.get(subject=subj2)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)

        df = ESUtilities.export_playlist_ES_noise_study_style(ec)
        # df.to_csv('test.csv', index=False)
        self.assertEqual(df.columns.to_list(),
                         ['participant_id', 'content', 'noise_level', 'interval', 'trial', 'Filename'])
        self.assertEqual(df.iloc[0].to_list(),
                         ['Netflix_Noise_1', 1, -1, 'A', 0, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.08_psnr36.88_kbps115614.98_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[1].to_list(),
                         ['Netflix_Noise_1', 1, -1, 'B', 0, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.08_psnr36.88_kbps115614.98_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[2].to_list(),
                         ['Netflix_Noise_1', 1, 0, 'A', 1, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__ni_denoise_filter_before_scale__qp18_vmaf83.17_psnr34.15_kbps28163.51_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[3].to_list(),
                         ['Netflix_Noise_1', 1, -1, 'B', 1, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.08_psnr36.88_kbps115614.98_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[10].to_list(),
                         ['Netflix_Noise_1', 0, 5, 'A', 5, '/media/mp4/es_noise_study/test1a1b/false-as-water-filmgrain-subj-test-prep-101b-beamr5-20211020aopalach-__beamr5__3840_2160__ni_denoise_with_target_noise_rmse_5_filter_before_scale__qp18_vmaf68.47_psnr33.67_kbps90682.35_fps24.0.mp4'])  # noqa E501
        self.assertEqual(df.iloc[-1].to_list(),
                         ['Netflix_Noise_2', 2, -1, 'B', 5, '/media/mp4/es_noise_study/test1a1b/PeeWeeS2Store-underVMAF-A-filmgrain-subj-test-prep-26-beamr5-20211007-__beamr5__960_540__none__qp37_vmaf26.91_psnr27.9_kbps283.91_fps29.97002997002997'])  # noqa E501

    def test_export_playlist_ES_noise_study_style_shuffle_intervals(self):
        ec: ExperimentController = ExperimentUtils.create_experiment(
            experiment_config_filepath=NestConfig.tests_resource_path('es_noise_study_test1a1b_dcr_with_training_and_reliability.json'),
            experimenter_username='lukas@catflix.com',
            is_test=True,
            random_seed=1,
            experiment_title='io_tests.TestCreateExperiment.test_export_playlist_ES_noise_study_style_shuffle_intervals')

        subj = Subject.objects.create(name='Netflix_Noise_1')
        ec.add_session(subj)
        sess = ec.experiment.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.INITIALIZED)

        subj2 = Subject.objects.create(name='Netflix_Noise_2')
        ec.add_session(subj2)
        sess2 = ec.experiment.session_set.get(subject=subj2)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)

        random.seed(1)
        df = ESUtilities.export_playlist_ES_noise_study_style(ec, shuffle_intervals=True)
        self.assertEqual(df.columns.to_list(),
                         ['participant_id', 'content', 'noise_level', 'interval', 'trial', 'Filename'])
        self.assertEqual(df.iloc[0].to_list(),
                         ['Netflix_Noise_1', 1, -1, 'A', 0, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.08_psnr36.88_kbps115614.98_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[1].to_list(),
                         ['Netflix_Noise_1', 1, -1, 'B', 0, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.08_psnr36.88_kbps115614.98_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[2].to_list(),
                         ['Netflix_Noise_1', 1, -1, 'A', 1, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.08_psnr36.88_kbps115614.98_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[3].to_list(),
                         ['Netflix_Noise_1', 1, 0, 'B', 1, '/media/mp4/es_noise_study/test1a1b/breaking-bad-season-1-gray-mat-filmgrain-subj-test-prep-101-beamr5-20211020aopalach-__beamr5__3840_2160__ni_denoise_filter_before_scale__qp18_vmaf83.17_psnr34.15_kbps28163.51_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[10].to_list(),
                         ['Netflix_Noise_1', 0, 5, 'A', 5, '/media/mp4/es_noise_study/test1a1b/false-as-water-filmgrain-subj-test-prep-101b-beamr5-20211020aopalach-__beamr5__3840_2160__ni_denoise_with_target_noise_rmse_5_filter_before_scale__qp18_vmaf68.47_psnr33.67_kbps90682.35_fps24.0.mp4'])  # noqa E501
        self.assertEqual(df.iloc[-1].to_list(),
                         ['Netflix_Noise_2', 2, -1, 'B', 5, '/media/mp4/es_noise_study/test1a1b/PeeWeeS2Store-underVMAF-A-filmgrain-subj-test-prep-26-beamr5-20211007-__beamr5__960_540__none__qp37_vmaf26.91_psnr27.9_kbps283.91_fps29.97002997002997'])  # noqa E501

    def test_export_playlist_ES_noise_study_test2_samviq_style_shuffle_intervals(self):
        ec: ExperimentController = ExperimentUtils.create_experiment(
            experiment_config_filepath=NestConfig.tests_resource_path('es_noise_study_test2_small.json'),
            experimenter_username='lukas@catflix.com',
            is_test=True,
            random_seed=1,
            experiment_title='io_tests.TestCreateExperiment.test_export_playlist_ES_noise_study_test2_samviq_style_shuffle_intervals')

        subj = Subject.objects.create(name='Netflix_Noise_1')
        ec.add_session(subj)
        sess = ec.experiment.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.INITIALIZED)

        subj2 = Subject.objects.create(name='Netflix_Noise_2')
        ec.add_session(subj2)
        sess2 = ec.experiment.session_set.get(subject=subj2)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)

        random.seed(1)
        df = ESUtilities.export_playlist_ES_noise_study_style(ec, shuffle_intervals=True, methodology='samviq')
        self.assertEqual(len(df.index), 40)

        self.assertEqual(df.columns.to_list(),
                         ['participant_id', 'content', 'noise_level', 'interval', 'trial', 'Filename'])
        self.assertEqual(df.iloc[0].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'A', 0, '/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp37_vmaf70.18_psnr32.6_kbps1203.85_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[1].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'B', 0, '/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp25_vmaf90.48_psnr35.28_kbps20330.72_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[2].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'C', 0, '/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp31_vmaf81.11_psnr33.89_kbps2924.92_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[3].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'D', 0, '/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp28_vmaf85.76_psnr34.37_kbps6643.19_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[4].to_list(),
                         ['Netflix_Noise_1', 0, -1, 'E', 0, '/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test2/training/reference/taxi-driver-filmgrain-subj-test-prep-102-4-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp20_vmaf96.07_psnr37.97_kbps78842.2_fps23.976023976023978.mp4'])  # noqa E501
        self.assertEqual(df.iloc[-1].to_list(),
                         ['Netflix_Noise_2', 3, -1, 'E', 3, '/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test2/testing/reference/groundhog-day-filmgrain-subj-test-prep-102-3-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp18_vmaf93.49_psnr37.44_kbps86656.13_fps23.976023976023978.mp4'])  # noqa E501


class TestValidateConfig(TestCase):

    def test_validate_config(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'))

    def test_validate_config_dcr(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr.json'))

    def test_validate_config_mlds(self):
        with self.assertRaises(AssertionError):
            ExperimentUtils.validate_config(
                NestConfig.tests_resource_path('cvxhull_subjexp_toy_mlds.json'))

    def test_validate_config_mlds_bad(self):
        with self.assertRaises(AssertionError):
            ExperimentUtils.validate_config(
                NestConfig.tests_resource_path('cvxhull_subjexp_toy_mlds_bad.json'))

    def test_validate_config_dcr11d(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d.json'))

    def test_validate_config_dcr3d_standard(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr3d_standard.json'))

    def test_validate_config_dcr11d_standard(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d_standard.json'))

    def test_validate_config_dcr11d_standard_bad(self):
        with self.assertRaises(AssertionError):
            ExperimentUtils.validate_config(
                NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d_standard_bad.json'))

    def test_validate_config_dcr11d_bad_choices(self):
        with self.assertRaises(AssertionError):
            ExperimentUtils.validate_config(
                NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d_bad_choices.json'))

    def test_validate_config_samviq(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq.json'))

    def test_validate_config_samviq5d(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq5d.json'))

    def test_validate_config_acr5c(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr5c.json'))

    def test_validate_config_acr5c_standard(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr5c_standard.json'))

    def test_validate_config_tafc(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc.json'))

    def test_validate_config_tafc_standard(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc_standard.json'))

    def test_validate_config_ccr(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_ccr.json'))

    def test_validate_config_ccr_standard(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_ccr_standard.json'))

    def test_validate_config_acr_standard_2bad(self):
        with self.assertRaises(AssertionError) as e:
            ExperimentUtils.validate_config(
                NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr_standard_2bad.json'))
        self.assertTrue('stimulusvotegroup_id 0 cannot be used by multiple stimulusgroups' in str(e.exception))

    def test_validate_config_acr_standard_2(self):
        ExperimentUtils.validate_config(
            NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr_standard_2.json'))

    def test_validate_config_acr_standard_2bad_supersg(self):
        with self.assertRaises(AssertionError) as e:
            ExperimentUtils.validate_config(
                NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr_standard_2bad_supersg.json'))
        self.assertTrue('super_stimulusgroup_id must be all-present or all-absent' in str(e.exception))


class TestUserUtils(TestCase):

    def test_create_user_and_set_password(self):
        UserUtils.create_user('zli')
        user = User.objects.get(username='zli')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        UserUtils.create_user('lkrasula', is_staff=True)
        user2 = User.objects.get(username='lkrasula')
        self.assertTrue(user2.is_staff)
        self.assertFalse(user2.is_superuser)

        UserUtils.create_user('christosb', is_superuser=True)
        user3 = User.objects.get(username='christosb')
        self.assertFalse(user3.is_staff)
        self.assertTrue(user3.is_superuser)

        UserUtils.set_password('zli', 'abc123')
        UserUtils.set_password('lkrasula', 'abc123')
        UserUtils.set_password('christosb', 'abc123')
        self.assertTrue(User.objects.get(username='zli').check_password('abc123'))
        self.assertTrue(User.objects.get(username='lkrasula').check_password('abc123'))
        self.assertTrue(User.objects.get(username='christosb').check_password('abc123'))


class TestConfigFileGeneration(TestCase):

    def setUp(self):
        self.output_config_json_filepath = \
            NestConfig.tests_workdir_path('TestConfigFileGeneration.json')

    def tearDown(self):
        if os.path.exists(self.output_config_json_filepath):
            os.remove(self.output_config_json_filepath)

    def populate_stimuli(self, filedir, mode, d_contents, d_stimuli,
                         d_stimulusgroups, d_stimulusvotegroups, prioritized,
                         blocklist_stimulusgroup_ids, training_round_ids):
        for path in glob.glob(os.path.join(filedir, '*.mp4')):
            content = os.path.basename(path).split('__')[0]
            content_id = ExperimentConfigFileUtils. \
                add_to_content_dict(content, d_contents)
            stimulus_id = ExperimentConfigFileUtils. \
                add_to_stimulus_dict(map_media_local_to_url(path), content_id, d_stimuli)
            stimulus_ids = [stimulus_id]  # single stimulus
            stimulusvotegroup_id = ExperimentConfigFileUtils. \
                add_to_stimulusvotegroup_dict(stimulus_ids,
                                              d_stimulusvotegroups)
            stimulusvotegroup_ids = [stimulusvotegroup_id]  # one vote per round
            stimulusgroup_id = ExperimentConfigFileUtils. \
                add_to_stimulusgroup_dict(stimulusvotegroup_ids,
                                          d_stimulusgroups)
            ExperimentConfigFileUtils.populate_prioritized_etc(
                stimulusgroup_id, mode, prioritized,
                blocklist_stimulusgroup_ids,
                training_round_ids)

    def test_generate_config_file_acr(self):

        d_contents = dict()
        d_stimuli = dict()
        d_stimulusvotegroups = dict()
        d_stimulusgroups = dict()

        prioritized = list()
        blocklist_stimulusgroup_ids = list()
        training_round_ids = list()

        training_filedir = NestConfig.media_path('mp4', 'samples', 'Meridian')
        reliability_filedir = NestConfig.media_path('mp4', 'samples', 'SolLevante')
        testing_filedir = NestConfig.media_path('mp4', 'samples', 'Sparks')

        self.populate_stimuli(training_filedir, 'training',
                              d_contents, d_stimuli, d_stimulusgroups, d_stimulusvotegroups,
                              prioritized, blocklist_stimulusgroup_ids, training_round_ids)
        self.populate_stimuli(reliability_filedir, 'reliability',
                              d_contents, d_stimuli, d_stimulusgroups, d_stimulusvotegroups,
                              prioritized, blocklist_stimulusgroup_ids, training_round_ids)
        self.populate_stimuli(testing_filedir, 'testing',
                              d_contents, d_stimuli, d_stimulusgroups, d_stimulusvotegroups,
                              prioritized, blocklist_stimulusgroup_ids, training_round_ids)

        additions = [
            {
                "position": {
                    "round_id": 0,
                    "before_or_after": "before"
                },
                "context": {
                    "title": "Instruction",
                    "text_html": "<p> This test involves evaluating the perceptual quality of videos. Please <b> set the browser in full-screen mode (shortcut: Control + Command + F) </b>. Please sit in a position such that your eyes are roughly aligned with the straight line marked on the floor. </p> <p> In each round, you are presented with two videos: Video A and Video B. Watch the videos and vote on which video has the better quality. </p> <p> There is no audio. You are expected to evaluate the <b> video quality </b> only. </p> <p> Videoss will loop over in the order of A -> B -> A ... up to <b> three times </b>. After the first time, you can <b> press \"space\" key or double click mouse </b> to skip to the voting page. </p>",  # noqa E501
                    "actions_html": "\n            <p>\n                <a class=\"button\" href=\"{action_url}\"  id=\"start\">Start Test</a>\n            </p>\n            "  # noqa E501
                }
            },
            {
                "position": {
                    "round_id": 0,
                    "before_or_after": "before"
                },
                "context": {
                    "title": "Training",
                    "text_html": " <p> To get you familiar with the test procedure, let's start with some training before kicking off the test officially. </p> ",  # noqa E501
                    "actions_html": "\n            <p>\n                <a class=\"button\" href=\"{action_url}\"  id=\"start\">Start Training</a>\n            </p>\n            "  # noqa E501
                }
            },
            {
                "position": {
                    "round_id": len(list(glob.glob(os.path.join(training_filedir, '*.mp4')))),
                    "before_or_after": "before"
                },
                "context": {
                    "title": "Start the test",
                    "text_html": " <p> Now let's officially start the test. </p> ",
                    "actions_html": "\n            <p>\n                <a class=\"button\" href=\"{action_url}\"  id=\"start\">Start Test</a>\n            </p>\n            "  # noqa E501
                }
            }
        ]

        round_context = {
            'video_display_percentage': 75,
            'video_show_controls': True,
        }

        stimulus_config = dict()
        stimulus_config['contents'] = list(d_contents.values())
        stimulus_config['stimuli'] = list(d_stimuli.values())
        stimulus_config['stimulusvotegroups'] = list(d_stimulusvotegroups.values())
        stimulus_config['stimulusgroups'] = list(d_stimulusgroups.values())

        experiment_config = dict()
        experiment_config['title'] = 'cvxhull_subjexp'
        experiment_config['description'] = 'convex hull subject test'
        experiment_config['vote_scale'] = "FIVE_POINT"
        experiment_config['methodology'] = 'acr'
        experiment_config['rounds_per_session'] = 16  # 8 stimuli, each twice
        experiment_config['random_seed'] = None
        experiment_config['prioritized'] = prioritized
        experiment_config['blocklist_stimulusgroup_ids'] = blocklist_stimulusgroup_ids
        experiment_config['training_round_ids'] = training_round_ids
        experiment_config['additions'] = additions
        experiment_config['round_context'] = round_context

        config = dict()
        config['stimulus_config'] = stimulus_config
        config['experiment_config'] = experiment_config

        expected_config = {'stimulus_config': {'contents': [{'content_id': 0, 'name': 'Meridian_A'}, {'content_id': 1, 'name': 'SolLevante10k_B'}, {'content_id': 2, 'name': 'Sparks_A'}], 'stimuli': [{'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__Hdr10Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf93.88_phonevmaf101.62_psnr42.45_kbps6509.97.mp4', 'stimulus_id': 0, 'type': 'video/mp4', 'content_id': 0}, {'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4', 'stimulus_id': 1, 'type': 'video/mp4', 'content_id': 0}, {'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__1920_1080__3000_enable_audio_False_vmaf95.93_phonevmaf100.00_psnr50.59_kbps3092.62.mp4', 'stimulus_id': 2, 'type': 'video/mp4', 'content_id': 0}, {'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__Dovi5Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf107.81_phonevmaf106.05_psnr24.30_kbps6441.59.mp4', 'stimulus_id': 3, 'type': 'video/mp4', 'content_id': 0}, {'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4', 'stimulus_id': 4, 'type': 'video/mp4', 'content_id': 0}, {'path': '/media/mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf27.22_phonevmaf42.03_psnr25.61_kbps642.42.mp4', 'stimulus_id': 5, 'type': 'video/mp4', 'content_id': 1}, {'path': '/media/mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__Hdr10Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf84.91_phonevmaf97.04_psnr37.76_kbps6894.95.mp4', 'stimulus_id': 6, 'type': 'video/mp4', 'content_id': 1}, {'path': '/media/mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__SdrVvhevce2pVE__1920_1080__3000_enable_audio_False_vmaf69.73_phonevmaf81.88_psnr26.71_kbps3699.96.mp4', 'stimulus_id': 7, 'type': 'video/mp4', 'content_id': 1}, {'path': '/media/mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__Dovi5Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf97.35_phonevmaf102.00_psnr18.69_kbps6954.28.mp4', 'stimulus_id': 8, 'type': 'video/mp4', 'content_id': 1}, {'path': '/media/mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf85.63_phonevmaf95.85_psnr26.99_kbps7275.37.mp4', 'stimulus_id': 9, 'type': 'video/mp4', 'content_id': 1}, {'path': '/media/mp4/samples/Sparks/Sparks_A__2_0_2_5__Dovi5Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf96.18_phonevmaf102.44_psnr22.73_kbps6206.91.mp4', 'stimulus_id': 10, 'type': 'video/mp4', 'content_id': 2}, {'path': '/media/mp4/samples/Sparks/Sparks_A__2_0_2_5__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf49.65_phonevmaf70.00_psnr31.50_kbps541.32.mp4', 'stimulus_id': 11, 'type': 'video/mp4', 'content_id': 2}, {'path': '/media/mp4/samples/Sparks/Sparks_A__2_0_2_5__SdrVvhevce2pVE__1920_1080__3000_enable_audio_False_vmaf76.41_phonevmaf92.39_psnr35.21_kbps3088.96.mp4', 'stimulus_id': 12, 'type': 'video/mp4', 'content_id': 2}, {'path': '/media/mp4/samples/Sparks/Sparks_A__2_0_2_5__Hdr10Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf83.87_phonevmaf96.84_psnr37.11_kbps6081.28.mp4', 'stimulus_id': 13, 'type': 'video/mp4', 'content_id': 2}, {'path': '/media/mp4/samples/Sparks/Sparks_A__2_0_2_5__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf84.08_phonevmaf96.96_psnr35.37_kbps6075.91.mp4', 'stimulus_id': 14, 'type': 'video/mp4', 'content_id': 2}], 'stimulusvotegroups': [{'stimulus_ids': [0], 'stimulusvotegroup_id': 0}, {'stimulus_ids': [1], 'stimulusvotegroup_id': 1}, {'stimulus_ids': [2], 'stimulusvotegroup_id': 2}, {'stimulus_ids': [3], 'stimulusvotegroup_id': 3}, {'stimulus_ids': [4], 'stimulusvotegroup_id': 4}, {'stimulus_ids': [5], 'stimulusvotegroup_id': 5}, {'stimulus_ids': [6], 'stimulusvotegroup_id': 6}, {'stimulus_ids': [7], 'stimulusvotegroup_id': 7}, {'stimulus_ids': [8], 'stimulusvotegroup_id': 8}, {'stimulus_ids': [9], 'stimulusvotegroup_id': 9}, {'stimulus_ids': [10], 'stimulusvotegroup_id': 10}, {'stimulus_ids': [11], 'stimulusvotegroup_id': 11}, {'stimulus_ids': [12], 'stimulusvotegroup_id': 12}, {'stimulus_ids': [13], 'stimulusvotegroup_id': 13}, {'stimulus_ids': [14], 'stimulusvotegroup_id': 14}], 'stimulusgroups': [{'stimulusvotegroup_ids': [0], 'stimulusgroup_id': 0}, {'stimulusvotegroup_ids': [1], 'stimulusgroup_id': 1}, {'stimulusvotegroup_ids': [2], 'stimulusgroup_id': 2}, {'stimulusvotegroup_ids': [3], 'stimulusgroup_id': 3}, {'stimulusvotegroup_ids': [4], 'stimulusgroup_id': 4}, {'stimulusvotegroup_ids': [5], 'stimulusgroup_id': 5}, {'stimulusvotegroup_ids': [6], 'stimulusgroup_id': 6}, {'stimulusvotegroup_ids': [7], 'stimulusgroup_id': 7}, {'stimulusvotegroup_ids': [8], 'stimulusgroup_id': 8}, {'stimulusvotegroup_ids': [9], 'stimulusgroup_id': 9}, {'stimulusvotegroup_ids': [10], 'stimulusgroup_id': 10}, {'stimulusvotegroup_ids': [11], 'stimulusgroup_id': 11}, {'stimulusvotegroup_ids': [12], 'stimulusgroup_id': 12}, {'stimulusvotegroup_ids': [13], 'stimulusgroup_id': 13}, {'stimulusvotegroup_ids': [14], 'stimulusgroup_id': 14}]}, 'experiment_config': {'title': 'cvxhull_subjexp', 'description': 'convex hull subject test', 'vote_scale': 'FIVE_POINT', 'methodology': 'acr', 'rounds_per_session': 16, 'random_seed': None, 'prioritized': [{'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0}, {'session_idx': None, 'round_id': 1, 'stimulusgroup_id': 1}, {'session_idx': None, 'round_id': 2, 'stimulusgroup_id': 2}, {'session_idx': None, 'round_id': 3, 'stimulusgroup_id': 3}, {'session_idx': None, 'round_id': 4, 'stimulusgroup_id': 4}, {'session_idx': None, 'round_id': None, 'stimulusgroup_id': 5}, {'session_idx': None, 'round_id': None, 'stimulusgroup_id': 6}, {'session_idx': None, 'round_id': None, 'stimulusgroup_id': 7}, {'session_idx': None, 'round_id': None, 'stimulusgroup_id': 8}, {'session_idx': None, 'round_id': None, 'stimulusgroup_id': 9}], 'blocklist_stimulusgroup_ids': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 'training_round_ids': [0, 1, 2, 3, 4], 'additions': [{'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': 'Instruction', 'text_html': '<p> This test involves evaluating the perceptual quality of videos. Please <b> set the browser in full-screen mode (shortcut: Control + Command + F) </b>. Please sit in a position such that your eyes are roughly aligned with the straight line marked on the floor. </p> <p> In each round, you are presented with two videos: Video A and Video B. Watch the videos and vote on which video has the better quality. </p> <p> There is no audio. You are expected to evaluate the <b> video quality </b> only. </p> <p> Videoss will loop over in the order of A -> B -> A ... up to <b> three times </b>. After the first time, you can <b> press "space" key or double click mouse </b> to skip to the voting page. </p>', 'actions_html': '\n            <p>\n                <a class="button" href="{action_url}"  id="start">Start Test</a>\n            </p>\n            '}}, {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': 'Training', 'text_html': " <p> To get you familiar with the test procedure, let's start with some training before kicking off the test officially. </p> ", 'actions_html': '\n            <p>\n                <a class="button" href="{action_url}"  id="start">Start Training</a>\n            </p>\n            '}}, {'position': {'round_id': 5, 'before_or_after': 'before'}, 'context': {'title': 'Start the test', 'text_html': " <p> Now let's officially start the test. </p> ", 'actions_html': '\n            <p>\n                <a class="button" href="{action_url}"  id="start">Start Test</a>\n            </p>\n            '}}], 'round_context': {'video_display_percentage': 75, 'video_show_controls': True}}}  # noqa E501
        self.assertDictEqual(config, expected_config)

        config_json = json.dumps(config, indent=2)
        with open(self.output_config_json_filepath, 'wt') as f:
            f.write(config_json)
        ExperimentUtils.validate_config(self.output_config_json_filepath)
