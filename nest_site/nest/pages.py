from abc import ABC, ABCMeta, abstractmethod

from nest.helpers import override


class PageWithVideoMixin(object):

    DEFAULT_VIDEO_CONTEXT = {
        'video_show_controls': False,
        'video_display_percentage': 100,
        'preload_videos': False,
    }

    def _assert_video_context(self):
        required_fields = ['video_show_controls', 'video_display_percentage']
        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        assert isinstance(self.context['video_show_controls'], bool)
        assert 0 < self.context['video_display_percentage'] <= 100
        assert isinstance(self.context['preload_videos'], bool)


class Page(object):

    __metaclass__ = ABCMeta

    DEFAULT_CONTEXT = dict()

    class Meta:
        abstract = True

    def __init__(self, context: dict):
        self.context = dict()

        # get default context
        self.context.update(self.DEFAULT_CONTEXT)
        if isinstance(self, PageWithVideoMixin):
            self.context.update(PageWithVideoMixin.DEFAULT_VIDEO_CONTEXT)

        # get from input context, overriding default
        self.context.update(context)

        # assert
        self._assert_context()
        if isinstance(self, PageWithVideoMixin):
            self._assert_video_context()

    @abstractmethod
    def _assert_context(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def DEFAULT_TEMPLATE(self):
        raise NotImplementedError

    def get_template(self):
        return self.DEFAULT_TEMPLATE

    VERSION = '1.0'


class GenericPage(Page, ABC):
    """Generic page"""
    DEFAULT_TEMPLATE = 'nest/generic.html'

    @override(Page)
    def _assert_context(self):
        required_fields = ['title', 'text_html', 'actions_html']
        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'


class AcrPage(Page, PageWithVideoMixin, ABC):  # TODO: generalize AcrPage to support continuous scale, so that there's no need for separate Acr5cPage # noqa E501
    """Absolute Catagory Rating (ACR) page"""
    TEMPLATES = {'interactive': 'nest/acr.html',
                 'standard': 'nest/acr_standard.html'
                 }
    DEFAULT_TEMPLATE = 'interactive'

    DEFAULT_CONTEXT = {
        'instruction_html':
            """<p> Watch a video by clicking on the "Play video" button. The video will loop. <em> Press "space" key or double click the mouse </em> to exit. After that, rate the video by answering the question provided. </p>""",  # noqa E501
        'button': 'Play video',
        'question':
            "On a scale of 1 to 5, how would you rate the video quality?",
        'choices':
            ['5 - Excellent',
             '4 - Good',
             '3 - Fair',
             '2 - Poor',
             '1 - Bad']
    }

    @override(Page)
    def _assert_context(self):
        if 'template_version' not in self.context:
            self.context['template_version'] = self.DEFAULT_TEMPLATE

        if self.context['template_version'] == 'interactive':
            required_fields = ['title', 'instruction_html',
                               'button', 'video',
                               'question', 'choices',
                               'stimulusvotegroup_id']
        elif self.context['template_version'] == 'standard':
            required_fields = ['title', 'instruction_html',
                               'num_plays', 't_gray',
                               'button', 'video',
                               'question', 'choices',
                               'stimulusvotegroup_id']
        else:
            assert False, 'acr methodology only supports interactive and standard template_version'

        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        if 'session_id' in self.context:
            assert isinstance(self.context['session_id'], int)
        if self.context['template_version'] == 'standard':
            assert self.context['num_plays'] >= 1
            if 'min_num_plays' in self.context:
                assert self.context['num_plays'] >= self.context['min_num_plays'] >= 0
            assert self.context['t_gray'] >= 0
            if 'text_color' in self.context:
                assert len(self.context['text_color']) == 7 and self.context['text_color'].startswith('#'), \
                    'text_color must in the format of #0000FF'
            if 'text_vert_perc' in self.context:
                assert 0 <= self.context['text_vert_perc'] <= 100
            if 'overlay_on_video_js' in self.context:
                assert isinstance(self.context['overlay_on_video_js'], str)

    @override(Page)
    def get_template(self):
        return self.TEMPLATES[self.context['template_version']]


class Acr5cPage(Page, PageWithVideoMixin, ABC):
    """Absolute Catagory Rating (ACR) with 5-point continuous scale page"""
    TEMPLATES = {'interactive': 'nest/acr5c.html',
                 'standard': 'nest/acr5c_standard.html'}

    DEFAULT_TEMPLATE = 'interactive'

    DEFAULT_CONTEXT = {
        'instruction_html':
            """<p> Watch a video by clicking on the "Play video" button. The video will loop. <em> Press "space" key or double click the mouse </em> to exit. After that, rate the video by answering the question provided. </p>""",  # noqa E501
        'button': 'Play video',
        'question':
            "On a scale of 0 to 100, how would you rate the video quality?",
        'labels':
            ['Excellent',
             'Good',
             'Fair',
             'Poor',
             'Bad']
    }

    @override(Page)
    def _assert_context(self):
        if 'template_version' not in self.context:
            self.context['template_version'] = self.DEFAULT_TEMPLATE

        if self.context['template_version'] == 'interactive':
            required_fields = ['title', 'instruction_html',
                               'button', 'video',
                               'question', 'labels',
                               'stimulusvotegroup_id']
        elif self.context['template_version'] == 'standard':
            required_fields = ['title', 'instruction_html',
                               'num_plays', 't_gray',
                               'button', 'video',
                               'question', 'labels',
                               'stimulusvotegroup_id']
        else:
            assert False, 'acr5c methodology only supports interactive and standard template_version'

        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        if 'session_id' in self.context:
            assert isinstance(self.context['session_id'], int)
        if self.context['template_version'] == 'standard':
            assert self.context['num_plays'] >= 1
            if 'min_num_plays' in self.context:
                assert self.context['num_plays'] >= self.context['min_num_plays'] >= 0
            assert self.context['t_gray'] >= 0
            if 'text_color' in self.context:
                assert len(self.context['text_color']) == 7 and self.context['text_color'].startswith('#'), \
                    'text_color must in the format of #0000FF'
            if 'text_vert_perc' in self.context:
                assert 0 <= self.context['text_vert_perc'] <= 100
        if self.context['template_version'] == 'interactive':
            assert (('start_seconds' in self.context and 'end_seconds' in self.context)
                    or ('start_seconds' not in self.context and 'end_seconds' not in self.context))
            if 'start_seconds' in self.context and 'end_seconds' in self.context:
                assert self.context['start_seconds'] >= 0
                assert self.context['end_seconds'] >= self.context['start_seconds']

    @override(Page)
    def get_template(self):
        return self.TEMPLATES[self.context['template_version']]


class DcrPage(Page, PageWithVideoMixin, ABC):
    """Degradation Category Rating (DCR) page"""
    TEMPLATES = {'interactive': 'nest/dcr.html',
                 'standard': 'nest/dcr_standard.html'
                 }
    DEFAULT_TEMPLATE = 'interactive'

    DEFAULT_CONTEXT = {
        'instruction_html':
            """<p> Watch a reference video R, followed by its degraded version D. Each video will loop. <em> Press "space" key or double click the mouse </em> to exit. After that, rate the videos by answering the question provided. </p>""",  # noqa E501
        'button_a': 'Play reference R',
        'button_b': 'Play degraded D',
        'question':
            "Comparing to the reference R, how would you rate the impairment in D?",
        'choices':
            ['5 - Imperceptible',
             '4 - Perceptible, but not annoying',
             '3 - Slightly annoying',
             '2 - Annoying',
             '1 - Very annoying']
    }

    @override(Page)
    def _assert_context(self):
        if 'template_version' not in self.context:
            self.context['template_version'] = self.DEFAULT_TEMPLATE

        if self.context['template_version'] == 'interactive':
            required_fields = ['title', 'instruction_html',
                               'button_a', 'button_b',
                               'video_a', 'video_b',
                               'question', 'choices',
                               'stimulusvotegroup_id']
        elif self.context['template_version'] == 'standard':
            required_fields = ['title', 'instruction_html',
                               'num_plays', 't_gray',
                               'button_a', 'button_b',
                               'video_a', 'video_b',
                               'question', 'choices',
                               'stimulusvotegroup_id']
        else:
            assert False, 'dcr methodology only supports interactive and standard template_version'

        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        if self.context['template_version'] == 'standard':
            assert self.context['num_plays'] >= 1
            if 'min_num_plays' in self.context:
                assert self.context['num_plays'] >= self.context['min_num_plays'] >= 0
            assert self.context['t_gray'] >= 0
            if 'text_color' in self.context:
                assert len(self.context['text_color']) == 7 and self.context['text_color'].startswith('#'), \
                    'text_color must in the format of #0000FF'
            if 'text_vert_perc' in self.context:
                assert 0 <= self.context['text_vert_perc'] <= 100

    @override(Page)
    def get_template(self):
        return self.TEMPLATES[self.context['template_version']]


class CcrPage(Page, PageWithVideoMixin, ABC):
    """Comparison Category Rating (CCR) page"""
    TEMPLATES = {'interactive': 'nest/ccr.html',
                 'standard': 'nest/ccr_standard.html'
                 }
    DEFAULT_TEMPLATE = 'interactive'

    DEFAULT_CONTEXT = {
        'instruction_html':
            """<p> Watch a Video A, followed by Video B. Each video will loop. <em> Press "space" key or double click the mouse </em> to exit. After that, rate the videos by answering the question provided. </p>""",  # noqa E501
        'button_a': 'Play Video A',
        'button_b': 'Play Video B',
        'question':
            "How do you compare the visual quality of Video A to Video B?",
        'choices':
            ['Video A is better',
             'They are the same',
             'Video B is better'],
    }

    @override(Page)
    def _assert_context(self):
        if 'template_version' not in self.context:
            self.context['template_version'] = self.DEFAULT_TEMPLATE

        if self.context['template_version'] == 'interactive':
            required_fields = ['title', 'instruction_html',
                               'button_a', 'button_b',
                               'video_a', 'video_b',
                               'video_a_to_b_values',
                               'question', 'choices',
                               'stimulusvotegroup_id']
        elif self.context['template_version'] == 'standard':
            required_fields = ['title', 'instruction_html',
                               'num_plays', 't_gray',
                               'button_a', 'button_b',
                               'video_a', 'video_b',
                               'video_a_to_b_values',
                               'question', 'choices',
                               'stimulusvotegroup_id']
        else:
            assert False, f"ccr methodology only supports interactive and standard template_version, but " \
                          f"is: {self.context['template_version']}"

        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'

        assert len(self.context['choices']) == len(self.context['video_a_to_b_values']), \
            f"the length of choices and video_a_to_b_values must be equal, but they are: {self.context['choices']} " \
            f"and {self.context['video_a_to_b_values']}"

        if self.context['template_version'] == 'standard':
            assert self.context['num_plays'] >= 1
            if 'min_num_plays' in self.context:
                assert self.context['num_plays'] >= self.context['min_num_plays'] >= 0
            assert self.context['t_gray'] >= 0
            if 'text_color' in self.context:
                assert len(self.context['text_color']) == 7 and self.context['text_color'].startswith('#'), \
                    'text_color must in the format of #0000FF'
            if 'text_vert_perc' in self.context:
                assert 0 <= self.context['text_vert_perc'] <= 100

    @override(Page)
    def get_template(self):
        return self.TEMPLATES[self.context['template_version']]


class SamviqPage(Page, PageWithVideoMixin, ABC):
    """SAMVIQ with continuous quality scale with 5 labels"""
    DEFAULT_TEMPLATE = 'nest/samviq.html'

    DEFAULT_CONTEXT = {
        'instruction_html':
            """<p> Watch a reference video R and rate each of its processed versions. Each video will loop. <em> Press "space" key or double click the mouse </em> to exit. After that, rate the videos by answering the question provided. </p>""",  # noqa E501
        'question':
            "Comparing to the reference R, how would you rate the quality of the videos?",
        'labels':
            ['Excellent',
             'Good',
             'Fair',
             'Poor',
             'Bad'],
    }

    @override(Page)
    def _assert_context(self):
        required_fields = ['title', 'instruction_html',
                           'videos', 'video_ref',
                           'buttons', 'button_ref',
                           'question', 'labels',
                           'stimulusvotegroup_ids']
        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        assert len(self.context['labels']) == 5
        assert isinstance(self.context['videos'], list)
        assert len(self.context['videos']) > 0
        assert isinstance(self.context['buttons'], list)
        assert len(self.context['buttons']) \
               == len(self.context['videos']) \
               == len(self.context['stimulusvotegroup_ids'])


class Samviq5dPage(Page, PageWithVideoMixin, ABC):
    """SAMVIQ with 5-point discrete quality scale"""
    DEFAULT_TEMPLATE = 'nest/samviq5d.html'

    DEFAULT_CONTEXT = {
        'instruction_html':
            """<p> Watch a reference video R and rate each of its processed versions. Each video will loop. <em> Press "space" key or double click the mouse </em> to exit. After that, rate the videos by answering the question provided. </p>""",  # noqa E501
        'question':
            "Comparing to the reference R, how would you rate the quality of the videos?",
        'choices':
            ['5 - Excellent',
             '4 - Good',
             '3 - Fair',
             '2 - Poor',
             '1 - Bad'],
    }

    @override(Page)
    def _assert_context(self):
        required_fields = ['title', 'instruction_html',
                           'videos', 'video_ref',
                           'buttons', 'button_ref',
                           'question', 'choices',
                           'stimulusvotegroup_ids']
        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        assert len(self.context['choices']) == 5
        assert isinstance(self.context['videos'], list)
        assert len(self.context['videos']) > 0
        assert isinstance(self.context['buttons'], list)
        assert len(self.context['buttons']) \
               == len(self.context['videos']) \
               == len(self.context['stimulusvotegroup_ids'])


class StatusPage(Page, ABC):
    """
    Status page to list experiment sessions status for a subject.
    Example for tests:
    tests = \
        [
            {'title': 'test 1', 'session': '1', 'status': 'Done', 'action': None},
            {'title': 'test 2', 'session': '5', 'status': 'Done', 'action': None},
            {'title': 'test 2', 'session': '25', 'status': 'Unfinished', 'action': 'Reset'},
            {'title': 'test 3', 'session': '61', 'status': 'New', 'action': 'Start'},
        ]
    """
    DEFAULT_TEMPLATE = 'nest/status.html'

    @override(Page)
    def _assert_context(self):
        required_fields = ['title', 'tests']
        for e in required_fields:
            assert e in self.context, f'parameter {e} is required in context'
        for test in self.context['tests']:
            assert isinstance(test, dict)
            assert 'title' in test
            assert 'session' in test
            assert 'status' in test
            assert 'action' in test
            assert test['status'] in ['Uninitialized', 'Partially initialized',
                                      'New', 'Unfinished', 'In progress', 'Done']
            assert test['action'] in [None, 'Start', 'Reset', 'Continue']
            if test['action'] in ['Reset', 'Start', 'Continue']:
                assert 'action_url' in test


def map_methodology_to_page_class(methodology: str) -> Page.__class__:
    if methodology == 'acr':
        return AcrPage
    elif methodology == 'acr5c':
        return Acr5cPage
    elif methodology == 'dcr':
        return DcrPage
    elif methodology == 'tafc':
        return CcrPage
    elif methodology == 'ccr':
        return CcrPage
    elif methodology == 'samviq5d':
        return Samviq5dPage
    elif methodology == 'samviq':
        return SamviqPage
    else:
        assert False, f'unknown mapping from methodology {methodology} to page class.'


def map_methodology_to_html_id_key(methodology: str) -> str:
    if methodology == 'tafc':
        return 'ccr'
    elif methodology in ['acr', 'acr5c', 'dcr', 'ccr', 'samviq5d', 'samviq']:
        return methodology
    else:
        assert False, f'unknown mapping from methodology {methodology} to HTML id key.'
