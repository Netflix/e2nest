import logging
import os
import shutil

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from nest.config import NestConfig
from nest.control import ExperimentController
from nest.io import ExperimentUtils, export_sureal_dataset
from nest.models import CcrThreePointVote, ElevenPointVote, FivePointVote, Round, SevenPointVote, Stimulus, \
    StimulusVoteGroup, Subject, TafcVote, ThreePointVote, Vote, Zero2HundredVote
from nest.sites import NestSite


class TestViews(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user('user', password='pass', is_staff=False)
        self.staff = User.objects.create_user('staff', password='pass', is_staff=True)

    def tearDown(self):
        self.user.delete()
        self.staff.delete()

    def test_login(self):
        response = self.client.get(reverse('nest:login'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:login'))
        self.assertEqual(response.status_code, 302)  # already logged in - redirect

    def test_logout(self):
        response = self.client.get(reverse('nest:logout'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:logout'))
        self.assertEqual(response.status_code, 200)

    def test_change_password(self):
        response = self.client.get(reverse('nest:password_change'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:password_change'))
        self.assertEqual(response.status_code, 200)

    def test_nestexp_with_login(self):
        response = self.client.get(reverse('admin:nestexp'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='paxx')
        self.assertFalse(login)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:nestexp'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:nestexp'))
        self.assertEqual(response.status_code, 200)

    def test_index_with_login(self):
        response = self.client.get(reverse('nest:index'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:index'))
        self.assertEqual(response.status_code, 302)

    def test_status_with_login(self):
        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

    def test_instruction_with_login(self):
        response = self.client.get(reverse('nest:instruction_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='paxx')
        self.assertFalse(login)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:instruction_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:instruction_demo'))
        self.assertEqual(response.status_code, 200)

    def test_acr_with_login(self):
        response = self.client.get(reverse('nest:acr_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:acr_demo'))
        self.assertEqual(response.status_code, 200)

    def test_acr5c_with_login(self):
        response = self.client.get(reverse('nest:acr5c_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:acr5c_demo'))
        self.assertEqual(response.status_code, 200)

    def test_acr5c_standard_with_login(self):
        response = self.client.get(reverse('nest:acr5c_standard_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:acr5c_standard_demo'))
        self.assertEqual(response.status_code, 200)

    def test_dcr_with_login(self):
        response = self.client.get(reverse('nest:dcr_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:dcr_demo'))
        self.assertEqual(response.status_code, 200)

    def test_tafc_with_login(self):
        response = self.client.get(reverse('nest:tafc_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:tafc_demo'))
        self.assertEqual(response.status_code, 200)

    def test_dcr11d_with_login(self):
        response = self.client.get(reverse('nest:dcr11d_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:dcr11d_demo'))
        self.assertEqual(response.status_code, 200)

    def test_dcr11d_standard_with_login(self):
        response = self.client.get(reverse('nest:dcr11d_standard_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:dcr11d_standard_demo'))
        self.assertEqual(response.status_code, 200)

    def test_samviq_with_login(self):
        response = self.client.get(reverse('nest:samviq_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:samviq_demo'))
        self.assertEqual(response.status_code, 200)

    def test_samviq5d_with_login(self):
        response = self.client.get(reverse('nest:samviq5d_demo'))
        self.assertEqual(response.status_code, 200)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:samviq5d_demo'))
        self.assertEqual(response.status_code, 200)


class TestViewsWithWriteDataset(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user('user', password='pass', is_staff=False)
        self.staff = User.objects.create_user('staff', password='pass', is_staff=True)
        self.config_filedir = os.path.dirname(NestSite.get_experiment_config_filepath("xxx", is_test=True))
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        self.user.delete()
        self.staff.delete()
        shutil.rmtree(self.config_filedir)
        logging.disable(logging.NOTSET)

    def test_start_and_step_session_with_login_and_cookie(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_start_and_step_session_with_login_and_cookie')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        # hit cookie_failed with 200, because haven't set_test_cookie()
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        # hit 302: redirect to step_session page
        self.assertEqual(response.status_code, 302)

        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        s = self.client.session
        s.delete_test_cookie()
        s.save()
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        # hit cookie_failed with 200, because delete_test_cookie()
        self.assertEqual(response.status_code, 200)

    def test_step_session_with_login_and_cookie(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_with_login_and_cookie')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        # hit cookie_failed with 200, because haven't set_test_cookie()
        self.assertEqual(response.status_code, 200)

        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        s = self.client.session
        s.delete_test_cookie()
        s.save()
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        # hit cookie_failed with 200, because delete_test_cookie()
        self.assertEqual(response.status_code, 200)

    def test_step_session(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session')

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session['session_id'], 1)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr_1': '1'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['session_id'], 1)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr_0': '4'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session['session_id'], 1)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 4})

        response = self.client.get(reverse('nest:cookie'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(""""score": {\n                    "0": 4""" in response.context_data['text_html'])

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 4)
        self.assertEqual(FivePointVote.objects.first().score, 1)
        self.assertEqual(FivePointVote.objects.all()[1].score, 4)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(AssertionError):
            # ACR cannot do alt: ignore_against (there is no against to ignore)
            self.client.get(reverse('admin:download_sureal_alt', args=(1,)))

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': 'user', 'rounds': [
                     {'round_id': 0, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 1.0}]},
                     {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 4.0}]}]})

        # add second session with repetitions:
        sess2 = ec.add_session(subj)
        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'acr_0': '1'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'acr_1': '3'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.login(username='staff', password='pass')

        sinfo2 = ec.get_session_info(sess2)
        self.assertEqual(
            sinfo2,
            {'session_id': 2, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 1.0}]},
                {'round_id': 1, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 3.0}]}]})

        einfo: dict = ec.get_experiment_info()
        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (4, 8))

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        dataset = export_sureal_dataset('nest_view_tests.TestViewsWithWriteDataset.test_step_session')
        self.assertEqual(dataset.dis_videos[0]['os'], {'user': [4.0, 1.0]})
        self.assertEqual(dataset.dis_videos[1]['os'], {'user': [1.0, 3.0]})

        # test reset session
        self.assertEqual(sess.round_set.first().vote_set.count(), 1)
        response = self.client.get(reverse('nest:reset_session', kwargs={'session_id': sess.id}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(sess.round_set.first().vote_set.count(), 0)

    def test_step_session_acr5c(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr5c.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr5c_1': '18'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 18})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr5c_0': '89'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 89})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, 18)
        self.assertEqual(Vote.objects.all()[1].score, 89)
        self.assertEqual(Zero2HundredVote.objects.first().score, 18)
        self.assertEqual(Zero2HundredVote.objects.all()[1].score, 89)

    def test_step_session_acr5c_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_acr5c_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr5c_1': '18'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 18})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr5c_0': '89'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 89})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, 18)
        self.assertEqual(Vote.objects.all()[1].score, 89)
        self.assertEqual(Zero2HundredVote.objects.first().score, 18)
        self.assertEqual(Zero2HundredVote.objects.all()[1].score, 89)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

    def test_step_session_dcr(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_dcr.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_dcr')

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_0': '5'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 5})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 5)
        self.assertEqual(FivePointVote.objects.first().score, 1)
        self.assertEqual(FivePointVote.objects.all()[1].score, 5)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:download_sureal_alt', args=(1,)))
        self.assertEqual(response.status_code, 200)

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 1.0}]},
                {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 5.0}]}]})

        einfo: dict = ec.get_experiment_info()
        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (2, 10))

        r1 = Round.objects.get(session=sess, round_id=0)
        r2 = Round.objects.get(session=sess, round_id=1)
        self.assertTrue(r1.response_sec > 0)
        self.assertTrue(r2.response_sec > 0)

        # add second session with repetitions:
        sess2 = ec.add_session(subj)
        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'dcr_0': '1'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'dcr_1': '4'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.login(username='staff', password='pass')

        sinfo2 = ec.get_session_info(sess2)
        self.assertEqual(
            sinfo2,
            {'session_id': 2, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 1.0}]},
                {'round_id': 1, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 4.0}]}]})

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        dataset = export_sureal_dataset('nest_view_tests.TestViewsWithWriteDataset.test_step_session_dcr',
                                        ignore_against=True)
        self.assertEqual(dataset.dis_videos[0]['os'], {'user': [5.0, 1.0]})
        self.assertEqual(dataset.dis_videos[1]['os'], {'user': [1.0, 4.0]})

    def test_step_session_dcr11d(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_dcr11d')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_0': '4'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 4})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(ElevenPointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 4)
        self.assertEqual(ElevenPointVote.objects.first().score, 1)
        self.assertEqual(ElevenPointVote.objects.all()[1].score, 4)

    def test_step_session_dcr3d_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr3d_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_dcr3d_standard')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_0': '3'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 3})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(ThreePointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 3)
        self.assertEqual(ThreePointVote.objects.first().score, 1)
        self.assertEqual(ThreePointVote.objects.all()[1].score, 3)

    def test_step_session_dcr7d_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr7d_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_dcr7d_standard')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_0': '7'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 7})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(SevenPointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 7)
        self.assertEqual(SevenPointVote.objects.first().score, 1)
        self.assertEqual(SevenPointVote.objects.all()[1].score, 7)

    def test_step_session_dcr11d_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_dcr11d_standard')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'dcr_0': '4'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 4})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(ElevenPointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 4)
        self.assertEqual(ElevenPointVote.objects.first().score, 1)
        self.assertEqual(ElevenPointVote.objects.all()[1].score, 4)

    def test_step_session_samviq(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_samviq')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                                    {'samviq_2': "18", "samviq_3": "89"})  # key: svg; value: score
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'2': 18, '3': 89})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                                    {"samviq_0": "2", "samviq_1": "4"})  # key: svg; value: score
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 2, '1': 4})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 4)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 4)

        self.assertEqual(Vote.objects.first().score, 18)
        self.assertEqual(Vote.objects.all()[1].score, 89)
        self.assertEqual(Vote.objects.all()[2].score, 2)
        self.assertEqual(Vote.objects.all()[3].score, 4)

        stim_1_ref = Stimulus.objects.get(stimulus_id=0)
        stim_1_dis1 = Stimulus.objects.get(stimulus_id=1)
        stim_1_dis2 = Stimulus.objects.get(stimulus_id=2)
        stim_2_ref = Stimulus.objects.get(stimulus_id=3)
        stim_2_dis1 = Stimulus.objects.get(stimulus_id=4)
        stim_2_dis2 = Stimulus.objects.get(stimulus_id=5)
        svg_1_1 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_1_dis1, stim_1_ref)[0]
        svg_1_2 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_1_dis2, stim_1_ref)[0]
        svg_2_1 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_2_dis1, stim_2_ref)[0]
        svg_2_2 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_2_dis2, stim_2_ref)[0]
        self.assertEqual(Zero2HundredVote.objects.get(stimulusvotegroup=svg_1_1).score, 2)
        self.assertEqual(Zero2HundredVote.objects.get(stimulusvotegroup=svg_1_2).score, 4)
        self.assertEqual(Zero2HundredVote.objects.get(stimulusvotegroup=svg_2_1).score, 18)
        self.assertEqual(Zero2HundredVote.objects.get(stimulusvotegroup=svg_2_2).score, 89)

    def test_step_session_samviq5d(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq5d.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_samviq5d')

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                                    {'samviq5d_2': "1", "samviq5d_3": "3"})  # key: svg; value: score
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'2': 1, '3': 3})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                                    {"samviq5d_0": "2", "samviq5d_1": "4"})  # key: svg; value: score
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 2, '1': 4})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 4)
        self.assertEqual(FivePointVote.objects.count(), 4)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 3)
        self.assertEqual(Vote.objects.all()[2].score, 2)
        self.assertEqual(Vote.objects.all()[3].score, 4)

        stim_1_ref = Stimulus.objects.get(stimulus_id=0)
        stim_1_dis1 = Stimulus.objects.get(stimulus_id=1)
        stim_1_dis2 = Stimulus.objects.get(stimulus_id=2)
        stim_2_ref = Stimulus.objects.get(stimulus_id=3)
        stim_2_dis1 = Stimulus.objects.get(stimulus_id=4)
        stim_2_dis2 = Stimulus.objects.get(stimulus_id=5)
        svg_1_1 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_1_dis1, stim_1_ref)[0]
        svg_1_2 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_1_dis2, stim_1_ref)[0]
        svg_2_1 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_2_dis1, stim_2_ref)[0]
        svg_2_2 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim_2_dis2, stim_2_ref)[0]
        self.assertEqual(FivePointVote.objects.get(stimulusvotegroup=svg_1_1).score, 2)
        self.assertEqual(FivePointVote.objects.get(stimulusvotegroup=svg_1_2).score, 4)
        self.assertEqual(FivePointVote.objects.get(stimulusvotegroup=svg_2_1).score, 1)
        self.assertEqual(FivePointVote.objects.get(stimulusvotegroup=svg_2_2).score, 3)

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 2, 'vote': 1.0},
                                                                              {'stimulusvotegroup_id': 3, 'vote': 3.0}]},
                {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 2.0},
                                                                              {'stimulusvotegroup_id': 1, 'vote': 4.0}]}]})

        einfo: dict = ec.get_experiment_info()
        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (4, 10))

        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:download_sureal_alt', args=(1,)))
        self.assertEqual(response.status_code, 200)
        dataset = export_sureal_dataset('nest_view_tests.TestViewsWithWriteDataset.test_step_session_samviq5d',
                                        ignore_against=True)
        self.assertEqual(dataset.dis_videos[0]['os'], {})
        self.assertEqual(dataset.dis_videos[1]['os'], {'user': 2.0})
        self.assertEqual(dataset.dis_videos[2]['os'], {'user': 4.0})
        self.assertEqual(dataset.dis_videos[3]['os'], {})
        self.assertEqual(dataset.dis_videos[4]['os'], {'user': 1.0})
        self.assertEqual(dataset.dis_videos[5]['os'], {'user': 3.0})

    def test_step_session_tafc(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_tafc')

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'tafc_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'tafc_0': '0'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 0})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)
        self.assertEqual(TafcVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 0)
        self.assertEqual(TafcVote.objects.first().score, 1)
        self.assertEqual(TafcVote.objects.all()[1].score, 0)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:download_sureal_alt', args=(1,)))
        self.assertEqual(response.status_code, 200)

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 1.0}]},
                {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 0.0}]}]})

        # add second session with repetitions:
        sess2 = ec.add_session(subj)
        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'tafc_0': '1'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'tafc_1': '0'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.login(username='staff', password='pass')

        sinfo2 = ec.get_session_info(sess2)
        self.assertEqual(
            sinfo2,
            {'session_id': 2, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 1.0}]},
                {'round_id': 1, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 0.0}]}]})

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        dataset = export_sureal_dataset('nest_view_tests.TestViewsWithWriteDataset.test_step_session_tafc',
                                        ignore_against=False)
        self.assertEqual(dataset.dis_videos[0]['os'], {('user', 0): [0.0, 1.0]})
        self.assertEqual(dataset.dis_videos[1]['os'], {('user', 0): [1.0, 0.0]})

        einfo: dict = ec.get_experiment_info()
        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (4, 10))

    def test_step_session_tafc_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.cvxhull_subjexp_toy_x_tafc_standard')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'tafc_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'tafc_0': '0'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 0})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)
        self.assertEqual(TafcVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 0)
        self.assertEqual(TafcVote.objects.first().score, 1)
        self.assertEqual(TafcVote.objects.all()[1].score, 0)

    def test_step_session_mismatched_session_and_cache(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.cvxhull_subjexp_toy_x_tafc_standard')

        ec2 = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_tafc')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)
        ec2.add_session(subj)

        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:status'))

        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))

        with self.assertRaises(AssertionError):
            self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))

    def test_step_session_samviq_with_double_post_issue(self):
        # reproducing issue reported by TY 2/20/2022
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_samviq_with_double_post_issue')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:status'))
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))

        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))  # instruction

        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                         {'samviq_2': "18", "samviq_3": "89"})  # round 1

        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                         {'samviq_2': "18", "samviq_3": "89"})  # round 1, double post

        # mistakenly submit, but should just be step:
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))

        # not yet recording result in database:
        self.assertEqual(Vote.objects.count(), 0)

    def test_step_session_samviq5d_with_double_post_issue(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq5d.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_samviq5d_with_double_post_issue')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:status'))
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))

        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))  # instruction

        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                         {'samviq5d_2': "1", "samviq5d_3": "3"})  # round 1

        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                         {'samviq5d_2': "1", "samviq5d_3": "3"})  # round 1, double post

        # mistakenly submit, but should just be step:
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))

        # not yet recording result in database:
        self.assertEqual(Vote.objects.count(), 0)

    def test_step_session_acr_with_double_post_issue(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_acr_with_double_post_issue')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:status'))
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))

        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))  # instruction

        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                         {'acr_1': '1'})  # round 1

        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}),
                         {'acr_1': '1'})  # round 1, double post

        # mistakenly submit, but should just be step:
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))

        # not yet recording result in database:
        self.assertEqual(Vote.objects.count(), 0)

    def test_step_session_ccr(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_ccr.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session_ccr')

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'ccr_1': '2'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 2})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'ccr_0': '0'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 0})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)
        self.assertEqual(CcrThreePointVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, 2)
        self.assertEqual(Vote.objects.all()[1].score, 0)
        self.assertEqual(CcrThreePointVote.objects.first().score, 2)
        self.assertEqual(CcrThreePointVote.objects.all()[1].score, 0)

        login = self.client.login(username='staff', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:download_sureal_alt', args=(1,)))
        self.assertEqual(response.status_code, 200)

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 2.0}]},
                {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 0.0}]}]})

        # add second session with repetitions:
        sess2 = ec.add_session(subj)
        self.client.login(username='user', password='pass')
        self.client.get(reverse('nest:start_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'ccr_0': '2'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 2}), {'ccr_1': '0'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 2}))
        self.client.login(username='staff', password='pass')

        sinfo2 = ec.get_session_info(sess2)
        self.assertEqual(
            sinfo2,
            {'session_id': 2, 'subject': 'user', 'rounds': [
                {'round_id': 0, 'stimulusgroup_id': 0, 'stimulusvotegroups': [{'stimulusvotegroup_id': 0, 'vote': 2.0}]},
                {'round_id': 1, 'stimulusgroup_id': 1, 'stimulusvotegroups': [{'stimulusvotegroup_id': 1, 'vote': 0.0}]}]})

        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
        dataset = export_sureal_dataset('nest_view_tests.TestViewsWithWriteDataset.test_step_session_ccr',
                                        ignore_against=False)
        self.assertEqual(dataset.dis_videos[0]['os'], {('user', 0): [0.0, 2.0]})
        self.assertEqual(dataset.dis_videos[1]['os'], {('user', 0): [2.0, 0.0]})

        einfo: dict = ec.get_experiment_info()
        df = ExperimentController.denormalize_experiment_info(einfo)
        self.assertEqual(df.shape, (4, 10))

    def test_step_session_ccr_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_ccr_standard.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.cvxhull_subjexp_toy_x_ccr_standard')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('nest:status'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 1)
        self.assertTrue(NestSite._step_is_addition(steps[0]))

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'ccr_1': '1'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 2)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'1': 1})

        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'ccr_0': '2'})
        self.assertEqual(response.status_code, 302)
        steps = self.client.session['steps']
        self.assertEqual(len(steps), 3)
        self.assertFalse(NestSite._step_is_addition(steps[-1]))
        self.assertEqual(steps[-1]['context']['score'], {'0': 2})

        self.assertEqual(Vote.objects.count(), 0)
        response = self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)
        self.assertEqual(CcrThreePointVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 2)
        self.assertEqual(CcrThreePointVote.objects.first().score, 1)
        self.assertEqual(CcrThreePointVote.objects.all()[1].score, 2)
