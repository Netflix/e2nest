import json
import logging
import os
import random
import string
from typing import List, Optional

import numpy as np
import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from nest.config import ExperimentConfig, NestConfig, StimulusConfig
from nest.control import ExperimentController, SessionStatus
from nest.helpers import empty_object, map_path_to_noise_rmse, override
from nest.models import Content, DiscreteVote, Experiment, Experimenter, \
    ExperimentRegister, Round, Session, Stimulus, StimulusGroup, \
    StimulusVoteGroup, Subject, Vote, VoteRegister
from nest.pages import map_methodology_to_page_class
from nest.sites import NestSite
from sureal.dataset_reader import PairedCompDatasetReader as \
    SurealPairedCompDatasetReader
from sureal.dataset_reader import RawDatasetReader as SurealRawDatasetReader

logging.basicConfig()
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])
logger.setLevel('INFO')


class SurealMixin(object):
    def _retrieve_or_create_stimuli(self) -> List[Stimulus]:
        dict_contentid_refvideo = dict()
        for ref_video in self.dataset.ref_videos:
            dict_contentid_refvideo[ref_video['content_id']] = ref_video
        stimuli = []
        for dis_video in self.dataset.dis_videos:
            ref_video = dict_contentid_refvideo[dis_video['content_id']]
            content = Content.objects.get(
                name=f"{self.dataset.dataset_name}-{ref_video['content_name']}",
                content_id=dis_video['content_id'])
            try:
                stimulus = Stimulus.objects.get(
                    content=content, stimulus_id=dis_video['asset_id'])
            except Stimulus.DoesNotExist:
                stimulus = Stimulus.objects.create(
                    content=content, stimulus_id=dis_video['asset_id'])
            stimuli.append(stimulus)
        return stimuli

    @staticmethod
    def find_or_create_experimenter(experiment, experimenter_username):
        # find or create user from experimenter's username
        user: User
        try:
            user = User.objects.get(username=experimenter_username)
            if not user.is_staff:
                raise AssertionError(
                    f"Cannot populate NEST with experimenter: user "
                    f"{experimenter_username} exists but is not staff")
        except User.DoesNotExist:
            user = User.objects.create_user(experimenter_username,
                                            password="", is_staff=True)
        # find or create experimenter from user
        experimenter: Experimenter
        try:
            experimenter = Experimenter.objects.get(user=user)
        except Experimenter.DoesNotExist:
            experimenter = Experimenter.objects.create(user=user)
        ExperimentRegister.objects.create(experiment=experiment,
                                          experimenter=experimenter)

    @staticmethod
    def make_experiment_config_dict(contents, stimuli, stimulusvotegroups, stimulusgroups, seed):
        d = dict()
        d['stimulus_config'] = {
            'contents': contents,
            'stimuli': stimuli,
            'stimulusvotegroups': stimulusvotegroups,
            'stimulusgroups': stimulusgroups,
        }
        additions = list()

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
            """
            <p>
                <a class="button" href="{action_url}"  id="start">Start Test</a>
            </p>
            """
        additions.append({
            'position': {
                'round_id': 0,
                'before_or_after': 'before'
            },
            'context': {
                'title': title,
                'text_html': text_html,
                'actions_html': actions_html,
            }
        })
        d['experiment_config'] = {
            'title': 'test',
            'description': 'test',
            "methodology": "acr",  # hardcoded, not meant for actual test
            'vote_scale': 'FIVE_POINT',  # hardcoded, not meant for actual test
            'rounds_per_session': len(stimulusgroups),
            'random_seed': seed,
            'prioritized': [],
            'blocklist_stimulusgroup_ids': [],
            'additions': additions,
        }
        # assert conformity
        scfg = StimulusConfig(d['stimulus_config'], skip_path_check=True)
        _ = ExperimentConfig(stimulus_config=scfg, config=d['experiment_config'])
        return d


class SurealRawDatasetReaderPlus(SurealRawDatasetReader, SurealMixin):
    """
    Extended dataset reader that handles Sureal dataset format, and have extra
    capability such as populate NEST databases.
    """

    @override(SurealRawDatasetReader)
    def _assert_dataset(self):
        super()._assert_dataset()

        assert hasattr(self.dataset, 'dataset_name')
        assert hasattr(self.dataset, 'ref_videos')
        assert isinstance(self.dataset.ref_videos, list)
        for ref_video in self.dataset.ref_videos:
            assert 'content_name' in ref_video
            assert 'content_id' in ref_video
            assert 'path' in ref_video
        assert hasattr(self.dataset, 'dis_videos')
        assert isinstance(self.dataset.dis_videos, list)
        self.os_style = None
        for dis_video in self.dataset.dis_videos:
            assert 'asset_id' in dis_video
            assert 'content_id' in dis_video
            assert 'os' in dis_video

            assert (isinstance(dis_video['os'], list) or
                    isinstance(dis_video['os'], dict))

            if isinstance(dis_video['os'], list):
                assert len(dis_video['os']) == self.num_observers
                if self.os_style is None:
                    self.os_style = list
                else:
                    assert self.os_style == list
            elif isinstance(dis_video['os'], dict):
                if self.os_style is None:
                    self.os_style = dict
                else:
                    assert self.os_style == dict
            else:
                assert False

            assert 'path' in dis_video

    @transaction.atomic  # noqa C901
    def populate_nest(self, **more):  # noqa C901

        assert 'vote_class' in more
        vote_class = more['vote_class']

        experimenter_username = more['experimenter_username'] \
            if 'experimenter_username' in more else None
        assert experimenter_username is None or \
               isinstance(experimenter_username, str)

        # create experiment, dataset
        try:
            experiment = Experiment(title=self.dataset.dataset_name)
            experiment.save()
        except IntegrityError:
            raise AssertionError(
                f'Experiment with title {self.dataset.dataset_name} exists.')

        if experimenter_username is not None:
            self.find_or_create_experimenter(experiment, experimenter_username)

        # create contents
        for ref_video in self.dataset.ref_videos:
            Content(
                name=f"{self.dataset.dataset_name}-{ref_video['content_name']}",
                content_id=ref_video['content_id']).save()

        # create subjects and sessions
        if self.os_style == list:
            subjects = []
            sessions = []
            for subject_id in range(self.num_observers):
                subject = Subject(
                    name=f'{self.dataset.dataset_name}-#{subject_id}')
                subject.save()
                subjects.append(subject)

                session = Session(experiment=experiment, subject=subject)
                session.save()
                sessions.append(session)
        elif self.os_style == dict:
            subjects = []
            sessions = []
            for subject_name in self._get_list_observers():
                subject = Subject(
                    name=f'{self.dataset.dataset_name}-{subject_name}')
                subject.save()
                subjects.append(subject)

                session = Session(experiment=experiment, subject=subject)
                session.save()
                sessions.append(session)
        else:
            assert False

        # create stimuli
        stimuli = self._retrieve_or_create_stimuli()

        # create sg, svg
        sg_svg_cache = dict()
        for dis_video, stimulus in zip(self.dataset.dis_videos, stimuli):
            if stimulus.id in sg_svg_cache:
                # sg, svg = sg_svg_cache[stimulus.id]
                pass
            else:
                sg = StimulusGroup(stimulusgroup_id=stimulus.stimulus_id,
                                   experiment=experiment)
                sg.save()
                svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimulus(
                    stimulus,
                    stimulusgroup=sg,
                    stimulusvotegroup_id=stimulus.stimulus_id,
                    experiment=experiment)
                sg_svg_cache[stimulus.id] = (sg, svg)

        # create rounds
        for rid, (dis_video, stimulus) in enumerate(zip(self.dataset.dis_videos, stimuli)):
            assert len(subjects) == len(sessions)
            for session_id, session in enumerate(sessions):
                assert stimulus.id in sg_svg_cache
                sg, svg = sg_svg_cache[stimulus.id]
                rnd = Round(session=session, stimulusgroup=sg,
                            round_id=rid,
                            )
                rnd.save()

        # create votes
        for rid, (dis_video, stimulus) in enumerate(zip(self.dataset.dis_videos, stimuli)):
            os = dis_video['os']
            if self.os_style == list:
                assert isinstance(os, list)
                assert len(os) == len(subjects) == len(sessions)
                for score, session in zip(os, sessions):
                    if stimulus.id in sg_svg_cache:
                        sg, svg = sg_svg_cache[stimulus.id]
                    else:
                        sg = StimulusGroup(stimulusgroup_id=stimulus.stimulus_id,
                                           experiment=experiment)
                        sg.save()
                        svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimulus(
                            stimulus,
                            stimulusgroup=sg,
                            stimulusvotegroup_id=stimulus.stimulus_id,
                            experiment=experiment)
                        sg_svg_cache[stimulus.id] = (sg, svg)

                    rnd = Round.objects.get(session=session, stimulusgroup=sg,
                                            round_id=rid,
                                            )
                    vote = vote_class(score=score,
                                      round=rnd,
                                      stimulusvotegroup=svg)
                    vote.save()

            elif self.os_style == dict:
                assert isinstance(os, dict)
                for subject_name in os.keys():
                    for subject in subjects:
                        if subject.name == f'{self.dataset.dataset_name}-{subject_name}':
                            break
                    else:
                        assert False, \
                            f'no subject matches name {self.dataset.dataset_name}-{subject_name}'
                    session = Session.objects.get(experiment=experiment,
                                                  subject=subject)

                    if stimulus.id in sg_svg_cache:
                        sg, svg = sg_svg_cache[stimulus.id]
                    else:
                        sg = StimulusGroup(stimulusgroup_id=stimulus.stimulus_id,
                                           experiment=experiment)
                        sg.save()
                        svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimulus(
                            stimulus,
                            stimulusgroup=sg,
                            stimulusvotegroup_id=stimulus.stimulus_id,
                            experiment=experiment)

                        sg_svg_cache[stimulus.id] = (sg, svg)

                    rnd = Round.objects.get(session=session, stimulusgroup=sg,
                                            round_id=rid,
                                            )
                    vote = vote_class(score=os[subject_name],
                                      round=rnd,
                                      stimulusvotegroup=svg)
                    vote.save()

            else:
                assert False

    def get_stimulus_dict(self):
        contents = list()
        for ref_video in self.dataset.ref_videos:
            contents.append({
                'content_id': ref_video['content_id'],
                'name': ref_video['content_name'],
            })
        stimuli = list()
        stimulusvotegroups = list()
        stimulusgroups = list()
        for dis_video in self.dataset.dis_videos:
            stimuli.append({
                'path': dis_video['path'],
                'stimulus_id': dis_video['asset_id'],
                'type': 'video/mp4',  # hardcoded, don't use in real test config
                'content_id': dis_video['content_id'],
            })
            stimulusvotegroups.append({
                'stimulus_ids': [dis_video['asset_id']],
                'stimulusvotegroup_id': dis_video['asset_id'],
            })
            stimulusgroups.append({
                'stimulusvotegroup_ids': [dis_video['asset_id']],
                'stimulusgroup_id': dis_video['asset_id'],
            })
        return {'contents': contents,
                'stimuli': stimuli,
                'stimulusvotegroups': stimulusvotegroups,
                'stimulusgroups': stimulusgroups,
                }


class SurealPairedCompDatasetReaderPlus(SurealPairedCompDatasetReader, SurealMixin):
    """
    Extended paired comparison dataset reader that handles Sureal dataset
    format, and have extra capability such as populate NEST databases.
    """

    @override(SurealPairedCompDatasetReader)
    def _assert_dataset(self):
        super()._assert_dataset()

        assert hasattr(self.dataset, 'dataset_name')
        assert hasattr(self.dataset, 'ref_videos')
        assert isinstance(self.dataset.ref_videos, list)
        for ref_video in self.dataset.ref_videos:
            assert 'content_name' in ref_video
            assert 'content_id' in ref_video
            assert 'path' in ref_video
        assert hasattr(self.dataset, 'dis_videos')
        assert isinstance(self.dataset.dis_videos, list)
        self.os_style = None
        for dis_video in self.dataset.dis_videos:
            assert 'asset_id' in dis_video
            assert 'content_id' in dis_video
            assert 'os' in dis_video
            assert isinstance(dis_video['os'], dict)
            for key in dis_video['os'].keys():
                assert isinstance(key[0], str)
                assert isinstance(key[1], int)
            assert 'path' in dis_video

    @transaction.atomic
    def populate_nest(self, **more):

        assert 'vote_class' in more
        vote_class = more['vote_class']

        experimenter_username = more['experimenter_username'] \
            if 'experimenter_username' in more else None
        assert experimenter_username is None or \
               isinstance(experimenter_username, str)

        # create experiment, dataset
        try:
            experiment = Experiment(title=self.dataset.dataset_name)
            experiment.save()
        except IntegrityError:
            raise AssertionError(
                f'Experiment with title {self.dataset.dataset_name} exists.')

        if experimenter_username is not None:
            self.find_or_create_experimenter(experiment, experimenter_username)

        # create contents
        for ref_video in self.dataset.ref_videos:
            Content(
                name=f"{self.dataset.dataset_name}-{ref_video['content_name']}",
                content_id=ref_video['content_id']).save()

        # create subjects and sessions
        subjects = []
        sessions = []
        for subject_name in self._get_list_observers():
            subject = Subject(name=f'{self.dataset.dataset_name}-{subject_name}')
            subject.save()
            subjects.append(subject)

            session = Session(experiment=experiment, subject=subject)
            session.save()
            sessions.append(session)

        # create stimuli
        stimuli = self._retrieve_or_create_stimuli()

        # create rounds, sg, svg, votes
        d_subjname_to_rid = dict()
        sg_svg_cache = dict()
        sgid_count = 0
        for dis_video, stimulus in zip(self.dataset.dis_videos, stimuli):
            os = dis_video['os']
            assert isinstance(os, dict)
            for key in os.keys():
                subject_name, pc_stim_id = key
                for subject in subjects:
                    if subject.name == f'{self.dataset.dataset_name}-{subject_name}':
                        break
                else:
                    assert False, \
                        f'no subject matches name {self.dataset.dataset_name}-{subject_name}'
                session = Session.objects.get(
                    experiment=experiment, subject=subject)
                for stimulus_against in stimuli:
                    if stimulus_against.stimulus_id == pc_stim_id:
                        break
                else:
                    assert False, \
                        f'no stimulus matches stimulus_id {pc_stim_id}'

                if (stimulus.id, stimulus_against.id) in sg_svg_cache:
                    sg, svg = sg_svg_cache[(stimulus.id, stimulus_against.id)]
                else:
                    sg = StimulusGroup(stimulusgroup_id=sgid_count,
                                       experiment=experiment)
                    sg.save()
                    sgid_count += 1
                    svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
                        stimulus, stimulus_against,
                        stimulusgroup=sg,
                        stimulusvotegroup_id=sgid_count,
                        experiment=experiment)
                    sg_svg_cache[(stimulus.id, stimulus_against.id)] = (sg, svg)

                rnd = Round(session=session, stimulusgroup=sg,
                            round_id=d_subjname_to_rid.setdefault(session.subject.name, 0))
                d_subjname_to_rid[session.subject.name] += 1
                rnd.save()
                vote = vote_class(score=os[key],
                                  round=rnd,
                                  stimulusvotegroup=svg)
                vote.save()

    @property
    def ref_score(self):
        raise NotImplementedError

    @property
    def opinion_score_2darray(self):
        # return np.nansum(self.opinion_score_3darray, axis=1)
        raise NotImplementedError

    def to_persubject_dataset(self, quality_scores, **kwargs):
        raise NotImplementedError

    def get_stimulusgroups(self):
        raise NotImplementedError


def import_sureal_dataset(dataset, scale, **more):
    vote_class = Vote.find_subclass(scale)
    try:
        dataset_reader = SurealPairedCompDatasetReaderPlus(dataset)
    except AssertionError:
        dataset_reader = SurealRawDatasetReaderPlus(dataset)

    dataset_reader.populate_nest(vote_class=vote_class, **more)

    write_config = more['write_config'] if 'write_config' in more else False
    assert isinstance(write_config, bool)
    if write_config:
        config_filedir = more['config_filedir'] if 'config_filedir' in more \
            else NestConfig.media_path('experiment_config')
        sd = dataset_reader.get_stimulus_dict()
        assert 'contents' in sd
        assert 'stimuli' in sd
        assert 'stimulusvotegroups' in sd
        assert 'stimulusgroups' in sd
        config = dataset_reader.make_experiment_config_dict(
            sd['contents'],
            sd['stimuli'],
            sd['stimulusvotegroups'],
            sd['stimulusgroups'],
            seed=None
        )
        config_filepath = os.path.join(
            config_filedir, f"{dataset_reader.dataset.dataset_name}.json")
        os.makedirs(os.path.dirname(config_filepath), exist_ok=True)
        with open(config_filepath, "wt") as fp:
            json.dump(config, fp, indent=4)


def export_sureal_dataset(experiment_title, ignore_against: bool = False):  # noqa C901
    """
    ignore_against: set True if the experiment methodology is DCR or SAMVIQ,
    with which Sureal format does not have Reference as "against"
    """
    dataset = empty_object()

    experiment = Experiment.objects.get(title=experiment_title)

    try:
        config = NestSite._load_experiment_config2(experiment_title, is_test=False)
        ec = NestSite._get_experiment_controller2(experiment, config)
    except FileNotFoundError:
        ec = None

    sessions = Session.objects.filter(experiment=experiment).all()

    ref_video_dict = dict()  # dict: content_id -> ref_video
    dis_video_dict = dict()  # dict: asset_id -> dis_video

    os_dict_style = None  # either
    for session in sessions:

        # subject_name logic
        subject = session.subject
        subject_name = subject.get_subject_name()

        for rnd in session.round_set.all():
            if rnd.vote_set.count() == 0:
                continue
            vote: Vote
            for vote in rnd.vote_set.all():
                svg = StimulusVoteGroup.objects.get(vote=vote)
                vrs = VoteRegister.objects.filter(stimulusvotegroup=svg)
                assert vrs.count() == 1 or vrs.count() == 2, \
                    f'expect #stimuli to be either 1 or 2, but get {vrs.count()}'
                if vrs.count() == 1:
                    if os_dict_style is None:
                        os_dict_style = 'single'
                    else:
                        assert os_dict_style == 'single'

                    assert ignore_against is False, \
                        'cannot have os_dict_style single AND ignore_against ' \
                        'is False: there is nothing against'

                    vr = vrs.all()[0]
                    stimulus: Stimulus = vr.stimulus
                    content: Content = stimulus.content
                    if content.content_id not in ref_video_dict:
                        ref_video = {
                            'content_id': content.content_id,
                            'content_name': content.name,
                            'path': str(content.content_id),
                        }
                        ref_video_dict[content.content_id] = ref_video

                    if stimulus.stimulus_id not in dis_video_dict:
                        if ec is not None:
                            stim_dict = NestSite._get_matched_stimulus_dict(
                                ec, stimulus.stimulus_id)
                            path = stim_dict['path']
                        else:
                            path = str(stimulus.stimulus_id)
                        dis_video = {
                            'asset_id': stimulus.stimulus_id,
                            'content_id': content.content_id,
                            'os': dict(),
                            'path': path,
                        }
                        dis_video_dict[stimulus.stimulus_id] = dis_video

                    if subject_name in dis_video_dict[stimulus.stimulus_id]['os']:
                        if not isinstance(dis_video_dict[stimulus.stimulus_id]['os'][subject_name], list):
                            dis_video_dict[stimulus.stimulus_id]['os'][subject_name] = \
                                [dis_video_dict[stimulus.stimulus_id]['os'][subject_name]]
                        dis_video_dict[stimulus.stimulus_id]['os'][subject_name].append(vote.score)
                    else:
                        dis_video_dict[stimulus.stimulus_id]['os'][subject_name] = vote.score

                elif vrs.count() == 2:
                    if os_dict_style is None:
                        os_dict_style = 'double'
                    else:
                        assert os_dict_style == 'double'

                    vrs = vrs.order_by('stimulus_order')
                    assert vrs[0].stimulus_order == 1
                    assert vrs[1].stimulus_order == 2
                    stimulus = vrs[0].stimulus
                    stimulus_against = vrs[1].stimulus
                    content = stimulus.content
                    content_against = stimulus_against.content
                    if content.content_id not in ref_video_dict:
                        ref_video = {
                            'content_id': content.content_id,
                            'content_name': content.name,
                            'path': str(content.content_id),
                        }
                        ref_video_dict[content.content_id] = ref_video

                    if stimulus.stimulus_id not in dis_video_dict:
                        if ec is not None:
                            stim_dict = NestSite._get_matched_stimulus_dict(
                                ec, stimulus.stimulus_id)
                            path = stim_dict['path']
                        else:
                            path = str(stimulus.stimulus_id)
                        dis_video = {
                            'asset_id': stimulus.stimulus_id,
                            'content_id': content.content_id,
                            'os': dict(),
                            'path': path,
                        }
                        dis_video_dict[stimulus.stimulus_id] = dis_video

                    if stimulus_against.stimulus_id not in dis_video_dict:
                        if ec is not None:
                            stim_dict = NestSite._get_matched_stimulus_dict(
                                ec, stimulus_against.stimulus_id)
                            path = stim_dict['path']
                        else:
                            path = str(stimulus_against.stimulus_id)
                        dis_video = {
                            'asset_id': stimulus_against.stimulus_id,
                            'content_id': content_against.content_id,
                            'os': dict(),
                            'path': path,
                        }
                        dis_video_dict[stimulus_against.stimulus_id] = dis_video

                    if ignore_against is True:
                        if subject_name in dis_video_dict[stimulus.stimulus_id]['os']:
                            if not isinstance(dis_video_dict[stimulus.stimulus_id]['os'][subject_name], list):
                                dis_video_dict[stimulus.stimulus_id]['os'][subject_name] = \
                                    [dis_video_dict[stimulus.stimulus_id]['os'][subject_name]]
                            dis_video_dict[stimulus.stimulus_id]['os'][subject_name].append(vote.score)
                        else:
                            dis_video_dict[stimulus.stimulus_id]['os'][subject_name] = vote.score
                    else:
                        if (subject_name, stimulus_against.stimulus_id) in dis_video_dict[stimulus.stimulus_id]['os']:
                            if not isinstance(dis_video_dict[stimulus.stimulus_id]['os'][subject_name, stimulus_against.stimulus_id], list):
                                dis_video_dict[stimulus.stimulus_id]['os'][subject_name, stimulus_against.stimulus_id] = \
                                    [dis_video_dict[stimulus.stimulus_id]['os'][subject_name, stimulus_against.stimulus_id]]
                            dis_video_dict[stimulus.stimulus_id]['os'][subject_name, stimulus_against.stimulus_id].append(vote.score)
                        else:
                            dis_video_dict[stimulus.stimulus_id]['os'][subject_name, stimulus_against.stimulus_id] = vote.score

                else:
                    assert False

    dataset.dataset_name = experiment.title
    dataset.ref_videos = [ref_video_dict[content_id]
                          for content_id in sorted(ref_video_dict.keys())]
    dataset.dis_videos = [dis_video_dict[asset_id]
                          for asset_id in sorted(dis_video_dict.keys())]

    return dataset


class ExperimentUtils(object):

    @staticmethod
    def get_experiment_controller(experiment_title: str,
                                  config: dict = None,
                                  skip_path_check: bool = False) -> ExperimentController:
        if config is None:
            with open(NestConfig.media_path('experiment_config',
                                            f"{experiment_title}.json"),
                      "rt") as fp:
                config = json.load(fp)
        exp = Experiment.objects.get(title=experiment_title)
        assert isinstance(config, dict)
        assert 'stimulus_config' in config
        assert 'experiment_config' in config
        scfg = StimulusConfig(config['stimulus_config'],
                              skip_path_check=skip_path_check)
        ecfg = ExperimentConfig(stimulus_config=scfg,
                                config=config['experiment_config'])
        ec = ExperimentController(experiment=exp, experiment_config=ecfg)
        return ec

    @staticmethod
    def _create_experiment_from_config(
            source_config_filepath: str,
            is_test: bool = False,
            random_seed: int = None,
            experiment_title: str = None):

        if is_test:
            assert random_seed is not None and isinstance(random_seed, int)
            assert experiment_title is not None and isinstance(experiment_title, str)
        else:
            if random_seed is not None:
                assert isinstance(random_seed, int)
            if experiment_title is not None:
                assert isinstance(experiment_title, str)

        if experiment_title is None:
            with open(source_config_filepath, 'rt') as fp_source:
                config = json.load(fp_source)
            experiment_title = config['experiment_config']['title']

        target_config_filepath = NestSite.get_experiment_config_filepath(
            experiment_title, is_test=is_test)
        assert target_config_filepath != source_config_filepath
        os.makedirs(os.path.dirname(target_config_filepath), exist_ok=True)
        with open(source_config_filepath, 'rt') as fp_source:
            with open(target_config_filepath, 'wt') as fp_target:
                config = json.load(fp_source)
                if is_test:
                    config['experiment_config']['random_seed'] = random_seed
                    config['experiment_config']['title'] = experiment_title
                else:
                    if random_seed is not None:
                        config['experiment_config']['random_seed'] = random_seed
                    if experiment_title is not None:
                        config['experiment_config']['title'] = experiment_title
                json.dump(config, fp_target, indent=4)
        with open(target_config_filepath, 'rt') as fp:
            config = json.load(fp)
        if is_test:
            scfg = StimulusConfig(config['stimulus_config'], skip_path_check=True)
        else:
            scfg = StimulusConfig(config['stimulus_config'])
        ecfg = ExperimentConfig(stimulus_config=scfg,
                                config=config['experiment_config'])
        e = Experiment(title=config['experiment_config']['title'],
                       description=config['experiment_config']['description'])
        e.save()
        ec = ExperimentController(experiment=e, experiment_config=ecfg)
        ec.populate_stimuli()
        return ec

    @classmethod
    def validate_config(cls,
                        experiment_config_filepath: str):
        """
        Validate if the experiment config file is a good one.
        """

        # do not check validity of these fields
        round_context_default_d = {
            'title': None,
            'video': None, 'video_a': None, 'video_b': None,
            'button': None, 'button_a': None, 'button_b': None,
            'video_a_value': 0, 'video_b_value': 1,
            'videos': [None], 'video_ref': None,
            'buttons': [None], 'button_ref': None,
            'stimulusvotegroup_ids': [None],
            'stimulusvotegroup_id': 0,
        }

        with open(experiment_config_filepath, 'rt') as fp_source:
            config = json.load(fp_source)
        experiment_title = config['experiment_config']['title']
        try:
            Experiment.objects.get(title=experiment_title)
            raise AssertionError(
                f"Experiment with title {experiment_title} already exists.")
        except Experiment.DoesNotExist:
            pass
        scfg = StimulusConfig(config['stimulus_config'])
        ecfg = ExperimentConfig(
            stimulus_config=scfg,
            config=config['experiment_config'])
        PageClass = map_methodology_to_page_class(ecfg.methodology)
        d = dict()
        d.update(round_context_default_d)
        d.update(ecfg.round_context)
        _ = PageClass(d)
        VoteClass = Vote.find_subclass(ecfg.vote_scale)
        if 'choices' in d and issubclass(VoteClass, DiscreteVote):
            assert len(d['choices']) == len(VoteClass.support), \
                f"the length of choices ({len(d['choices'])}) does not match " \
                f"vote_scale {ecfg.vote_scale}"

    @classmethod
    def create_experiment(cls,
                          experiment_config_filepath: str,
                          experimenter_username: str,
                          is_test: bool = False,
                          random_seed: int = None,
                          experiment_title: str = None,
                          ):
        """
        Create a new experiment from config file specified by
        experiment_config_filepath, with the experimenter associated with
        experimenter_username.
        """
        ec: ExperimentController = cls._create_experiment_from_config(
            source_config_filepath=experiment_config_filepath,
            is_test=is_test,
            random_seed=random_seed,
            experiment_title=experiment_title)

        exper = Experimenter.find_by_username(experimenter_username)
        if exper is None:
            exper = Experimenter.create_by_username(experimenter_username)
        ExperimentRegister.objects.create(experiment=ec.experiment,
                                          experimenter=exper)

        return ec

    @classmethod
    def delete_experiment_by_title(cls,
                                   experiment_title: str = None,
                                   is_test: bool = False,
                                   ):
        """
        Delete an experiment by experiment_title, through cleaning up the
        relevant objects in the DB and removing the config file.
        """
        target_config_filepath = NestSite.get_experiment_config_filepath(
            experiment_title, is_test=is_test)
        assert os.path.exists(target_config_filepath)
        exp: Experiment = Experiment.objects.get(title=experiment_title)
        exp.delete()
        os.remove(target_config_filepath)

    @classmethod
    def add_session_to_experiment(cls,
                                  experiment_title: str,
                                  subject_username: str,
                                  config: dict = None,
                                  skip_path_check: bool = False) -> Session:
        """
        Add a new session (Not started) to experiment with experiment_title,
        assigning to a subject with username. config default to None and should
        be read from a config file, and is only supplied for testing purpose.
        skip_path_check is True only for testing purpose.
        """
        ec = cls.get_experiment_controller(experiment_title, config, skip_path_check)

        subj = Subject.find_by_username(subject_username)
        if subj is None:
            subj = Subject.create_by_username(subject_username)
        return ec.add_session(subj)

    @classmethod
    def delete_session_by_id(cls,
                             session_id: int,
                             experiment_title: str,
                             config: dict = None,
                             skip_path_check: bool = False):
        """
        Delete a session by a session ID. config default to None and should
        be read from a config file, and is only supplied for testing purpose.
        skip_path_check is True only for testing purpose.
        """
        ec = cls.get_experiment_controller(experiment_title, config, skip_path_check)
        ec.delete_session(session_id)

    @classmethod
    def update_subject_for_session(cls,
                                   experiment_title: str,
                                   session_id: int,
                                   subject_username: str,
                                   config: dict = None,
                                   skip_path_check: bool = False):
        """
        Update the subject of the n-th session of an experiment with
        experiment_title, assigned to a subject with username. function
        is mainly for testing purpose.
        """
        ec = cls.get_experiment_controller(experiment_title, config,
                                           skip_path_check=skip_path_check)

        subj = Subject.find_by_username(subject_username)
        if subj is None:
            subj = Subject.create_by_username(subject_username)
        sess: Session = ec.experiment.session_set.get(id=session_id)
        sess.subject = subj
        sess.save()

    @classmethod
    def reset_unfinished_session(cls,
                                 experiment_title: str,
                                 session_id: int,
                                 config: dict = None,
                                 skip_path_check: bool = False):
        """
        Reset an unfinished session. config dict not None is only for testing
        purpose. skip_path_check True only for testing purpose.
        """
        ec: ExperimentController = \
            cls.get_experiment_controller(experiment_title,
                                          config, skip_path_check)
        sess: Session = ec.experiment.session_set.get(id=session_id)
        assert ec.get_session_status(sess) == SessionStatus.PARTIALLY_FINISHED
        return ec.reset_session(sess)


class ESUtilities(object):

    @staticmethod
    def export_playlist_ES_noise_study_style(
            ec: ExperimentController,
            shuffle_intervals: bool = False,
            methodology: Optional[str] = None,
    ) -> pd.DataFrame:

        assert methodology is None or methodology in ['samviq']

        stimuli_info = ec.get_stimuli_info()
        assert 'contents' in stimuli_info
        assert 'stimuli' in stimuli_info
        assert 'stimulusvotegroups' in stimuli_info
        assert 'stimulusgroups' in stimuli_info

        # build dict of dict:
        dd_s = dict(zip([s['stimulus_id'] for s in stimuli_info['stimuli']], stimuli_info['stimuli']))
        dd_svg = dict(zip([s['stimulusvotegroup_id'] for s in stimuli_info['stimulusvotegroups']], stimuli_info['stimulusvotegroups']))

        rows = list()
        session: Session
        for session in ec.experiment.session_set.all():
            sess_info: dict = ec.get_session_info(session)
            assert 'subject' in sess_info
            assert 'rounds' in sess_info
            rd: dict
            for rd in sess_info['rounds']:
                assert 'round_id' in rd
                assert 'stimulusvotegroups' in rd

                if methodology is None:
                    svgds: list = rd['stimulusvotegroups']

                    assert len(svgds) == 1, f'currently expect only one svg per round if methodology is None, but {svgds}'

                    svgd: dict
                    for svgd in svgds:  # prepared for generalization beyond len(svgds) == 1
                        assert 'stimulusvotegroup_id' in svgd
                        d_svg: dict = dd_svg[svgd['stimulusvotegroup_id']]
                        assert 'stimulus_ids' in d_svg
                        sids = d_svg['stimulus_ids']

                        if shuffle_intervals is True:
                            random.shuffle(sids)
                        for isid, sid in enumerate(sids):
                            d_s: dict = dd_s[sid]
                            assert 'path' in d_s
                            assert 'content_id' in d_s
                            filename = d_s['path']
                            noise_level = map_path_to_noise_rmse(os.path.basename(filename))

                            row = {
                                'participant_id': sess_info['subject'],
                                'content': d_s['content_id'],
                                'noise_level': noise_level,
                                'interval': string.ascii_uppercase[isid],
                                'trial': rd['round_id'],
                                'Filename': filename,
                            }
                            rows.append(row)
                elif methodology == 'samviq':
                    svgds: list = rd['stimulusvotegroups']
                    assert len(svgds) > 1
                    if shuffle_intervals is True:
                        random.shuffle(svgds)
                    svgd: dict
                    enc_sids = list()
                    ref_sid = None
                    for svgd in svgds:
                        assert 'stimulusvotegroup_id' in svgd
                        d_svg: dict = dd_svg[svgd['stimulusvotegroup_id']]
                        assert 'stimulus_ids' in d_svg
                        sids = d_svg['stimulus_ids']
                        assert len(sids) == 2
                        enc_sid_, ref_sid_ = sids
                        if ref_sid is None:
                            ref_sid = ref_sid_
                        else:
                            assert ref_sid == ref_sid_
                        enc_sids.append(enc_sid_)
                    assert ref_sid is not None
                    assert len(enc_sids) == len(svgds)
                    for isid, sid in enumerate(enc_sids + [ref_sid]):
                        d_s: dict = dd_s[sid]
                        assert 'path' in d_s
                        assert 'content_id' in d_s
                        filename = d_s['path']
                        noise_level = map_path_to_noise_rmse(os.path.basename(filename))

                        row = {
                            'participant_id': sess_info['subject'],
                            'content': d_s['content_id'],
                            'noise_level': noise_level,
                            'interval': string.ascii_uppercase[isid],
                            'trial': rd['round_id'],
                            'Filename': filename,
                        }
                        rows.append(row)
                else:
                    assert False
        return pd.DataFrame(rows)

    @staticmethod
    def visualize_playlist_ES_style(ax, csv_filepath: str):
        import pprint
        df = pd.read_csv(csv_filepath, sep=',')
        # print(df)
        enc_filepaths = sorted(set(df['Filename']))
        dict_enc_filepaths = dict(zip(enc_filepaths, range(len(enc_filepaths))))
        subjects = sorted(set(df['participant_id']))
        dict_subjects = dict(zip(subjects, range(len(subjects))))
        mtx = np.ones([len(enc_filepaths), len(subjects)])
        for index, row in df.iterrows():
            mtx[dict_enc_filepaths[row['Filename']], dict_subjects[row['participant_id']]] = 0
        ax.imshow(mtx, interpolation='nearest', cmap='gray')
        ax.set_title(os.path.basename(csv_filepath))
        ax.set_ylabel('Stimulus')
        ax.set_xlabel('Subject')
        pprint.pprint(dict_subjects)
        pprint.pprint(dict_enc_filepaths)


class UserUtils(object):

    @staticmethod
    def create_user(username: str, is_staff: bool = False, is_superuser: bool = False) -> User:
        try:
            user = User.objects.get(username=username)
            touched = False
            if user.is_staff is False and is_staff is True:
                user.is_staff = True
                touched = True
            if user.is_superuser is False and is_superuser is True:
                user.is_superuser = True
                touched = True
            if touched:
                user.save()
        except User.DoesNotExist:
            user = User.objects.create_user(username=username,
                                            is_staff=is_staff,
                                            is_superuser=is_superuser)
        return user

    @staticmethod
    def set_password(username: str, password: str):
        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
        except User.DoesNotExist:
            logger.warning(f'user {username} does not exist; skip set_password')
