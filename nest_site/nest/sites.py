import json
import logging
import os
import random
import re
import string
import tempfile
from functools import update_wrapper
from time import time
from typing import Union, Optional

from django.apps import apps
from django.contrib.admin import AdminSite
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, re_path, reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic import RedirectView
try:
    from e2nestprivate.sites import NestSitePrivateMixin
except ImportError:
    from .helpers import DummyClass as NestSitePrivateMixin
from nest_site.settings import MEDIA_URL
from sureal.dataset_reader import DatasetReader

from .config import ExperimentConfig, NestConfig, StimulusConfig
from .helpers import override
from .pages import Acr5cPage, AcrPage, CcrPage, DcrPage, GenericPage, map_methodology_to_html_id_key, \
    map_methodology_to_page_class, Samviq5dPage, SamviqPage, StatusPage
logging.basicConfig()
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])
logger.setLevel('INFO')


class ExperimentMixin(object):

    @staticmethod
    def _is_test_environment(request):
        if 'SERVER_NAME' in request.environ and \
                request.environ['SERVER_NAME'] == 'testserver':
            is_test_env = True
        else:
            is_test_env = False
        return is_test_env

    @staticmethod
    def get_experiment_config_filepath(experiment_title, is_test):
        if is_test:
            config_filepath = NestConfig.tests_workdir_path(
                'media', 'experiment_config', f"{experiment_title}.json")
        else:
            config_filepath = NestConfig.media_path(
                'experiment_config', f"{experiment_title}.json")
        return config_filepath

    @classmethod
    def _load_experiment_config(cls, experiment_title: str, request):
        is_test = cls._is_test_environment(request)
        config = cls._load_experiment_config2(experiment_title, is_test)
        return config

    @classmethod
    def _load_experiment_config2(cls, experiment_title, is_test):
        config_filepath = cls.get_experiment_config_filepath(experiment_title,
                                                             is_test)
        with open(config_filepath, "rt") as fp:
            config = json.load(fp)
        return config

    def _get_experiment_controller(self, exp, request):
        config = self._load_experiment_config(exp.title, request)
        ec = self._get_experiment_controller2(exp, config)
        return ec

    @staticmethod
    def _get_experiment_controller2(exp, config):
        from .control import ExperimentController
        scfg = StimulusConfig(config['stimulus_config'])
        ecfg = ExperimentConfig(stimulus_config=scfg,
                                config=config['experiment_config'])
        ec = ExperimentController(experiment=exp, experiment_config=ecfg)
        return ec


class NestAdminSite(AdminSite, ExperimentMixin):
    site_title = gettext_lazy('e2nest admin')
    site_header = gettext_lazy('e2nest: Media Subjective Testing Admin')
    index_title = gettext_lazy('Site administration')

    @override(AdminSite)
    def get_urls(self):

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        urlpatterns = list()
        urlpatterns += [path('nestexp', wrap(self.nestexp), name='nestexp')]
        urlpatterns += [re_path(r'^nestexp/download_sureal/(?P<experiment_id>[0-9]+)$',
                                wrap(self.download_sureal), name='download_sureal')]
        urlpatterns += [re_path(r'^nestexp/download_sureal_alt/(?P<experiment_id>[0-9]+)$',
                                wrap(self.download_sureal_alt), name='download_sureal_alt')]
        urlpatterns += [re_path(r'^nestexp/download_nest/(?P<experiment_id>[0-9]+)$',
                                wrap(self.download_nest), name='download_nest')]
        urlpatterns += [re_path(r'^nestexp/download_nest_csv/(?P<experiment_id>[0-9]+)$',
                                wrap(self.download_nest_csv), name='download_nest_csv')]
        urlpatterns += super().get_urls()
        return urlpatterns

    @method_decorator(never_cache)
    def nestexp(self, request, extra_context=None):
        from .models import Experiment
        experiments = Experiment.objects.order_by('-id')
        context = {
            **self.each_context(request),
            'title': 'NEST experiments',
            'experiments': experiments,
            **(extra_context or {}),
        }
        request.current_app = self.name
        return TemplateResponse(request, self.index_template or 'admin/nestexp.html', context)

    @method_decorator(never_cache)
    def download_sureal(self, request, experiment_id):
        from .io import export_sureal_dataset
        from .models import Experiment
        experiment = Experiment.objects.get(id=experiment_id)
        dataset = export_sureal_dataset(experiment.title)
        with tempfile.NamedTemporaryFile(mode='r+t') as tf:
            DatasetReader.write_out_dataset(dataset, tf.name)
            if os.path.exists(tf.name):
                with open(tf.name, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="text/plain")
                    response['Content-Disposition'] = f'attachment; filename={experiment.title}.vote.py'
                    return response
            raise Http404

    @method_decorator(never_cache)
    def download_sureal_alt(self, request, experiment_id):
        from .io import export_sureal_dataset
        from .models import Experiment
        experiment = Experiment.objects.get(id=experiment_id)
        dataset = export_sureal_dataset(experiment.title, ignore_against=True)
        with tempfile.NamedTemporaryFile(mode='r+t') as tf:
            DatasetReader.write_out_dataset(dataset, tf.name)
            if os.path.exists(tf.name):
                with open(tf.name, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="text/plain")
                    response['Content-Disposition'] = f'attachment; filename={experiment.title}.vote.alt.py'
                    return response
            raise Http404

    @method_decorator(never_cache)
    def download_nest(self, request, experiment_id):
        from .models import Experiment
        experiment = Experiment.objects.get(id=experiment_id)
        ec = self._get_experiment_controller(experiment, request)
        einfo: dict = ec.get_experiment_info()
        with tempfile.NamedTemporaryFile(mode='r+t') as tf:
            with open(tf.name, 'wt') as f:
                json.dump(einfo, f, indent=2)
            if os.path.exists(tf.name):
                with open(tf.name, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/json")
                    response['Content-Disposition'] = f'attachment; filename={experiment.title}.vote.json'
                    return response
            raise Http404

    @method_decorator(never_cache)
    def download_nest_csv(self, request, experiment_id):
        import pandas as pd
        from .control import ExperimentController
        from .models import Experiment
        experiment = Experiment.objects.get(id=experiment_id)
        ec = self._get_experiment_controller(experiment, request)
        einfo: dict = ec.get_experiment_info()
        with tempfile.NamedTemporaryFile(mode='r+t') as tf:
            df: pd.DataFrame = ExperimentController.denormalize_experiment_info(einfo)
            df.to_csv(tf.name, index=False)
            if os.path.exists(tf.name):
                with open(tf.name, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="text/plain")
                    response['Content-Disposition'] = f'attachment; filename={experiment.title}.vote.csv'
                    return response
            raise Http404


class NestSite(ExperimentMixin, NestSitePrivateMixin):
    """
    An NestSite object encapsulates an instance of the Django nest application,
    ready to be hooked in to your URLconf.
    """

    # Text to put at the end of each page's <title>.
    site_title = gettext_lazy('e2nest')

    # Text to put in each page's <h1>.
    site_header = gettext_lazy('e2nest: Media Subjective Testing Platform')

    # Text to put at the top of the welcome page.
    index_title = gettext_lazy('e2nest')

    # URL for the "View site" link at the top of each page.
    site_url = '/'

    login_form = None
    login_template = None
    logout_template = None
    password_change_template = None
    password_change_done_template = None
    index_template = None

    def __init__(self, name='nest'):
        self.name = name

    @property
    def urls(self):
        return self.get_urls(), 'nest', self.name

    def has_permission(self, request):
        """
        Return True if the given HttpRequest has permission to view
        *at least one* page in the site.
        """
        return request.user.is_active

    def user_view(self, view, cacheable=False):
        """
        Decorator to create an user view attached to this site. This
        wraps the view and provides permission checking by calling
        ``self.has_permission``.

        By default, user_views are marked non-cacheable using the
        ``never_cache`` decorator. If the view can be safely cached, set
        cacheable=True.
        """
        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                if request.path == reverse('nest:logout', current_app=self.name):
                    index_path = reverse('nest:index', current_app=self.name)
                    return HttpResponseRedirect(index_path)
                # Inner import to prevent django.contrib.admin (app) from
                # importing django.contrib.auth.models.User (unrelated model).
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(
                    request.get_full_path(),
                    reverse('nest:login', current_app=self.name)
                )
            return view(request, *args, **kwargs)
        if not cacheable:
            inner = never_cache(inner)
        # We add csrf_protect here so this function can be used as a utility
        # function for any view, without having to repeat 'csrf_protect'.
        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    def get_urls(self):

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.user_view(view, cacheable)(*args, **kwargs)
            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        urlpatterns = [
            path('login/', self.login, name='login'),
            path('logout/', wrap(self.logout), name='logout'),
            path('password_change/',  wrap(self.password_change, cacheable=True), name='password_change'),
            path('password_change/done/', wrap(self.password_change_done, cacheable=True), name='password_change_done'),
            path('', RedirectView.as_view(url=reverse_lazy('nest:status'), permanent=False), name='index'),
            path('status/', wrap(self.status), name='status'),
            path('cookie/', wrap(self.cookie), name='cookie'),
            re_path(r'^session/(?P<session_id>\d+)/reset/$', wrap(self.reset_session), name='reset_session'),
            re_path(r'^session/(?P<session_id>\d+)/start/$', wrap(self.start_session), name='start_session'),
            re_path(r'^session/(?P<session_id>\d+)/step/$', wrap(self.step_session), name='step_session'),

            # temp:
            path('instruction_demo/', self.instruction_demo, name='instruction_demo'),
            path('acr_demo/', self.acr_demo, name='acr_demo'),
            path('acr5c_demo/', self.acr5c_demo, name='acr5c_demo'),
            path('acr5c_standard_demo/', self.acr5c_standard_demo, name='acr5c_standard_demo'),
            path('acr_standard_demo/', self.acr_standard_demo, name='acr_standard_demo'),
            path('dcr_demo/', self.dcr_demo, name='dcr_demo'),
            path('dcr_standard_demo/', self.dcr_standard_demo, name='dcr_standard_demo'),
            path('hdr_demo_meridian/', self.hdr_demo_meridian, name='hdr_demo_meridian'),
            path('hdr_demo_sollevante/', self.hdr_demo_sollevante, name='hdr_demo_sollevante'),
            path('hdr_demo_sparks/', self.hdr_demo_sparks, name='hdr_demo_sparks'),
            path('tafc_demo/', self.tafc_demo, name='tafc_demo'),
            path('tafc_standard_demo/', self.tafc_standard_demo, name='tafc_standard_demo'),
            path('ccr_demo/', self.ccr_demo, name='ccr_demo'),
            path('ccr_standard_demo/', self.ccr_standard_demo, name='ccr_standard_demo'),
            path('dcr7d_standard_demo/', self.dcr7d_standard_demo, name='dcr7d_standard_demo'),
            path('dcr11d_demo/', self.dcr11d_demo, name='dcr11d_demo'),
            path('dcr11d_standard_demo/', self.dcr11d_standard_demo, name='dcr11d_standard_demo'),
            path('samviq_demo/', self.samviq_demo, name='samviq_demo'),
            path('samviq5d_demo/', self.samviq5d_demo, name='samviq5d_demo')
        ]

        try:
            urlpatterns += self.get_urls_private()
        except AttributeError:
            pass

        return urlpatterns

    def each_context(self, request):
        """
        Return a dictionary of variables to put in the template context for
        *every* page in the site.

        For sites running on a subpath, use the SCRIPT_NAME value if site_url
        hasn't been customized.
        """
        script_name = request.META['SCRIPT_NAME']
        site_url = script_name if self.site_url == '/' and script_name else self.site_url
        return {
            'site_title': self.site_title,
            'site_header': self.site_header,
            'site_url': site_url,
            'has_permission': self.has_permission(request),
            'is_popup': False,
        }

    @method_decorator(never_cache)
    def login(self, request, extra_context=None):
        """
        Display the login form for the given HttpRequest.
        """
        if request.method == 'GET' and self.has_permission(request):
            # Already logged-in, redirect to welcome
            index_path = reverse('nest:index', current_app=self.name)
            return HttpResponseRedirect(index_path)

        from django.contrib.auth.views import LoginView
        # Since this module gets imported in the application's root package,
        # it cannot import models from other applications at the module level,
        # and django.contrib.admin.forms eventually imports User.
        from django.contrib.admin.forms import AuthenticationForm
        context = {
            **self.each_context(request),
            'title': 'Log in',
            'app_path': request.get_full_path(),
            'username': request.user.get_username(),
        }
        if (REDIRECT_FIELD_NAME not in request.GET and
                REDIRECT_FIELD_NAME not in request.POST):
            context[REDIRECT_FIELD_NAME] = reverse('nest:index', current_app=self.name)
        context.update(extra_context or {})

        defaults = {
            'extra_context': context,
            'authentication_form': self.login_form or AuthenticationForm,
            'template_name': self.login_template or 'admin/login.html',
        }
        request.current_app = self.name
        return LoginView.as_view(**defaults)(request)

    @method_decorator(never_cache)
    def logout(self, request, extra_context=None):
        """
        Log out the user for the given HttpRequest.

        This should *not* assume the user is already logged in.
        """
        defaults = {
            'extra_context': {
                **self.each_context(request),
                # Since the user isn't logged out at this point, the value of
                # has_permission must be overridden.
                'has_permission': False,
                **(extra_context or {})
            },
        }
        if self.logout_template is not None:
            defaults['template_name'] = self.logout_template
        request.current_app = self.name
        from .views import NestLogoutView
        response = NestLogoutView.as_view(**defaults)(request)

        # clear cookie when logging out
        self._clear_test_cookie(request)
        self._clear_session_cookie(request)

        return response

    @staticmethod
    def _set_test_cookie(request):
        request.session.set_test_cookie()

    @staticmethod
    def _test_cookie_worked(request):
        return request.session.test_cookie_worked()

    @staticmethod
    def _clear_test_cookie(request):
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

    @staticmethod
    def _get_session_steps_from_cookie(request):
        return request.session.setdefault('steps', [])

    @staticmethod
    def _get_session_id_from_cookie(request):
        return request.session.setdefault('session_id', None)

    @staticmethod
    def _set_session_cookie(request, val):
        assert isinstance(val, dict) and 'steps' in val and 'session_id' in val
        request.session['steps'] = val['steps']
        request.session['session_id'] = val['session_id']

    @staticmethod
    def _get_round_response_sec_from_cookie(request, round_ID: int) -> Union[float, None]:
        return request.session.setdefault('round_response_sec', dict()).setdefault(str(round_ID), None)

    @staticmethod
    def _set_round_response_sec_in_cookie(request, round_ID: int, round_response_sec: float):
        request.session.setdefault('round_response_sec', dict())[str(round_ID)] = round_response_sec
        # since modification is not directly on session, but on dict of dict,
        # need to explicitly tell the session has been modified:
        request.session.modified = True

    @staticmethod
    def _clear_session_cookie(request):
        if 'session_id' in request.session:
            del request.session['session_id']
        if 'steps' in request.session:
            del request.session['steps']
        if 'round_response_sec' in request.session:
            del request.session['round_response_sec']

    def password_change(self, request, extra_context=None):
        """
        Handle the "change password" task -- both form display and validation.
        """
        from django.contrib.admin.forms import AdminPasswordChangeForm
        from .views import NestPasswordChangeView
        url = reverse('nest:password_change_done', current_app=self.name)
        defaults = {
            'form_class': AdminPasswordChangeForm,
            'success_url': url,
            'extra_context': {**self.each_context(request), **(extra_context or {})},
        }
        if self.password_change_template is not None:
            defaults['template_name'] = self.password_change_template
        request.current_app = self.name
        return NestPasswordChangeView.as_view(**defaults)(request)

    def password_change_done(self, request, extra_context=None):
        """
        Display the "success" page after a password change.
        """
        from .views import NestPasswordChangeDoneView
        defaults = {
            'extra_context': {**self.each_context(request), **(extra_context or {})},
        }
        if self.password_change_done_template is not None:
            defaults['template_name'] = self.password_change_done_template
        request.current_app = self.name
        return NestPasswordChangeDoneView.as_view(**defaults)(request)

    @method_decorator(never_cache)
    def status(self, request, extra_context=None):
        from .control import SessionStatus
        from .models import Experiment, Session, Subject

        username: str = request.user.get_username()

        subj: Subject = Subject.find_by_username(username)
        tests = []
        for session in Session.objects.filter(subject=subj):
            exp: Experiment = session.experiment
            ec = self._get_experiment_controller(exp, request)
            ss = ec.get_session_status(session)
            extra = {}
            if ss == SessionStatus.UNINITIALIZED:
                status = 'Uninitialized'
                action = None
            elif ss == SessionStatus.PARTIALLY_INITIALIZED:
                status = 'Partially initialized'
                action = None
            elif ss == SessionStatus.INITIALIZED:
                session_id_from_cookie = self._get_session_id_from_cookie(request)
                steps_performed = self._get_session_steps_from_cookie(request)
                if session_id_from_cookie == session.id and len(steps_performed) > 0:
                    # This would allow a session to be cached and resumed, even
                    # after a user goes back to the main page. The session will
                    # only gets cleaned if 1) user logs out, or 2) user starts
                    # another session.
                    status = 'In progress'
                    action = 'Continue'
                    extra['action_url'] = \
                        reverse('nest:step_session', kwargs={"session_id": session.id})
                else:
                    status = 'New'
                    action = 'Start'
                    extra['action_url'] = \
                        reverse('nest:start_session', kwargs={"session_id": session.id})
            elif ss == SessionStatus.PARTIALLY_FINISHED:
                status = 'Unfinished'
                action = 'Reset'
                extra['action_url'] = \
                    reverse('nest:reset_session', kwargs={"session_id": session.id})
            elif ss == SessionStatus.FINISHED:
                status = 'Done'
                action = None
            else:
                assert False, F"unknown status: {ss}"
            tests.append({
                'title': exp.title,
                'session': session.id,
                'status': status,
                'action': action,
                **extra,
            })

        page = StatusPage({
            'title': f"Welcome, {username}!",
            'tests': tests
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name

        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def cookie(self, request, extra_context=None):
        session_id_from_cookie = self._get_session_id_from_cookie(request)
        steps_performed = self._get_session_steps_from_cookie(request)
        title = 'Cookie status'
        proceed_url = reverse('nest:status')
        cookie_json = json.dumps({
            'session_id': session_id_from_cookie,
            'steps_performed': steps_performed
        }, indent=4)
        text_html = f"""<p> {cookie_json} </p>"""
        actions_html = f""" <p> <a class="button" href="{proceed_url}"  id="start">Main page</a> </p>"""
        script_html = \
            """
            function press_submit() {
                document.getElementById("start").click();
            }
            document.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                    press_submit();
                }
            });
            """
        page = GenericPage({'title': title, 'text_html': text_html, 'actions_html': actions_html, 'script_html': script_html})
        context = {**self.each_context(request), **page.context}
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def instruction_demo(self, request, extra_context=None):
        title = 'Instruction'

        text_html = ""
        text_html += """ <p> In this session, you will be asked to evaluate the annoyance caused by presence of banding artifact in a set of videos. </p> """  # noqa E501
        text_html += """ <p> If you don't know what banding artifacts are, it would be good idea to contact the author <b>ptandon@catflix.com</b> before proceeding with the test. </p> """  # noqa E501
        text_html += """ <p> There are two phases, a training and a testing phase. In the training, you will see 6 videos and will be asked to rate the presence of banding artifacts. The videos are chosen to span the scale and there is an expected score for each of the video to provide an anchor for the testing videos. </p> """  # noqa E501
        text_html += """ <p> Next, the testing phase will start and at this point, your scores will be recorded.</b> </p> """  # noqa E501
        text_html += """ <p> To play a video, click on the <b>"Play Video"</b> button. </p> """  # noqa E501
        text_html += """ <p> <b style='color:red !important;'>Please, maintain the viewing distance of approximately 1.5 times the monitor height.</b> </p> """  # noqa E501
        text_html += """ <p> Video clips will loop over, <b>press "space" key or double click mouse </b> to terminate the video. A slider will appear and you will be able to rate annoyance caused by the presence of banding in the video on the 0-100 scale, qualitatively from unwatchable to imperceptible. Please try to focus only on the banding artifacts. For all clips rate the worst case banding seen during video playback, even for videos with multiple scenes. </p>  """  # noqa E501
        text_html += """ <p> Once you have scored the video, click the "Next" button to fetch next video and repeat. </p> """  # noqa E501
        text_html += """ <p> Progress is shown for training and testing cases on top, near instructions. </p> """  # noqa E501

        actions_html = \
            f"""
            <p>
                <a class="button" href="{reverse_lazy('nest:instruction_demo')}"  id="start">Start Evaluation</a>
            </p>
            """
        script_html = \
            """
            function press_submit() {
                document.getElementById("start").click();
            }
            document.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                    press_submit();
                }
            });
            """
        page = GenericPage({
            'title': title,
            'text_html': text_html,
            'actions_html': actions_html,
            'script_html': script_html,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def acr_demo(self, request, extra_context=None):
        page = AcrPage({
            'title': "Round 1 of 10",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_display_percentage': 75,
            'video_show_controls': True,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def acr5c_demo(self, request, extra_context=None):
        page = Acr5cPage({
            'title': "Round 1 of 10",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"), # noqa E501
            'video_display_percentage': 100,
            'stimulusvotegroup_id': 0,
            'video_show_controls': True,
            'start_seconds': 3,
            'end_seconds': 3.5,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def acr5c_standard_demo(self, request, extra_context=None):
        page = Acr5cPage({
            'title': "Round 1 of 10",
            'instruction_html': """ <p> Rate the video by answering the question below. </p>""",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"), # noqa E501
            'template_version': 'standard',
            't_gray': 2000,
            'num_plays': 2, 'min_num_plays': 0,
            'button': 'Watch the video',
            'video_show_controls': False,
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def acr_standard_demo(self, request, extra_context=None):
        page = AcrPage({
            'title': "Round 1 of 10",
            'instruction_html': """ <p> Rate the video by answering the question below. </p>""",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"), # noqa E501
            'template_version': 'standard',
            't_gray': 500,
            'num_plays': 100, 'min_num_plays': 0,
            'button': '<message that I can customize>',
            'video_show_controls': False,
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
            "text_color": "#0000FF",
            "text_fontsize": "50px",
            "overlay_on_video_js": """
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas

        // Define the rectangle size and position in percentage
        const rectWidthPercent = 20; // 20% of the canvas width
        const rectHeightPercent = 20; // 20% of the canvas height
        const rectXPercent = 80; // 80% of the canvas width for the upper right corner
        const rectYPercent = 0; // 0% of the canvas height for the upper right corner

        // Calculate the actual size and position
        const rectWidth = (rectWidthPercent / 100) * canvas.width;
        const rectHeight = (rectHeightPercent / 100) * canvas.height;
        const rectX = (rectXPercent / 100) * canvas.width;
        const rectY = (rectYPercent / 100) * canvas.height;

        // Draw the rectangle
        ctx.fillStyle = 'rgba(20, 20, 20, 0.95)';
        ctx.fillRect(rectX, rectY, rectWidth, rectHeight);

        // Calculate the center of the rectangle for the text
        const text = 'LIVE';
        const fontSize = 40
        ctx.font = fontSize + 'px Arial'; // Font size and family
        ctx.fillStyle = 'white'; // Text color
        const textWidth = ctx.measureText(text).width;
        const textHeight = ctx.measureText(text).height;
        const textX = rectX + (rectWidth - textWidth) / 2;
        const textY = rectY + (rectHeight + fontSize) / 2;

        // Draw the text
        ctx.fillText(text, textX, textY);
            """
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def dcr_demo(self, request, extra_context=None):
        page = DcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def dcr_standard_demo(self, request, extra_context=None):
        page = DcrPage({
            'title': 'Round 1 of 10',
            'instruction_html': """ <p> Rate the videos by answering the question below. </p>""",
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'template_version': "standard",
            'num_plays': 2, 'min_num_plays': 0,
            't_gray': 1000,
            'video_show_controls': True,
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def hdr_demo_meridian(self, request, extra_context=None):
        page = SamviqPage({
            'title': 'Round 1 of 10',
            'video_ref': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"), # noqa E501
            'button_ref': 'Reference',
            'videos': [os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__Dovi5Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf107.81_phonevmaf106.05_psnr24.30_kbps6441.59.m3u8"), # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__Hdr10Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf93.88_phonevmaf101.62_psnr42.45_kbps6509.97.mp4"), # noqa E501
                       ],
            'buttons': ['A', 'B'],
            'stimulusvotegroup_ids': [0, 1],
            'video_display_percentage': 100,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def hdr_demo_sollevante(self, request, extra_context=None):
        page = SamviqPage({
            'title': 'Round 1 of 10',
            'video_ref': os.path.join(MEDIA_URL, "mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf85.63_phonevmaf95.85_psnr26.99_kbps7275.37.mp4"), # noqa E501
            'button_ref': 'Reference',
            'videos': [os.path.join(MEDIA_URL, "mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__Dovi5Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf97.35_phonevmaf102.00_psnr18.69_kbps6954.28.m3u8"), # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/SolLevante/SolLevante10k_B__0_7_0_12__Hdr10Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf84.91_phonevmaf97.04_psnr37.76_kbps6894.95.mp4"), # noqa E501
                       ],
            'buttons': ['A', 'B'],
            'stimulusvotegroup_ids': [0, 1],
            'video_display_percentage': 100,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def hdr_demo_sparks(self, request, extra_context=None):
        page = SamviqPage({
            'title': 'Round 1 of 10',
            'video_ref': os.path.join(MEDIA_URL, "mp4/samples/Sparks/Sparks_A__2_0_2_5__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf84.08_phonevmaf96.96_psnr35.37_kbps6075.91.mp4"), # noqa E501
            'button_ref': 'Reference',
            'videos': [os.path.join(MEDIA_URL, "mp4/samples/Sparks/Sparks_A__2_0_2_5__Dovi5Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf96.18_phonevmaf102.44_psnr22.73_kbps6206.91.m3u8"), # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Sparks/Sparks_A__2_0_2_5__Hdr10Vvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf83.87_phonevmaf96.84_psnr37.11_kbps6081.28.mp4"), # noqa E501
                       ],
            'buttons': ['A', 'B'],
            'stimulusvotegroup_ids': [0, 1],
            'video_display_percentage': 100,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def tafc_demo(self, request, extra_context=None):
        from .models import TafcVote
        page = CcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_a_to_b_values': TafcVote.support,
            'question': 'Between Video A and Video B, which video has the better visual quality?',
            'choices':
                ['Video A is better',
                 'Video B is better'],
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def tafc_standard_demo(self, request, extra_context=None):
        from .models import TafcVote
        page = CcrPage({
            'title': 'Round 1 of 10',
            'instruction_html': "",
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_a_to_b_values': TafcVote.support,
            'question': 'Between Video A and Video B, which video has the better visual quality?',
            'choices':
                ['Video A is better',
                 'Video B is better'],
            'template_version': 'standard',
            'num_plays': 2, 'min_num_plays': 0,
            't_gray': 1000, 'text_color': '#FFFFFF',
            'text_vert_perc': 45,  # text vertical position percentage
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def ccr_demo(self, request, extra_context=None):
        from .models import CcrThreePointVote
        page = CcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_a_to_b_values': CcrThreePointVote.support,
            'video_display_percentage': 75,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def ccr_standard_demo(self, request, extra_context=None):
        from .models import CcrThreePointVote
        page = CcrPage({
            'title': 'Round 1 of 10',
            'instruction_html': "",
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_a_to_b_values': CcrThreePointVote.support,
            'template_version': 'standard',
            'num_plays': 2, 'min_num_plays': 0,
            't_gray': 1000, 'text_color': '#FFFFFF',
            'text_vert_perc': 45,  # text vertical position percentage
            'video_display_percentage': 100,
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def dcr11d_demo(self, request, extra_context=None):
        page = DcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_display_percentage': 75,
            'choices':
                ['11 - Imperceptible',
                 '10 - Slightly perceptible somewhere',
                 '9 - Slightly perceptible everywhere',
                 '8 - Perceptible somewhere',
                 '7 - Perceptible everywhere',
                 '6 - Clearly perceptible somewhere',
                 '5 - Clearly perceptible everywhere',
                 '4 - Annoying somewhere',
                 '3 - Annoying everywhere',
                 '2 - Severely annoying somewhere',
                 '1 - Severely annoying everywhere'],
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def dcr7d_standard_demo(self, request, extra_context=None):
        page = DcrPage({
            'title': 'Round 1 of 10',
            'instruction_html': """ <p> Rate the videos by answering the question below. </p>""",
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'template_version': "standard",
            'num_plays': 2, 'min_num_plays': 0,
            't_gray': 1000,
            'video_show_controls': True,
            'video_display_percentage': 75,
            'choices':
                ['7 - Imperceptible',
                 '6 - Slightly perceptible',
                 '5 - Perceptible',
                 '4 - Clearly perceptible',
                 '3 - Annoying',
                 '2 - Severely annoying',
                 '1 - Unwatchable'],
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def dcr11d_standard_demo(self, request, extra_context=None):
        page = DcrPage({
            'title': 'Round 1 of 10',
            'instruction_html': """ <p> Rate the videos by answering the question below. </p>""",
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'template_version': "standard",
            'num_plays': 2, 'min_num_plays': 0,
            't_gray': 1000,
            'video_show_controls': True,
            'video_display_percentage': 75,
            'choices':
                ['11 - Imperceptible',
                 '10 - Slightly perceptible somewhere',
                 '9 - Slightly perceptible everywhere',
                 '8 - Perceptible somewhere',
                 '7 - Perceptible everywhere',
                 '6 - Clearly perceptible somewhere',
                 '5 - Clearly perceptible everywhere',
                 '4 - Annoying somewhere',
                 '3 - Annoying everywhere',
                 '2 - Severely annoying somewhere',
                 '1 - Severely annoying everywhere'],
            'stimulusvotegroup_id': 0,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def samviq5d_demo(self, request, extra_context=None):
        page = Samviq5dPage({
            'title': 'Round 1 of 10',
            'video_ref': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'button_ref': 'Reference',
            'videos': [os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
                       ],
            'buttons': ['A', 'B', 'C', 'D'],
            'stimulusvotegroup_ids': [0, 1, 2, 3],
            'video_display_percentage': 75,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    @method_decorator(never_cache)
    def samviq_demo(self, request, extra_context=None):
        page = SamviqPage({
            'title': 'Round 1 of 10',
            'video_ref': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"), # noqa E501
            'button_ref': 'Reference',
            'videos': [os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"), # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"), # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"), # noqa E501
                       os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"), # noqa E501
                       ],
            'buttons': ['A', 'B', 'C', 'D'],
            'stimulusvotegroup_ids': [0, 1, 2, 3],
            'video_display_percentage': 75,
        })
        context = {
            **self.each_context(request),
            **page.context,
        }
        request.current_app = self.name
        return TemplateResponse(request, page.get_template(), context)

    def reset_session(self, request, session_id, extra_context=None):
        from .models import Experiment, Session
        session_id = int(session_id)
        session: Session = Session.objects.get(id=session_id)
        exp: Experiment = session.experiment
        ec = self._get_experiment_controller(exp, request)
        ec.reset_session(session)
        return HttpResponseRedirect(reverse('nest:status'))

    def start_session(self, request, session_id, extra_context=None):
        self._verify_subject(request, session_id)
        self._set_test_cookie(request)
        response = HttpResponseRedirect(
            reverse("nest:step_session", kwargs={'session_id': session_id}))
        self._clear_session_cookie(request)
        return response

    @staticmethod
    def _verify_subject(request, session_id):
        from .models import Session
        sess: Session = Session.objects.get(id=session_id)
        assert request.user.get_username() == sess.subject.user.username, \
            "expect subject with username {} for session {} but got username {}".format(
                sess.subject.user.username, session_id,
                request.user.get_username())

    def step_session(self, request, session_id, extra_context=None):  # noqa C901

        if not self._test_cookie_worked(request):
            title = 'Cookie disabled'
            proceed_url = reverse('nest:status')
            text_html = """ <p> To start the test, you must first enable cookie in your browser. </p> """  # noqa E501
            actions_html = f""" <p> <a class="button" href="{proceed_url}"  id="start">Back to Main Page</a> </p> """  # noqa E501
            script_html = \
                """
                function press_submit() {
                    document.getElementById("start").click();
                }
                document.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                        press_submit();
                    }
                });
                """
            page = GenericPage({'title': title, 'text_html': text_html, 'actions_html': actions_html, 'script_html': script_html})  # noqa E501
            context = {**self.each_context(request), **page.context}
            request.current_app = self.name
            return TemplateResponse(request, page.get_template(), context)

        self._verify_subject(request, session_id)

        from .control import ExperimentController, SessionStatus
        from .models import Experiment, Session
        from .models import Round, StimulusGroup, StimulusVoteGroup, Vote
        session_id = int(session_id)
        session: Session = Session.objects.get(id=session_id)
        exp: Experiment = session.experiment
        ec: ExperimentController = self._get_experiment_controller(exp, request)

        VoteClass = Vote.find_subclass(ec.experiment_config.vote_scale)

        # only check session status (expensive) when GET
        if request.method == 'GET':

            start_time = time()
            ss: SessionStatus = ec.get_session_status(session)
            logger.info(f'get_session_status for session {session.id} took {time() - start_time} sec')
            if ss == SessionStatus.FINISHED:

                title = 'Session has already been completed'
                proceed_url = reverse('nest:status')
                text_html = """ <p> You have already completely this session ({}, ID {}). </p> """. \
                    format(session.experiment.title, session_id)
                actions_html = f""" <p> <a class="button" href="{proceed_url}"  id="start">Main page</a> </p>"""
                script_html = \
                    """
                    function press_submit() {
                        document.getElementById("start").click();
                    }
                    document.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") {
                            press_submit();
                        }
                    });
                    """
                page = GenericPage({'title': title, 'text_html': text_html, 'actions_html': actions_html, 'script_html': script_html})  # noqa E501
                context = {**self.each_context(request), **page.context}
                request.current_app = self.name
                return TemplateResponse(request, page.get_template(), context)

            else:
                assert ss in [SessionStatus.INITIALIZED,
                              SessionStatus.PARTIALLY_FINISHED]

            assert ss == SessionStatus.INITIALIZED, \
                "expect session {} status {}, but got: {}".format(
                    session, SessionStatus.INITIALIZED, ss)

        # figure out what's the next step, by comparing the steps_planned
        # obtained from the ec, and the steps_performed that is stored in the
        # cookie
        session_id_from_cookie = self._get_session_id_from_cookie(request)
        if session_id_from_cookie is not None:
            assert session_id_from_cookie == session_id
        steps_performed = self._get_session_steps_from_cookie(request)
        steps_planned = ec.get_session_steps(session)

        # do some basic sanity check
        assert len(steps_performed) <= len(steps_planned)
        for sperf, splan in zip(steps_performed, steps_planned):
            assert 'position' in sperf and 'position' in splan
            assert 'round_id' in sperf['position'] and 'round_id' in splan['position']
            assert sperf['position']['round_id'] == splan['position']['round_id']
            if self._step_is_addition(sperf):
                assert self._step_is_addition(splan)
                assert sperf['position']['before_or_after'] == \
                       splan['position']['before_or_after']
                assert 'context' in splan or 'super_stimulusgroup_context_list' in splan
                if 'context' in splan:
                    assert 'title' in splan['context']
                    assert 'text_html' in splan['context']
                    assert 'actions_html' in splan['context']
                elif 'super_stimulusgroup_context_list' in splan:
                    for context in splan['super_stimulusgroup_context_list']:
                        assert 'title' in context
                        assert 'text_html' in context
                        assert 'actions_html' in context
                else:
                    assert False
            else:
                assert 'context' in splan
                if 'stimulusgroup_id' in splan['context']:
                    assert 'context' in sperf and 'stimulusgroup_id' in sperf['context']
                    assert sperf['context']['stimulusgroup_id'] == \
                           splan['context']['stimulusgroup_id']
            # title, text_html, actions_html are ignored when step is addition

        if len(steps_performed) == len(steps_planned):
            # have done all steps. next:
            # 1) record results in db (by creating votes of round and svg, update round with response_sec)
            # 2) delete cookie
            # 3) display done page

            for step in steps_performed:
                if self._step_is_addition(step):
                    continue
                assert 'context' in step
                assert 'score' in step['context']
                assert 'response_sec' in step['context']
                rnd: Round = Round.objects.get(
                    session=session, round_id=step['position']['round_id'])

                if (ec.experiment_config.methodology == 'acr5c' and ec.experiment_config.vote_scale == '0_TO_100') or \
                        (ec.experiment_config.methodology in ['acr', 'dcr'] and
                         ec.experiment_config.vote_scale in [
                             'THREE_POINT',
                             'FIVE_POINT',
                             'SEVEN_POINT',
                             'ELEVEN_POINT'
                         ]) or \
                        (ec.experiment_config.methodology == 'tafc' and
                         ec.experiment_config.vote_scale == '2AFC') or \
                        (ec.experiment_config.methodology == 'ccr' and
                         ec.experiment_config.vote_scale in ['CCR_THREE_POINT', 'CCR_FIVE_POINT']) or \
                        (ec.experiment_config.methodology == 'samviq' and
                         ec.experiment_config.vote_scale == '0_TO_100') or \
                        (ec.experiment_config.methodology == 'samviq5d' and
                         ec.experiment_config.vote_scale == 'FIVE_POINT'):
                    sg: StimulusGroup = StimulusGroup.objects.get(
                        experiment=exp,
                        stimulusgroup_id=step['context']['stimulusgroup_id'])
                    score_dict = step['context']['score']
                    assert isinstance(score_dict, dict)
                    for svgid, score in score_dict.items():
                        assert isinstance(score, int)
                        svg: StimulusVoteGroup = StimulusVoteGroup.objects.get(
                            stimulusgroup=sg, stimulusvotegroup_id=svgid)

                        # in each round, for a single svg, there can only be one
                        # vote; if more than one, it could be a duplicated submission
                        try:
                            vote2: VoteClass = VoteClass.objects.get(
                                round=rnd, stimulusvotegroup=svg)
                            if vote2.score == score:
                                msg = f'skip saving vote {score} as vote with ' \
                                      f'score {vote2.score} and svg {svg} already ' \
                                      f'exists in round {rnd}, possibly a double ' \
                                      f'POST submission.'
                                logger.warning(msg)
                                continue
                            else:
                                msg = f'error saving vote {score} as vote with ' \
                                      f'score {vote2.score} and svg {svg} already ' \
                                      f'exists in round {rnd}.'
                                logger.error(msg)
                                raise AssertionError(msg)
                        except VoteClass.DoesNotExist:
                            pass

                        vote: VoteClass = VoteClass(score=score,
                                                    round=rnd,
                                                    stimulusvotegroup=svg)
                        vote.save()
                else:
                    assert False, 'The combination of {m} methodology with {s} vote_scale is undefined'.format(
                        m=ec.experiment_config.methodology, s=ec.experiment_config.vote_scale)

                response_sec = step['context']['response_sec']
                assert response_sec != 'none'
                rnd.response_sec = response_sec
                rnd.save()

            title = 'Test done'
            proceed_url = reverse('nest:status')
            if 'text_html' in ec.experiment_config.done_context:
                text_html = ec.experiment_config.done_context['text_html']
            else:
                text_html = """ <p> You have completed the test. </p> """
            actions_html = f""" <p> <a class="button" href="{proceed_url}"  id="start">Done</a> </p>"""
            script_html = \
                """
                function press_submit() {
                    document.getElementById("start").click();
                }
                document.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                        press_submit();
                    }
                });
                """
            page = GenericPage({'title': title, 'text_html': text_html, 'actions_html': actions_html, 'script_html': script_html})  # noqa E501
            context = {**self.each_context(request), **page.context}
            request.current_app = self.name
            response = TemplateResponse(request, page.get_template(), context)

            self._clear_test_cookie(request)
            self._clear_session_cookie(request)

            return response

        next_step = steps_planned[len(steps_performed)]
        step_is_addition = self._step_is_addition(next_step)
        if step_is_addition:

            if 'context' in next_step:
                context = next_step['context']
            elif 'super_stimulusgroup_context_list' in next_step:
                # find out which one to use, depending on the step assoicated with this additional step
                if next_step['position']['before_or_after'] == 'before':
                    associated_step = steps_planned[len(steps_performed) + 1]  # associated step is the next one
                else:
                    associated_step = steps_planned[len(steps_performed) - 1]  # associated step is the previous one
                assert not self._step_is_addition(associated_step)
                stimulusgroup_id = associated_step['context']['stimulusgroup_id']
                stimulusgroup = ec.experiment_config.stimulus_config.stimulusgroups[stimulusgroup_id]
                assert 'super_stimulusgroup_id' in stimulusgroup
                context = next_step['super_stimulusgroup_context_list'][stimulusgroup['super_stimulusgroup_id']]
            else:
                assert False

            action_html_template = context['actions_html']
            script_html_template = context['script_html'] if 'script_html' in context else None

            assert '{action_url}' in action_html_template
            action_html = action_html_template.format(
                action_url=reverse("nest:step_session", kwargs={'session_id': session_id}))
            page_input = {'title': context['title'],
                          'text_html': context['text_html'],
                          'actions_html': action_html}
            if script_html_template is not None:
                page_input['script_html'] = script_html_template
            page = GenericPage(page_input)
            context = {**self.each_context(request), **page.context}
            request.current_app = self.name
            response = TemplateResponse(request, page.get_template(), context)

            # avoid context (title...) in cookie
            if 'context' in next_step:
                del next_step['context']
            elif 'super_stimulusgroup_context_list' in next_step:
                del next_step['super_stimulusgroup_context_list']
            else:
                assert False

            self._set_session_cookie(request, {
                'steps': steps_performed + [next_step],
                'session_id': session_id})

        else:  # step is actual round

            if request.method == 'GET':

                training_round_ids = ec.experiment_config.training_round_ids
                if next_step['position']['round_id'] in training_round_ids:
                    title = "Training {} of {}".format(
                        next_step['position']['round_id'] + 1,
                        len(training_round_ids))
                else:
                    title = "Round {} of {}".format(
                        next_step['position']['round_id'] + 1 - len(training_round_ids),
                        ec.experiment_config.rounds_per_session - len(training_round_ids))

                round_start_sec: float = time()
                rnd: Round = Round.objects.get(
                    session=session, round_id=next_step['position']['round_id'])
                round_start_sec_in_cookie = self._get_round_response_sec_from_cookie(request, rnd.id)
                if round_start_sec_in_cookie is not None:
                    logger.warning(f'round_start_sec {round_start_sec_in_cookie} for round {rnd.id} '
                                   f'in cookie exists, override with {round_start_sec}')
                self._set_round_response_sec_in_cookie(request, rnd.id, round_start_sec)

                if (ec.experiment_config.methodology in ['acr', 'dcr']
                        and ec.experiment_config.vote_scale in [
                            'THREE_POINT',
                            'FIVE_POINT',
                            'SEVEN_POINT',
                            'ELEVEN_POINT',
                        ]) or (ec.experiment_config.methodology == 'acr5c' and
                               ec.experiment_config.vote_scale == '0_TO_100'):

                    PageClass = map_methodology_to_page_class(
                        ec.experiment_config.methodology)
                    sgid: int = next_step['context']['stimulusgroup_id']
                    video_display_percentage = ec.experiment_config. \
                        stimulus_config.get_video_display_percentage(sgid)
                    pre_message: str = ec.experiment_config. \
                        stimulus_config.get_pre_message(sgid)
                    start_end_seconds: Optional[tuple[int, int]] = \
                        ec.experiment_config.stimulus_config.get_start_end_seconds(sgid)
                    text_color: str = ec.experiment_config. \
                        stimulus_config.get_text_color(sgid)
                    overlay_on_video_js: str = ec.experiment_config. \
                        stimulus_config.get_overlay_on_video_js(sgid)
                    assert video_display_percentage is not None

                    svgid = self._get_matched_single_stimulusvotegroup_id(ec, next_step)

                    d = {'title': title,
                         'session_id': session_id,
                         'video_display_percentage': video_display_percentage,
                         'stimulusvotegroup_id': svgid,
                         **ec.experiment_config.round_context,
                         }

                    if ec.experiment_config.methodology == 'acr5c':
                        if start_end_seconds is not None:
                            d['start_seconds'], d['end_seconds'] = start_end_seconds

                    # add special logic to acr only: customize the button text
                    # through stimulus_config.get_pre_message. For acr standard
                    # mode, this will be displayed as banner before the video is
                    # played.
                    if ec.experiment_config.methodology == 'acr':
                        if pre_message is not None:
                            if 'template_version' in ec.experiment_config.round_context and ec.experiment_config.round_context['template_version'] == 'standard':  # noqa E501
                                d['button'] = pre_message
                                if text_color is not None:
                                    # `text_color` could appear in round_context, but
                                    # it can be overriden here.
                                    d['text_color'] = text_color
                                if overlay_on_video_js is not None:
                                    d['overlay_on_video_js'] = overlay_on_video_js
                            else:
                                if text_color is not None:
                                    d['instruction_html'] += f"<p> <b><font color='{text_color}'>{pre_message}</font></b> </p>"  # enrich the instruction_html in round_context  # noqa E501
                                else:
                                    d['instruction_html'] += f"<p> <b>{pre_message}</b> </p>"  # enrich the instruction_html in round_context  # noqa E501

                    if ec.experiment_config.methodology.startswith('acr'):
                        sid = self._get_matched_single_stimulus_id(ec, svgid)
                        s = self._get_matched_stimulus_dict(ec, sid)
                        assert s['type'] == 'video/mp4'
                        d['video'] = s['path']

                    elif ec.experiment_config.methodology == 'dcr':
                        dis_sid, ref_sid = self._get_matched_double_stimulus_ids(ec, svgid)
                        dis_s = self._get_matched_stimulus_dict(ec, dis_sid)
                        ref_s = self._get_matched_stimulus_dict(ec, ref_sid)
                        assert dis_s['type'] == 'video/mp4'
                        assert ref_s['type'] == 'video/mp4'
                        d['video_a'] = ref_s['path']
                        d['video_b'] = dis_s['path']

                    else:
                        assert False

                    if ec.experiment_config.vote_scale == 'THREE_POINT':
                        # only if choices not yet overridden by round_context:
                        if 'choices' not in d:
                            d['choices'] = \
                                ["Indistinguishable",
                                 "Distinguishable but acceptable as premium quality",
                                 "Not acceptable as premium quality",
                                 ]
                    elif ec.experiment_config.vote_scale in ['FIVE_POINT', '0_TO_100']:
                        pass
                    elif ec.experiment_config.vote_scale == 'SEVEN_POINT':
                        # only if choices not yet overridden by round_context:
                        if 'choices' not in d:
                            d['choices'] = \
                                ['7 - Imperceptible',
                                 '6 - Slightly perceptible',
                                 '5 - Perceptible',
                                 '4 - Clearly perceptible',
                                 '3 - Annoying',
                                 '2 - Severely annoying',
                                 '1 - Unwatchable']
                    elif ec.experiment_config.vote_scale == 'ELEVEN_POINT':
                        # only if choices not yet overridden by round_context:
                        if 'choices' not in d:
                            d['choices'] = \
                                ['11 - Imperceptible',
                                 '10 - Slightly perceptible somewhere',
                                 '9 - Slightly perceptible everywhere',
                                 '8 - Perceptible somewhere',
                                 '7 - Perceptible everywhere',
                                 '6 - Clearly perceptible somewhere',
                                 '5 - Clearly perceptible everywhere',
                                 '4 - Annoying somewhere',
                                 '3 - Annoying everywhere',
                                 '2 - Severely annoying somewhere',
                                 '1 - Severely annoying everywhere']

                    else:
                        assert False
                    page = PageClass(d)
                    context = {**self.each_context(request), **page.context}
                    request.current_app = self.name
                    response = TemplateResponse(request, page.get_template(), context)
                elif (ec.experiment_config.methodology == 'ccr' and
                      ec.experiment_config.vote_scale in ['CCR_THREE_POINT', 'CCR_FIVE_POINT']) \
                        or (ec.experiment_config.methodology == 'tafc' and
                            ec.experiment_config.vote_scale == '2AFC'):

                    VoteClass = Vote.find_subclass(ec.experiment_config.vote_scale)

                    svgid = self._get_matched_single_stimulusvotegroup_id(ec, next_step)
                    sid_1st, sid_2nd = self._get_matched_double_stimulus_ids(ec, svgid)
                    s_1st = self._get_matched_stimulus_dict(ec, sid_1st)
                    s_2nd = self._get_matched_stimulus_dict(ec, sid_2nd)
                    assert s_1st['type'] == 'video/mp4'
                    assert s_2nd['type'] == 'video/mp4'

                    # randomize the order of stimuli on 2AFC page
                    if random.random() < 0.5:
                        video_a = s_1st['path']
                        video_b = s_2nd['path']
                        video_a_to_b_values = VoteClass.support
                    else:
                        video_b = s_1st['path']
                        video_a = s_2nd['path']
                        video_a_to_b_values = list(reversed(VoteClass.support))

                    sgid: int = next_step['context']['stimulusgroup_id']
                    video_display_percentage = ec.experiment_config. \
                        stimulus_config.get_video_display_percentage(sgid)
                    assert video_display_percentage is not None
                    d = {'title': title,
                         'video_a': video_a,
                         'video_b': video_b,
                         'video_a_to_b_values': video_a_to_b_values,
                         'session_id': session_id,
                         'video_display_percentage': video_display_percentage,
                         'stimulusvotegroup_id': svgid,
                         **ec.experiment_config.round_context,
                         }
                    if ec.experiment_config.vote_scale == 'CCR_FIVE_POINT':
                        # only if choices not yet overridden by round_context:
                        if 'choices' not in d:
                            d['choices'] = \
                                ['Video A is much better',
                                 'Video A is better',
                                 'They are the same',
                                 'Video B is better',
                                 'Video B is much better'],
                    PageClass = map_methodology_to_page_class(
                        ec.experiment_config.methodology)
                    page = PageClass(d)
                    context = {**self.each_context(request), **page.context}
                    request.current_app = self.name
                    response = TemplateResponse(request, page.get_template(), context)
                elif (ec.experiment_config.methodology == 'samviq5d' and
                      ec.experiment_config.vote_scale == 'FIVE_POINT') or \
                        (ec.experiment_config.methodology == 'samviq' and
                         ec.experiment_config.vote_scale == '0_TO_100'):
                    svgids = self._get_matched_stimulusvotegroup_ids(ec, next_step)

                    # randomize the order of stimuli on the SAMVIQ page
                    random.shuffle(svgids)

                    ref_sid = None
                    dis_sids = []
                    for svgid in svgids:
                        sid, sid2 = self._get_matched_double_stimulus_ids(ec, svgid)
                        if ref_sid is None:
                            ref_sid = sid2
                        else:
                            assert ref_sid == sid2
                        dis_sids.append(sid)
                    ref_s = self._get_matched_stimulus_dict(ec, ref_sid)
                    dis_ss = [self._get_matched_stimulus_dict(ec, dis_sid)
                              for dis_sid in dis_sids]
                    assert ref_s['type'] == 'video/mp4'
                    for dis_s in dis_ss:
                        assert dis_s['type'] == 'video/mp4'
                    PageClass = map_methodology_to_page_class(
                        ec.experiment_config.methodology)
                    sgid: int = next_step['context']['stimulusgroup_id']
                    video_display_percentage = ec.experiment_config. \
                        stimulus_config.get_video_display_percentage(sgid)
                    assert video_display_percentage is not None
                    d = {
                        'title': title,
                        'video_ref': ref_s['path'],
                        'button_ref': 'Reference',
                        'videos': [dis_s['path'] for dis_s in dis_ss],
                        'stimulusvotegroup_ids': svgids,
                        'buttons': list(string.ascii_uppercase[:len(dis_ss)]),
                        'video_display_percentage': video_display_percentage,
                        **ec.experiment_config.round_context,
                    }
                    page = PageClass(d)
                    context = {
                        **self.each_context(request),
                        **page.context,
                    }
                    request.current_app = self.name
                    return TemplateResponse(request, page.get_template(), context)
                else:
                    assert False, 'The combination of {m} methodology with {s} vote_scale is undefined'.format(
                        m=ec.experiment_config.methodology, s=ec.experiment_config.vote_scale)

            elif request.method == 'POST':

                round_end_sec: float = time()
                rnd: Round = Round.objects.get(
                    session=session, round_id=next_step['position']['round_id'])
                round_start_sec_in_cookie = self._get_round_response_sec_from_cookie(request, rnd.id)
                try:
                    assert round_start_sec_in_cookie is not None, \
                        "expect round_start_sec in cookie but it's not"
                    response_sec = round_end_sec - round_start_sec_in_cookie
                    assert response_sec > 0, \
                        f'expect response_sec > 0 but got {response_sec} ' \
                        f'(round_end_sec {round_end_sec}, round_start_sec_in_cookie {round_start_sec_in_cookie})'
                except AssertionError as e:
                    if str(e) == "expect round_start_sec in cookie but it's not":
                        logger.warning(str(e))
                        response_sec = 'none'
                    else:
                        raise e

                sgid = next_step['context']['stimulusgroup_id']
                sg: StimulusGroup = StimulusGroup.objects.get(
                    experiment=exp,
                    stimulusgroup_id=sgid)
                skip_set_cookie: bool = False

                if (ec.experiment_config.methodology == 'acr' and
                    ec.experiment_config.vote_scale == 'FIVE_POINT') or \
                        (ec.experiment_config.methodology == 'acr5c' and
                         ec.experiment_config.vote_scale == '0_TO_100') or \
                        (ec.experiment_config.methodology == 'dcr' and
                         ec.experiment_config.vote_scale in [
                             'THREE_POINT',
                             'FIVE_POINT',
                             'SEVEN_POINT',
                             'ELEVEN_POINT',
                         ]) or \
                        (ec.experiment_config.methodology == 'tafc' and
                         ec.experiment_config.vote_scale == '2AFC') or \
                        (ec.experiment_config.methodology == 'ccr' and
                         ec.experiment_config.vote_scale in ['CCR_THREE_POINT', 'CCR_FIVE_POINT']) or \
                        (ec.experiment_config.methodology == 'samviq5d' and
                         ec.experiment_config.vote_scale == 'FIVE_POINT') or \
                        (ec.experiment_config.methodology == 'samviq' and
                         ec.experiment_config.vote_scale == '0_TO_100'):
                    score_dict = dict()
                    for key, val in request.POST.items():
                        mo = re.match(
                            r"^{m}_([0-9]*)$".format(m=map_methodology_to_html_id_key(ec.experiment_config.methodology)),
                            key)
                        if mo is None:
                            continue
                        svgid = int(mo.group(1))
                        try:
                            StimulusVoteGroup.objects.get(
                                stimulusgroup=sg, stimulusvotegroup_id=svgid)
                        except StimulusVoteGroup.DoesNotExist:
                            # verify svg does exist; if not exist, it could
                            # be double POST submission
                            skip_set_cookie = True
                            logger.warning(f'skip setting cookie as stimulus_vote_group '
                                           f'{svgid} with stimulus_group {sgid} could not '
                                           f'be identified, possibly a double POST submission.')
                            break
                        score = int(val)
                        VoteClass.assert_vote(score)
                        score_dict[svgid] = score
                    if skip_set_cookie is True:
                        pass
                    else:
                        next_step['context']['score'] = score_dict
                        next_step['context']['response_sec'] = response_sec
                        self._set_session_cookie(request, {
                            'steps': steps_performed + [next_step],
                            'session_id': session_id})
                    response = HttpResponseRedirect(
                        reverse("nest:step_session", kwargs={'session_id': session_id}))
                else:
                    assert False, 'The combination of {m} methodology with {s} vote_scale is undefined'.format(
                        m=ec.experiment_config.methodology, s=ec.experiment_config.vote_scale)
            else:
                assert False

        return response

    @staticmethod
    def _get_matched_stimulus_dict(ec, sid):
        s: dict
        for s in ec.experiment_config.stimulus_config.stimuli:
            if s['stimulus_id'] == sid:
                break
        else:
            assert False, 'no stimilus with matching ' \
                          'stimulus_id {} found: {}'. \
                format(sid,
                       ec.experiment_config.stimulus_config.stimuli)
        return s

    @staticmethod
    def _get_matched_single_stimulus_id(ec, svgid):
        svg: dict
        for svg in ec.experiment_config.stimulus_config.stimulusvotegroups:
            if svg['stimulusvotegroup_id'] == svgid:
                break
        else:
            assert False, 'no stimulusvotegroup with matching ' \
                          'stimulusvotegroup_id {} found: {}'. \
                format(svgid,
                       ec.experiment_config.stimulus_config.stimulusvotegroups)
        assert len(svg['stimulus_ids']) == 1, \
            "expect only one stimulus per" \
            " stimulusvotegroup, but has {}".format(svg['stimulus_ids'])
        sid = svg['stimulus_ids'][0]
        return sid

    @staticmethod
    def _get_matched_double_stimulus_ids(ec, svgid):
        svg: dict
        for svg in ec.experiment_config.stimulus_config.stimulusvotegroups:
            if svg['stimulusvotegroup_id'] == svgid:
                break
        else:
            assert False, 'no stimulusvotegroup with matching ' \
                          'stimulusvotegroup_id {} found: {}'. \
                format(svgid,
                       ec.experiment_config.stimulus_config.stimulusvotegroups)
        assert len(svg['stimulus_ids']) == 2, \
            "expect exactly two stimuli per" \
            " stimulusvotegroup, but has {}".format(svg['stimulus_ids'])
        sid = svg['stimulus_ids'][0]
        sid2 = svg['stimulus_ids'][1]
        return sid, sid2

    @staticmethod
    def _get_matched_single_stimulusvotegroup_id(ec, step):
        sg: dict
        for sg in ec.experiment_config.stimulus_config.stimulusgroups:
            if sg['stimulusgroup_id'] == step['context']['stimulusgroup_id']:
                break
        else:
            assert False, 'no stimulusgroup with matching ' \
                          'stimulusgroup_id {} found: {}'. \
                format(step['context']['stimulusgroup_id'],
                       ec.experiment_config.stimulus_config.stimulusgroups)
        assert len(sg['stimulusvotegroup_ids']) == 1, \
            "expect only one stimulusvotegroup per" \
            " round, but has {}".format(sg['stimulusvotegroup_ids'])
        svgid = sg['stimulusvotegroup_ids'][0]
        return svgid

    @classmethod
    def _get_matched_stimulusvotegroup_ids(cls, ec, step):
        return cls._get_matched_stimulusgroup(ec, step)['stimulusvotegroup_ids']

    @staticmethod
    def _get_matched_stimulusgroup(ec, step):
        sg: dict
        for sg in ec.experiment_config.stimulus_config.stimulusgroups:
            if sg['stimulusgroup_id'] == step['context']['stimulusgroup_id']:
                break
        else:
            assert False, 'no stimulusgroup with matching ' \
                          'stimulusgroup_id {} found: {}'. \
                format(step['context']['stimulusgroup_id'],
                       ec.experiment_config.stimulus_config.stimulusgroups)
        return sg

    @staticmethod
    def _step_is_addition(step):
        """
        Criterion to determine if a step is addition (but not round).

        A step could be either an "addition step" (instruction, survey, etc.)
        or "round step" (step where some stimuli got voted).
        """
        return 'before_or_after' in step['position']


class DefaultNestSite(LazyObject):
    def _setup(self):
        NestSiteClass = import_string(apps.get_app_config('nest').default_site)
        self._wrapped = NestSiteClass()


site = DefaultNestSite()
