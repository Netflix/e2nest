import logging

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from nest.config import NestConfig
from nest.io import ExperimentUtils
from nest.models import Subject


class TestViews(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user('user', password='pass', is_staff=True)
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        self.user.delete()
        logging.disable(logging.NOTSET)

    def test_login(self):
        response = self.client.get(reverse('admin:login'))
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        response = self.client.get(reverse('admin:logout'))
        self.assertEqual(response.status_code, 302)

    def test_nestexp_with_login(self):
        response = self.client.get(reverse('admin:nestexp'))
        self.assertEqual(response.status_code, 302)

        login = self.client.login(username='user', password='paxx')
        self.assertFalse(login)

        login = self.client.login(username='user', password='pass')
        self.assertTrue(login)

        response = self.client.get(reverse('admin:nestexp'))
        self.assertEqual(response.status_code, 200)

    def test_nestexp(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(reverse('admin:nestexp'))
        self.assertEqual(response.status_code, 200)

    def test_nest_download_sureal(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json'),
            is_test=True,
            random_seed=1,
            experiment_title='nest_view_tests.TestViewsWithWriteDataset.test_step_session')

        subj: Subject = Subject.create_by_username('user')
        ec.add_session(subj)

        self.client.login(username='user', password='pass')

        self.client.get(reverse('nest:start_session', kwargs={'session_id': 1}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr': '1'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.post(reverse('nest:step_session', kwargs={'session_id': 1}), {'acr': '4'})
        self.client.get(reverse('nest:step_session', kwargs={'session_id': 1}))
        self.client.login(username='staff', password='pass')
        response = self.client.get(reverse('admin:download_sureal', args=(1,)))
        self.assertEqual(response.status_code, 200)
