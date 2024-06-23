import os

from typing import List, Optional

from nest.helpers import validate_xml
from nest_site.settings import map_media_url_to_local

NEST_ROOT = os.path.dirname(os.path.realpath(__file__))


class NestConfig(object):

    @classmethod
    def root_path(cls, *components):
        return os.path.join(NEST_ROOT, *components)

    @classmethod
    def tests_resource_path(cls, *components):
        return cls.root_path('tests', 'resource', *components)

    @classmethod
    def media_path(cls, *components):
        return cls.root_path('..', 'media', *components)

    @classmethod
    def tests_workdir_path(cls, *components):
        return cls.root_path('tests', 'workdir', *components)

    @classmethod
    def resource_path(cls, *components):
        return cls.root_path('resource', *components)


class DisplayConfig(object):

    @staticmethod
    def show(**kwargs):
        from matplotlib import pyplot as plt
        if 'write_to_dir' in kwargs:
            format = kwargs['format'] if 'format' in kwargs else 'png'
            filedir = kwargs['write_to_dir'] if kwargs['write_to_dir'] is not None else NestConfig.tests_workdir_path('output')
            os.makedirs(filedir, exist_ok=True)
            for fignum in plt.get_fignums():
                fig = plt.figure(fignum)
                fig.savefig(os.path.join(filedir, str(fignum) + '.' + format), format=format)
        else:
            plt.show()


class StimulusConfig(object):

    def __init__(self, config: dict, **more):
        self.config: dict = config
        assert isinstance(self.config, dict)
        self._assert(**more)

    def _assert(self, **more):
        assert 'contents' in self.config
        assert 'stimuli' in self.config
        assert 'stimulusvotegroups' in self.config
        assert 'stimulusgroups' in self.config

        assert isinstance(self.contents, list)
        for c in self.contents:
            assert isinstance(c, dict)
            assert 'content_id' in c
            assert 'name' in c
        cids = self.content_ids
        assert len(set(cids)) == len(cids), \
            f'content_ids must be unique, but got: {cids}'

        assert isinstance(self.stimuli, list)
        for s in self.stimuli:
            assert isinstance(s, dict)
            assert 'stimulus_id' in s
            assert 'path' in s
            assert 'type' in s
            assert 'content_id' in s
            assert s['content_id'] in self.content_ids
        sids = self.stimulus_ids
        assert len(set(sids)) == len(sids), \
            f'stimulus_ids must be unique, but got: {sids}'

        if 'skip_path_check' in more and more['skip_path_check'] is True:
            pass
        else:
            for s in self.stimuli:
                url_path: str = s['path']
                if url_path.startswith('http://') or url_path.startswith('https://'):
                    # don't check publically hosted urls
                    continue
                local_path = map_media_url_to_local(url_path)
                assert os.path.exists(local_path), \
                    f"url path {url_path} should map to local path {local_path}, which does not exist"

        assert isinstance(self.stimulusvotegroups, list)
        for svg in self.stimulusvotegroups:
            assert isinstance(svg, dict)
            assert 'stimulusvotegroup_id' in svg
            assert 'stimulus_ids' in svg
            assert isinstance(svg['stimulus_ids'], list)
            for sid in svg['stimulus_ids']:
                assert sid in self.stimulus_ids
            assert len(svg['stimulus_ids']) in [1, 2], \
                "for now, only support stimulus_ids list length 1 " \
                "(single-stimulus test) or 2 (double-stimulus test)"
        svgids = self.stimulusvotegroup_ids
        assert len(set(svgids)) == len(svgids), \
            f'stimulusvotegroup_ids must be unique, but got: {svgids}'

        assert isinstance(self.stimulusgroups, list)
        for sg in self.stimulusgroups:
            assert isinstance(sg, dict)
            assert 'stimulusgroup_id' in sg
            assert 'stimulusvotegroup_ids' in sg
            assert isinstance(sg['stimulusvotegroup_ids'], list)
            for svgid in sg['stimulusvotegroup_ids']:
                assert svgid in self.stimulusvotegroup_ids
            if 'video_display_percentage' in sg:
                assert 0 < sg['video_display_percentage'] <= 100
        sgids = self.stimulusgroup_ids
        assert len(set(sgids)) == len(sgids), \
            f'stimulusgroup_ids must be unique, but got: {sgids}'

    @property
    def contents(self) -> List[dict]:
        return self.config['contents']

    @property
    def stimuli(self) -> List[dict]:
        return self.config['stimuli']

    @property
    def stimulusvotegroups(self) -> List[dict]:
        return self.config['stimulusvotegroups']

    @property
    def stimulusgroups(self) -> List[dict]:
        return self.config['stimulusgroups']

    @property
    def content_ids(self) -> List[int]:
        return [c['content_id'] for c in self.contents]

    @property
    def stimulus_ids(self) -> List[int]:
        return [s['stimulus_id'] for s in self.stimuli]

    @property
    def stimulusvotegroup_ids(self) -> List[int]:
        return [svg['stimulusvotegroup_id'] for svg in self.stimulusvotegroups]

    @property
    def stimulusgroup_ids(self) -> List[int]:
        return [sg['stimulusgroup_id'] for sg in self.stimulusgroups]

    def get_video_display_percentage(self, stimulusgroup_id: int) -> Optional[int]:
        sg: dict
        for sg in self.stimulusgroups:
            if sg['stimulusgroup_id'] == stimulusgroup_id:
                if 'video_display_percentage' in sg:
                    return sg['video_display_percentage']
                else:
                    return 100  # 100%, or full browser canvas
        else:
            return None

    def get_pre_message(self, stimulusgroup_id: int) -> Optional[str]:
        sg: dict
        for sg in self.stimulusgroups:
            if sg['stimulusgroup_id'] == stimulusgroup_id:
                if 'pre_message' in sg:
                    return sg['pre_message']
                else:
                    return None
        else:
            return None

    def get_text_color(self, stimulusgroup_id: int) -> Optional[str]:
        sg: dict
        for sg in self.stimulusgroups:
            if sg['stimulusgroup_id'] == stimulusgroup_id:
                if 'text_color' in sg:
                    return sg['text_color']
                else:
                    return None
        else:
            return None

    def get_super_stimulusgroup_id(self, stimulusgroup_id: int) -> Optional[int]:
        sg: dict
        for sg in self.stimulusgroups:
            if sg['stimulusgroup_id'] == stimulusgroup_id:
                if 'super_stimulusgroup_id' in sg:
                    return sg['super_stimulusgroup_id']
                else:
                    return None
        else:
            return None

    @property
    def super_stimulusgroup_ids(self) -> Optional[List[int]]:
        """
        super_stimulusgroup_ids, if present, allows for a hierarchical grouping
        of stimulusgroups. The randomization of stimulusgroups within a session
        will then be hierarchical instead of flat: first randomize between
        super_stimulusgroups, then randomize within each super_stimulusgroup.
        """
        # check super_stimulusgroup_id is all-present or all-absent
        super_sg_ids = [sg['super_stimulusgroup_id'] if 'super_stimulusgroup_id' in sg else None for sg in self.stimulusgroups]
        assert all([ssid is None for ssid in super_sg_ids]) or all([ssid is not None for ssid in super_sg_ids]), \
            f"super_stimulusgroup_id must be all-present or all-absent, but is {super_sg_ids}."
        if all([ssid is not None for ssid in super_sg_ids]):
            return super_sg_ids
        else:
            return None


class ExperimentConfig(object):

    def __init__(self,
                 stimulus_config: StimulusConfig,
                 config: dict):
        self.stimulus_config: StimulusConfig = stimulus_config
        self.config: dict = config
        assert isinstance(self.config, dict)
        self._assert()

    def _assert(self):
        assert isinstance(self.title, str)

        if self.description is not None:
            assert isinstance(self.description, str)

        assert isinstance(self.rounds_per_session, int)
        assert self.rounds_per_session >= 1

        assert self.random_seed is None or isinstance(self.random_seed, int)

        from .models import Vote
        Vote.find_subclass(self.vote_scale)

        assert self.methodology in ['acr', 'acr5c', 'dcr', 'tafc', 'ccr', 'samviq', 'samviq5d']
        if self.methodology in ['acr', 'acr5c']:
            for svg in self.stimulus_config.stimulusvotegroups:
                assert len(svg['stimulus_ids']) == 1
        elif self.methodology in ['dcr', 'tafc', 'ccr']:
            for svg in self.stimulus_config.stimulusvotegroups:
                assert len(svg['stimulus_ids']) == 2
        elif self.methodology in ['samviq', 'samviq5d']:
            for svg in self.stimulus_config.stimulusvotegroups:
                assert len(svg['stimulus_ids']) == 2
            # must make sure that for each sg, all svgs share the same reference
            svgs = self.stimulus_config.stimulusvotegroups
            svg_dict = dict(zip(  # dict: svg_id -> svg
                [svg['stimulusvotegroup_id'] for svg in svgs], svgs))
            for sg in self.stimulus_config.stimulusgroups:
                second_sids = [svg_dict[svg_id]['stimulus_ids'][1]
                               for svg_id in sg['stimulusvotegroup_ids']]
                assert len(set(second_sids)) == 1, \
                    f"all svgs belong to one sg must share the same second " \
                    f"element in svg['stimulus_ids'], which is the reference:" \
                    f" {second_sids}"
        else:
            assert False

        try:
            if self.methodology in ['acr', 'dcr']:
                assert self.vote_scale in [
                    'THREE_POINT',
                    'FIVE_POINT',
                    'SEVEN_POINT',
                    'ELEVEN_POINT',
                ]
            elif self.methodology == 'tafc':
                assert self.vote_scale in ['2AFC']
            elif self.methodology == 'ccr':
                assert self.vote_scale in ['CCR_THREE_POINT', 'CCR_FIVE_POINT']
            elif self.methodology == 'acr':
                assert self.vote_scale in ['FIVE_POINT']
            elif self.methodology == 'acr5c':
                assert self.vote_scale in ['0_TO_100']
            elif self.methodology == 'samviq':
                assert self.vote_scale in ['0_TO_100']
            elif self.methodology == 'samviq5d':
                assert self.vote_scale in ['FIVE_POINT']
            else:
                assert False
        except AssertionError:
            raise AssertionError(f'Unsupported (methodology, vote_scale): ({self.methodology}, {self.vote_scale})')

        self._assert_blocklist_stimulusgroup_ids()
        self._assert_training_round_ids()
        self._assert_prioritized()
        self._assert_additions()
        self._assert_round_context()
        self._assert_done_context()

    @property
    def title(self):
        assert 'title' in self.config
        return self.config['title']

    @property
    def description(self):
        return self.config['description'] \
            if 'description' in self.config else None

    @property
    def rounds_per_session(self):
        assert 'rounds_per_session' in self.config
        return self.config['rounds_per_session']

    @property
    def random_seed(self):
        return self.config['random_seed'] \
            if 'random_seed' in self.config else None

    @property
    def vote_scale(self):
        assert 'vote_scale' in self.config
        return self.config['vote_scale']

    @property
    def methodology(self):
        assert 'methodology' in self.config
        return self.config['methodology']

    @property
    def prioritized(self):
        """
        prioritized is a list of dictionaries in the format of
        [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 1, 'round_id': None, 'stimulusgroup_id': 6},
        ],
        where 'session_idx': None represents that the rule applies to all sessions,
        and 'round_id': None represents that the rule applies to a randomized
        round within that session. The prioritized list dictates in which
        (session, round) to set the stimulusgroup to be voted, not subject to
        the ordering procedure by ExperimentOrder. Note that the later a
        dictionary appears in the list, the higher priority it has to override
        earlier dictionaries.

        Note that stimulusgroup_idx is different from stimulusgroup_id. The
        former has to take a value from [0, len(stimulusgroups) - 1], and the
        latter could take value from any non-negative integers.
        """
        return self.config['prioritized'] \
            if 'prioritized' in self.config else list()

    @property
    def blocklist_stimulusgroup_ids(self):
        """
        stimulusgroup_ids that appear in blocklist_stimulusgroup_ids are not
        selected unless they appear in the prioritized list.

        For example:
        to set sg 0 as training:
        1) add it to the prioritized list
        2) mark it in the blocklist_stimulusgroup_ids, such that it won't
        appear elsewhere
        """
        return self.config['blocklist_stimulusgroup_ids'] \
            if 'blocklist_stimulusgroup_ids' in self.config else list()

    @property
    def training_round_ids(self):
        """
        training_round_ids are the round_ids for rounds that are considered as
        "training" rounds. Usually this affects the messages displayed in the
        round titles. For example, if a round is a "training" round, the title
        could be "training 1 of 2"; if a round is a regular round, the title
        could be "round 1 of 8" (assume in rounds_per_session is 10).
        """
        return self.config['training_round_ids'] \
            if 'training_round_ids' in self.config else list()

    def _assert_training_round_ids(self):
        assert isinstance(self.training_round_ids, list)
        rounds_per_session = self.rounds_per_session
        for rid in self.training_round_ids:
            assert 0 <= rid < rounds_per_session

    def _assert_blocklist_stimulusgroup_ids(self):
        assert isinstance(self.blocklist_stimulusgroup_ids, list)
        stimulusgroup_ids = self.stimulus_config.stimulusgroup_ids
        for bsgid in self.blocklist_stimulusgroup_ids:
            assert isinstance(bsgid, int) and \
                bsgid in stimulusgroup_ids

    def _assert_prioritized(self):
        assert isinstance(self.prioritized, list)
        stimulusgroup_ids = self.stimulus_config.stimulusgroup_ids
        for d in self.prioritized:
            assert isinstance(d, dict)
            assert 'session_idx' in d
            assert 'round_id' in d
            assert 'stimulusgroup_id' in d
            session_idx = d['session_idx']
            round_id = d['round_id']
            stimulusgroup_id = d['stimulusgroup_id']
            assert session_idx is None or \
                   (isinstance(session_idx, int) and session_idx >= 0)
            assert round_id is None or \
                   (isinstance(round_id, int) and
                    0 <= round_id < self.rounds_per_session)
            assert isinstance(stimulusgroup_id, int) and \
                   stimulusgroup_id in stimulusgroup_ids

    @property
    def additions(self):
        """
        additions specify the steps in a test session that are not "rounds".
        This includes instruction pages, pre-/post-test surveys etc.
        """
        return self.config['additions'] \
            if 'additions' in self.config else list()

    @property
    def round_context(self):
        """
        round_context specifies the appearances (the page displayed) in each
        voting round.
        """
        return self.config['round_context'] \
            if 'round_context' in self.config else dict()

    @property
    def done_context(self):
        """
        done_conext specifies the appearances (the page display) when a session
        is done.
        """
        return self.config['done_context'] \
            if 'done_context' in self.config else dict()

    def _assert_additions(self):
        assert isinstance(self.additions, list), f'expect self.additions to be a list, but is: {self.additions}'
        for addition in self.additions:
            assert 'position' in addition
            assert 'round_id' in addition['position']
            assert isinstance(addition['position']['round_id'], int)
            assert 0 <= addition['position']['round_id'] < self.rounds_per_session
            assert 'before_or_after' in addition['position']
            assert addition['position']['before_or_after'] in ['before', 'after']
            assert 'context' in addition
            assert 'title' in addition['context']
            assert 'text_html' in addition['context']
            assert 'actions_html' in addition['context']
            assert '{action_url}' in addition['context']['actions_html'], \
                "expect '{action_url}' in actions_html as template to be" \
                "filled during page rendering"

    def _assert_round_context(self):
        assert isinstance(self.round_context, dict)
        # leave other assertions to the Page initialization stage

    def _assert_done_context(self):
        assert isinstance(self.done_context, dict)
        if 'text_html' in self.done_context:
            assert validate_xml(self.done_context['text_html']), \
                f"invalid html: {self.done_context['text_html']}"
