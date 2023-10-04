import os
import unittest
from time import sleep

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from nest.config import NestConfig
from nest.io import ExperimentUtils
from nest.models import ElevenPointVote, FivePointVote, Round, SevenPointVote, \
    Subject, TafcVote, ThreePointVote, Vote, Zero2HundredVote, CcrThreePointVote
from nest.sites import NestSite
from nest_site import settings
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait

os.environ['PATH'] += os.pathsep + os.path.dirname(settings.CHROMEDRIVER_PATH)

MSG_INCORRECT_CHROMEDRIVER_PATH = \
    'CHROMEDRIVER_PATH must be correctly set to chromedriver in ' \
    'nest_site.settings, see https://chromedriver.chromium.org/home'


class LoginMixin(object):

    LOGIN_SUCCESS_MSG = 'Welcome'
    LOGOUT_SUCCESS_MSG = 'Thanks for spending some quality time with the Web site today.'

    def login(self):
        self.browser.get(self.live_server_url + reverse("nest:login"))
        self.browser.find_element(by='name', value='username').send_keys('user')
        self.browser.find_element(by='name', value='password').send_keys('pass')
        self.browser.find_element(by='xpath', value='//input[@value="Log in"]').click()
        WebDriverWait(self.browser, 10).until(
            lambda driver: driver.find_element('tag name', 'body'))
        self.assertTrue(self.LOGIN_SUCCESS_MSG in self.browser.page_source)

    def logout(self):
        self.browser.get(self.live_server_url + reverse("nest:logout"))
        WebDriverWait(self.browser, 10).until(
            lambda driver: driver.find_element('tag name', 'body'))
        self.assertTrue(self.LOGOUT_SUCCESS_MSG in self.browser.page_source)


@unittest.skipUnless(
    hasattr(settings, 'CHROMEDRIVER_PATH') and os.path.exists(settings.CHROMEDRIVER_PATH),
    MSG_INCORRECT_CHROMEDRIVER_PATH)
class TestBrowser(StaticLiveServerTestCase, LoginMixin):

    browser = None

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user('user', password='pass', is_staff=False)
        options = Options()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')
        self.browser = webdriver.Chrome(options=options)
        self.browser.implicitly_wait(10)

    def tearDown(self):
        self.browser.quit()
        self.user.delete()
        super().tearDown()

    def test_login_logout(self):
        self.login()
        self.logout()


@unittest.skipUnless(
    hasattr(settings, 'CHROMEDRIVER_PATH') and os.path.exists(settings.CHROMEDRIVER_PATH),
    MSG_INCORRECT_CHROMEDRIVER_PATH)
class TestBrowserWithWriteDataset(StaticLiveServerTestCase, LoginMixin):

    EXPERIMENT_TITLE = 'nest_browser_tests.TestBrowserWithWriteDataset'

    def setUp(self):
        super().setUp()
        self.config_filepath = NestSite.get_experiment_config_filepath(self.EXPERIMENT_TITLE, is_test=False)
        self.user = User.objects.create_user('user', password='pass', is_staff=False)
        options = Options()
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument('--headless')
        self.browser = webdriver.Chrome(options=options)
        self.browser.implicitly_wait(10)

    def tearDown(self):
        os.remove(self.config_filepath)
        self.user.delete()
        self.browser.quit()
        super().tearDown()

    def test_status_page(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_dcr.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)
        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)
        self.login()
        self.assertTrue(self.EXPERIMENT_TITLE in self.browser.page_source)
        self.assertTrue(str(sess.id) in self.browser.page_source)
        self.assertTrue('New' in self.browser.page_source)
        self.assertTrue('Start' in self.browser.page_source)

    def test_step_session_dcr(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_dcr.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)
        self.login()
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        self.browser.find_element(by='id', value='start').click()
        self.assertTrue('Round 1 of 2' in self.browser.page_source)
        self.browser.find_element(by='id', value='video_a').click()
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        self.browser.find_element(by='id', value='video_b').click()
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        self.browser.find_element(by='id', value='radio_dcr1').click()

        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Round 2 of 2' in self.browser.page_source)
        self.browser.find_element(by='id', value='video_a').click()
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        self.browser.find_element(by='id', value='video_b').click()
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        self.browser.find_element(by='id', value='radio_dcr4').click()

        self.assertEqual(Vote.objects.count(), 0)

        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Test done' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 4)
        self.assertEqual(FivePointVote.objects.first().score, 1)
        self.assertEqual(FivePointVote.objects.all()[1].score, 4)

        r1 = Round.objects.get(session=sess, round_id=0)
        r2 = Round.objects.get(session=sess, round_id=1)
        self.assertTrue(r1.response_sec > 0)
        self.assertTrue(r2.response_sec > 0)

    def test_step_session_dcr11d(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr11d.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        sleep(0.2)
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        sleep(0.2)
        self.browser.find_element(by='id', value='start').click()
        sleep(0.2)
        self.assertTrue('Round 1 of 2' in self.browser.page_source)
        sleep(0.2)
        self.browser.find_element(by='id', value='video_a').click()
        sleep(0.2)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.2)
        self.browser.find_element(by='id', value='video_b').click()
        sleep(0.2)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.2)
        self.browser.find_element(by='id', value='radio_dcr1').click()
        sleep(0.2)
        self.browser.find_element(by='id', value='submit').click()
        sleep(0.2)
        self.assertTrue('Round 2 of 2' in self.browser.page_source, f'page_source: {self.browser.page_source}')
        sleep(0.2)
        self.browser.find_element(by='id', value='video_a').click()
        sleep(0.2)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.2)
        self.browser.find_element(by='id', value='video_b').click()
        sleep(0.2)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.2)
        self.browser.find_element(by='id', value='radio_dcr4').click()
        sleep(0.2)

        self.assertEqual(Vote.objects.count(), 0)

        sleep(0.2)
        self.browser.find_element(by='id', value='submit').click()
        sleep(0.5)
        self.assertTrue('Test done' in self.browser.page_source, f'page_source: {self.browser.page_source}')

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(ElevenPointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 4)
        self.assertEqual(ElevenPointVote.objects.first().score, 1)
        self.assertEqual(ElevenPointVote.objects.all()[1].score, 4)

    def test_step_session_dcr7d_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_dcr7d_standard.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        self.browser.find_element(by='id', value='start').click()
        self.assertTrue('Round 1 of 2' in self.browser.page_source)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        self.browser.find_element(by='id', value='radio_dcr1').click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Round 2 of 2' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 0)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        self.browser.find_element(by='id', value='radio_dcr7').click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Test done' in self.browser.page_source)

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
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        sleep(0.2)
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        sleep(0.2)
        self.browser.find_element(by='id', value='start').click()
        sleep(0.2)
        self.assertTrue('Round 1 of 2' in self.browser.page_source)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        sleep(0.2)
        self.browser.find_element(by='id', value='radio_dcr1').click()
        sleep(0.2)
        self.browser.find_element(by='id', value='submit').click()
        sleep(0.2)
        self.assertTrue('Round 2 of 2' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 0)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.2)

        self.browser.find_element(by='id', value='radio_dcr4').click()
        sleep(0.2)
        self.browser.find_element(by='id', value='submit').click()
        sleep(0.2)
        self.assertTrue('Test done' in self.browser.page_source)

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
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        self.browser.find_element(by='id', value='start').click()
        self.assertTrue('Round 1 of 2' in self.browser.page_source)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        self.browser.find_element(by='id', value='radio_dcr1').click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Round 2 of 2' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 0)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        self.browser.find_element(by='id', value='radio_dcr3').click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Test done' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(ThreePointVote.objects.count(), 2)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)

        self.assertEqual(Vote.objects.first().score, 1)
        self.assertEqual(Vote.objects.all()[1].score, 3)
        self.assertEqual(ThreePointVote.objects.first().score, 1)
        self.assertEqual(ThreePointVote.objects.all()[1].score, 3)

    def test_step_session_tafc_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_tafc_standard.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        self.browser.find_element(by='id', value='start').click()
        self.assertTrue('Round 1 of 2' in self.browser.page_source)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        button = self.browser.find_element(by='id', value='radio_tafc0')
        value = int(button.get_attribute("value"))
        button.click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Round 2 of 2' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 0)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        button2 = self.browser.find_element(by='id', value='radio_tafc1')
        value2 = int(button2.get_attribute("value"))
        button2.click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Test done' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)
        self.assertEqual(TafcVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, value)
        self.assertEqual(Vote.objects.all()[1].score, value2)
        self.assertEqual(TafcVote.objects.first().score, value)
        self.assertEqual(TafcVote.objects.all()[1].score, value2)

    def test_step_session_samviq(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        sleep(0.1)
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        sleep(0.1)
        self.browser.find_element(by='id', value='start').click()
        sleep(0.1)
        self.assertTrue('Round 1 of 2' in self.browser.page_source)
        self.browser.find_element(by='id', value='video_ref').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_0').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_1').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)

        self.assertEqual(Vote.objects.count(), 0)

        self.browser.find_element(by='id', value='myRange_3').send_keys(Keys.RIGHT)
        sleep(0.1)
        self.browser.find_element(by='id', value='myRange_2').send_keys(Keys.RIGHT)
        sleep(0.1)

        self.browser.find_element(by='id', value='submit').click()
        sleep(0.1)

        self.assertEqual(Vote.objects.count(), 0)

        self.assertTrue('Round 2 of 2' in self.browser.page_source)
        self.browser.find_element(by='id', value='video_ref').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_0').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_1').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)

        self.assertEqual(Vote.objects.count(), 0)

        self.browser.find_element(by='id', value='submit').click()
        sleep(0.1)
        self.assertTrue('Test done' in self.browser.page_source, f'page_source: {self.browser.page_source}')

        self.assertEqual(Vote.objects.count(), 4)
        self.assertEqual(Vote.objects.all()[0].score, 51)
        self.assertEqual(Vote.objects.all()[1].score, 51)
        self.assertEqual(Vote.objects.all()[2].score, 50)
        self.assertEqual(Vote.objects.all()[3].score, 50)

        r1 = Round.objects.get(session=sess, round_id=0)
        r2 = Round.objects.get(session=sess, round_id=1)
        self.assertTrue(r1.response_sec > 0)
        self.assertTrue(r2.response_sec > 0)

    def test_step_session_samviq_with_preload(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_samviq_with_preload.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        sleep(0.1)
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        sleep(0.1)
        self.browser.find_element(by='id', value='start').click()
        self.assertTrue('Round 1 of 2' in self.browser.page_source)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_ref').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_0').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_1').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)

        self.assertEqual(Vote.objects.count(), 0)

        self.browser.find_element(by='id', value='myRange_3').send_keys(Keys.RIGHT)
        sleep(0.1)
        self.browser.find_element(by='id', value='myRange_2').send_keys(Keys.RIGHT)
        sleep(0.1)

        self.browser.find_element(by='id', value='submit').click()
        sleep(0.1)

        self.assertEqual(Vote.objects.count(), 0)

        self.assertTrue('Round 2 of 2' in self.browser.page_source)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_ref').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_0').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)
        self.browser.find_element(by='id', value='video_1').click()
        sleep(0.1)
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)
        sleep(0.1)

        self.assertEqual(Vote.objects.count(), 0)

        self.browser.find_element(by='id', value='submit').click()
        sleep(0.1)
        self.assertTrue('Test done' in self.browser.page_source, f'page_source: {self.browser.page_source}')

        self.assertEqual(Vote.objects.count(), 4)
        self.assertEqual(Vote.objects.all()[0].score, 51)
        self.assertEqual(Vote.objects.all()[1].score, 51)
        self.assertEqual(Vote.objects.all()[2].score, 50)
        self.assertEqual(Vote.objects.all()[3].score, 50)

        r1 = Round.objects.get(session=sess, round_id=0)
        r2 = Round.objects.get(session=sess, round_id=1)
        self.assertTrue(r1.response_sec > 0)
        self.assertTrue(r2.response_sec > 0)

    def test_step_session_ccr_standard(self):
        ec = ExperimentUtils._create_experiment_from_config(
            source_config_filepath=NestConfig.tests_resource_path('cvxhull_subjexp_toy_x_ccr_standard.json'),
            is_test=False,
            random_seed=1,
            experiment_title=self.EXPERIMENT_TITLE)

        subj: Subject = Subject.create_by_username('user')
        sess = ec.add_session(subj)

        self.login()
        self.browser.get(self.live_server_url + reverse('nest:start_session', kwargs={'session_id': sess.id}))
        self.browser.find_element(by='id', value='start').click()
        self.assertTrue('Round 1 of 2' in self.browser.page_source)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        button = self.browser.find_element(by='id', value='radio_ccr0')
        value = int(button.get_attribute("value"))
        button.click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Round 2 of 2' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 0)

        sleep(0.5)  # 0.5 sec buffer
        self.browser.find_element(by='tag name', value="body").send_keys(Keys.SPACE)

        button2 = self.browser.find_element(by='id', value='radio_ccr1')
        value2 = int(button2.get_attribute("value"))
        button2.click()
        self.browser.find_element(by='id', value='submit').click()
        self.assertTrue('Test done' in self.browser.page_source)

        self.assertEqual(Vote.objects.count(), 2)
        self.assertEqual(FivePointVote.objects.count(), 0)
        self.assertEqual(Zero2HundredVote.objects.count(), 0)
        self.assertEqual(CcrThreePointVote.objects.count(), 2)

        self.assertEqual(Vote.objects.first().score, value)
        self.assertEqual(Vote.objects.all()[1].score, value2)
        self.assertEqual(CcrThreePointVote.objects.first().score, value)
        self.assertEqual(CcrThreePointVote.objects.all()[1].score, value2)
