from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import List

from django.contrib.auth.models import User
from django.db import models, transaction
from django.utils import timezone
from polymorphic.models import PolymorphicModel

from .helpers import TypeVersionEnabled


class GenericModel(PolymorphicModel):
    """
    Abstract model that serves as the base class of other models derived.

    It has a created_date field that can be filled automatically with the the
    creation date, and a deactivate_date filed that is None by default,
    signaling that an object is active. Once deactivate_date is set to not None,
    it signals that the object is deactivated from the set date on.
    """
    create_date = models.DateTimeField('date created', default=timezone.now)
    deactivate_date = models.DateTimeField('date deactivated', null=True,
                                           default=None, blank=True)

    @property
    def is_active(self):
        """Returns if the object is currently active."""
        return (self.deactivate_date is None
                or timezone.now() < self.deactivate_date)

    def deactivate(self):
        """To deactivate the object."""
        self.deactivate_date = timezone.now()

    class Meta:
        abstract = True

    @property
    def saved(self):
        """Returns if the object is saved in database."""
        return not (self.pk is None)

    def __str__(self):
        return f"{self.__class__.__name__} {self.id}"


class Person(GenericModel):
    """Abtract class for a Person."""
    name = models.CharField('name', max_length=100, default="", blank=True)
    user: User = models.OneToOneField(User,
                                      null=True, blank=True,
                                      on_delete=models.SET_NULL)

    class Meta:
        abstract = True

    def __str__(self):
        s = super().__str__()
        disp_fields = []
        if self.name != "":
            disp_fields += [self.name]
        if self.user is not None:
            disp_fields += [str(self.user)]
        if len(disp_fields) > 0:
            s += f" ({', '.join(disp_fields)})"
        return s

    @classmethod
    def find_by_username(cls, username: str):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        try:
            person = cls.objects.get(user=user)
        except cls.DoesNotExist:
            return None
        return person


class Subject(Person):
    """Subject of an Experiment."""

    @classmethod
    @transaction.atomic
    def create_by_username(cls, username: str):
        """
        Create a new Subject object and associate it to a User of username.
        The method will try two things: 1) if the User exists, it will
        associate the new Subject to the User; 2) if the User does not exist,
        it will try to create a new User before association.
        """
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username)
        assert cls.objects.filter(user=user).count() == 0
        p = cls.objects.create(user=user)
        p.save()
        return p

    def get_subject_name(self):
        subject_name = self.name
        if subject_name == "":
            if self.user is not None:
                subject_name = self.user.username
        if subject_name == "":
            subject_name = str(self.id)
        return subject_name


class Experimenter(Person):
    """Experimenter of an Experiment."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.user is None or (self.user is not None and self.user.is_staff)

    @classmethod
    @transaction.atomic
    def create_by_username(cls, username: str):
        """
        Create a new Experimenter object and associate it to a User of username.
        The User must be is_staff. The method will try three things: 1) if the
        User exists, and is_staff, it will associate the new Experimenter to the
        User; 2) if the User exist but not is_staff, it will try to upgrade
        the User to is_staff before association; 3) if the User does not exist,
        it will try to create a new User which is_staff, before association.
        """
        try:
            user = User.objects.get(username=username, is_staff=True)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)
                user.is_staff = True
                user.save()
            except User.DoesNotExist:
                user = User.objects.create_user(username=username, is_staff=True)
        assert cls.objects.filter(user=user).count() == 0
        p = cls.objects.create(user=user)
        p.save()
        return p


class Experiment(GenericModel):
    """
    Experiment, each object typically consists of multiple Sessions, each
    Session run on a Subject.
    """
    title = models.CharField('experiment title',
                             max_length=200,
                             null=False, blank=False,
                             unique=True)
    description = models.TextField('experiment description',
                                   null=True, blank=True)
    experimenters = models.ManyToManyField(Experimenter,
                                           through='ExperimentRegister',
                                           blank=True)

    def __str__(self):
        return super().__str__() + f' ({self.title})'


class ExperimentRegister(GenericModel):
    """
    Register to associate an Experiment with an Experimenter.

    In NEST, the association between Experiment and Experimenter is
    many-to-many (an Experiment can be associated with more than one
    Experimenters, and an Experimenter can register multiple Experiments),
    and ExperimentRegister is the middle class to establish their
    association.
    """

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    experimenter = models.ForeignKey(Experimenter, on_delete=models.CASCADE)


class Session(GenericModel):
    """
    An continous interval within an Experiment, associated with one Subject.

    Multiple Sessions consist of an Experiment. A session must have one
    Subject, and may consists of multiple Rounds.
    """
    experiment: Experiment = models.ForeignKey(Experiment,
                                               on_delete=models.CASCADE)
    subject: Subject = models.ForeignKey(Subject,
                                         on_delete=models.SET_NULL,
                                         null=True, blank=True)

    def __str__(self):
        return super().__str__() + \
               f' ({str(self.experiment)}, {str(self.subject)})'


class Content(GenericModel):
    """
    A.k.a. source. The source material where a Stimulus can be created based on.

    For example, a piece of Content can be a 5-second video clip chosen from
    Stranger Things.
    """

    name = models.CharField('name', max_length=1000)
    content_id = models.IntegerField('content id', null=True, blank=True)
    experiment: Experiment = models.ForeignKey(Experiment,
                                               on_delete=models.CASCADE,
                                               null=True, blank=True)

    def __str__(self):
        return super().__str__() + f' ({self.name}, {self.content_id})'


class Condition(GenericModel):
    """
    A.k.a. HRC, or Hypothetical Reference Circuits.

    In subjective testing lingo, a Condition determines how the Content is
    presented to a Subject. For example, a Condition can be "encoding a video
    at 1000 Kbps, and decoded and displayed it on a screen which is three times
    the screen height from the Subject's eyes".
    """

    name = models.CharField('name', max_length=1000)
    condition_id = models.IntegerField('condition id', null=True, blank=True)
    experiment: Experiment = models.ForeignKey(Experiment,
                                               on_delete=models.CASCADE,
                                               null=True, blank=True)

    def __str__(self):
        return super().__str__() + f' ({self.name})'


class Stimulus(GenericModel):
    """
    A.k.a PVS: Processed Video Sequence.

    A Stimulus is determined by its Content and the Condition it is presented
    in.

    Note that 'path' and 'type' are present in stimulus_config.stimuli but are
    not fields for Stimulus purposely. The reason is that we want path be
    easily changed due to moving the media files around but the db doesn't
    needs to be updated every time.
    """

    content = models.ForeignKey(Content, on_delete=models.SET_NULL, null=True,
                                blank=True)
    condition = models.ForeignKey(Condition, on_delete=models.SET_NULL,
                                  null=True, blank=True)
    stimulus_id = models.IntegerField('stimulus id', null=True, blank=True)
    experiment: Experiment = models.ForeignKey(Experiment,
                                               on_delete=models.CASCADE,
                                               null=True, blank=True)

    def __str__(self):
        return (super().__str__() +
                f' ({self.content}, {self.condition}, {self.stimulus_id})')


class StimulusGroup(GenericModel):
    """
    One StimulusGroup contains multiple StimulusVoteGroups and is evaluated
    in each Round.
    """
    stimulusgroup_id = models.IntegerField('stimulus group id', null=True, blank=True)
    experiment: Experiment = models.ForeignKey(Experiment,
                                               on_delete=models.CASCADE,
                                               null=True, blank=True)

    @property
    def stimuli(self):
        stims = []
        for svg in StimulusVoteGroup.objects.filter(stimulusgroup=self):
            stims += svg.stimuli
        stims = sorted(set(stims), key=lambda x: x.id)
        return stims

    def __str__(self):
        return super().__str__() + f" ({self.stimulusgroup_id} : {','.join([str(stim.id) for stim in self.stimuli])})"


class StimulusVoteGroup(GenericModel):
    """
    A StimulusVoteGroup is a subset of a StimulusGroup. Each Vote is associated
    with a StimulusVoteGroup; each StimulusVoteGroup may have multiple votes.

    The relationship between StimulusVoteGroup and Stimulus is many-to-many:
    - Each Stimulus may belong to more than one StimulusVoteGroup.
    - Each StimulusVoteGroup may involve either one or two Stimuli, depending
    on if it is absolute (e.g. video A has “bad” quality) or relative scale
    (e.g. video A has “imperceptible” distortion compared to B). For the second
     case, the order matters, and this is preserved in the the VoteRegister
     (for example, if video A is order 1 and video B is order 2, then a vote
     of +1 represents that B is +1 better than A).
    """

    stimulus = models.ManyToManyField(Stimulus,
                                      through='VoteRegister',
                                      blank=True)
    stimulusgroup = models.ForeignKey(StimulusGroup,
                                      on_delete=models.CASCADE,
                                      null=True, blank=True)
    stimulusvotegroup_id = models.IntegerField('stimulus vote group id',
                                               null=True, blank=True)
    experiment: Experiment = models.ForeignKey(Experiment,
                                               on_delete=models.CASCADE,
                                               null=True, blank=True)

    @property
    def stimuli(self):
        stims = []
        for vr in VoteRegister.objects.filter(stimulusvotegroup=self):
            stims += [vr.stimulus]
        stims = sorted(set(stims), key=lambda x: x.id)
        return stims

    def __str__(self):
        return super().__str__() + f" ({','.join([str(stim.id) for stim in self.stimuli])})"

    @staticmethod
    def create_stimulusvotegroup_from_stimulus(stimulus: Stimulus,
                                               stimulusgroup: StimulusGroup = None,
                                               stimulusvotegroup_id: int = None,
                                               experiment: Experiment = None) -> StimulusVoteGroup:
        """
        create svg that corresponds to sg and a single stimulus
        """
        d = dict(stimulusgroup=stimulusgroup)
        if stimulusvotegroup_id is not None:
            d.update(dict(stimulusvotegroup_id=stimulusvotegroup_id))
        if experiment is not None:
            d.update(dict(experiment=experiment))

        svg = StimulusVoteGroup(**d)
        svg.save()
        VoteRegister.objects.create(
            stimulusvotegroup=svg,
            stimulus=stimulus,
        )
        return svg

    @staticmethod
    def find_stimulusvotegroups_from_stimulus(stim: Stimulus
                                              ) -> List[StimulusVoteGroup]:
        """
        find svgs that corresponds to single stimulus
        """

        svgs = StimulusVoteGroup.objects.filter(stimulus=stim)
        candidate_svgs = []
        for svg in svgs:
            vrs = VoteRegister.objects.filter(stimulus=stim,
                                              stimulus_order=1,
                                              stimulusvotegroup=svg)
            if vrs.count() > 0:
                assert vrs.count() == 1, \
                    f"expect a unique VoteRegister with svg and stim order 1," \
                    f" but got {vrs.count}: {vrs.all()}."
                candidate_svgs.append(svg)
        return candidate_svgs

    @staticmethod
    def create_stimulusvotegroup_from_stimuli_pair(stimulus1: Stimulus,
                                                   stimulus2: Stimulus,
                                                   stimulusgroup: StimulusGroup = None,
                                                   stimulusvotegroup_id: int = None,
                                                   experiment: Experiment = None) -> StimulusVoteGroup:
        """
        create svg that corresponds to sg and stimuli with order (stim1, stim2)
        """
        d = dict(stimulusgroup=stimulusgroup)
        if stimulusvotegroup_id is not None:
            d.update(dict(stimulusvotegroup_id=stimulusvotegroup_id))
        if experiment is not None:
            d.update(dict(experiment=experiment))
        svg = StimulusVoteGroup(**d)
        svg.save()
        VoteRegister.objects.create(
            stimulusvotegroup=svg,
            stimulus=stimulus1,
            stimulus_order=1,
        )
        VoteRegister.objects.create(
            stimulusvotegroup=svg,
            stimulus=stimulus2,
            stimulus_order=2,
        )
        return svg

    @staticmethod
    def find_stimulusvotegroups_from_stimuli_pair(stim1: Stimulus,
                                                  stim2: Stimulus
                                                  ) -> List[StimulusVoteGroup]:
        """
        find svgs that corresponds to stimuli with order (stim1, stim2)
        """

        # FIXME: the below logic seems convolved, although db_stress_test did
        #  not show much import/export time degradation as the db gets bigger
        svgs = (StimulusVoteGroup.objects.filter(stimulus=stim1)
                & StimulusVoteGroup.objects.filter(stimulus=stim2))
        candidate_svgs = []
        for svg in svgs:
            vrs = VoteRegister.objects.filter(stimulus=stim1,
                                              stimulus_order=1,
                                              stimulusvotegroup=svg)
            if vrs.count() > 0:
                assert vrs.count() == 1, \
                    f"expect a unique VoteRegister with svg and stim1 order 1 and " \
                    f"stim2 order 2, but got {vrs.count}: {vrs.all()}."
                candidate_svgs.append(svg)
        return candidate_svgs


class Round(GenericModel):
    """
    A short interval within a Session. It could be an interval where a Subject
    needs to evaluate the quality of a video Stimulus.
    """
    session: Session = models.ForeignKey(Session, on_delete=models.CASCADE)
    round_id: int = models.IntegerField('round id', null=True, blank=True)
    stimulusgroup: StimulusGroup = models.ForeignKey(StimulusGroup,
                                                     on_delete=models.SET_NULL,
                                                     null=True, blank=True)
    response_sec = models.FloatField('response sec', null=True, blank=True)

    def __str__(self):
        return super().__str__() + " ({}, {}, {})".format(
            self.session,
            self.round_id,
            self.stimulusgroup.stimulusgroup_id if
            self.stimulusgroup is not None else None
        )


class Vote(GenericModel, TypeVersionEnabled):
    """
    Abtract class for a Vote.

    It is associated with a Round of a Experiment Session, and can be
    associated with one (e.g. rate the quality of this video), two (e.g. rate
    the quality of the second video relative to the first video), or multiple
    (e.g. pick the best quality video from a list of videos) Stimuli.
    """
    round = models.ForeignKey(
        Round, on_delete=models.CASCADE,
        # the below are for convenience in tests since
        # don't want to create Round before creating Vote:
        null=True, blank=True,
    )
    stimulusvotegroup = models.ForeignKey(
        StimulusVoteGroup,
        on_delete=models.CASCADE,
        # the below are for convenience in tests since
        # don't want to create StimulusVoteGroup before
        # creating Vote:
        null=True, blank=True,
    )
    score = models.FloatField('score', null=False, blank=False)

    TYPE = 'VOTE'
    VERSION = '1.0'

    def __str__(self):
        return super().__str__() + f' ({self.score})'


class VoteRegister(GenericModel):
    """
    Register to associate a StimulusVoteGroup with a Stimulus.

    In NEST, the association between StimulusVoteGroup and Stimulus is
    many-to-many, and VoteRegister is the middle class to establish their
    association.

    For all the Stimuli associated with a StimulusVoteGroup, the order matters.
    For example, the first Stimulus is the reference and the second is the
    distorted, and the Vote associated with the StimulusVoteGroup is the
    quality of the distorted relative to the reference.
    """

    stimulusvotegroup = models.ForeignKey(StimulusVoteGroup, on_delete=models.CASCADE)
    stimulus = models.ForeignKey(Stimulus, on_delete=models.CASCADE)
    stimulus_order = models.PositiveIntegerField('stimulus order', default=1)


class DiscreteVote(Vote):
    """
    Abstract subclass of Vote, whose vote values come from a discrete set. For
    example, binary vote chosen from {0, 1}.
    """

    __metaclass__ = ABCMeta

    class Meta:
        abstract = True

    @property
    @abstractmethod
    def support(self):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'score' in kwargs:
            assert kwargs['score'] in self.support, \
                f"score {kwargs['score']} is not in the support {self.support}"

    @classmethod
    def assert_vote(cls, vote):
        assert vote in cls.support


class ContinuousVote(Vote):
    """
    Abstract subclass of Vote, whose vote values come from a continuous
    interval. For example, a real-value vote chosen in the interval of [0, 1].
    """

    __metaclass__ = ABCMeta

    class Meta:
        abstract = True

    @property
    @abstractmethod
    def range(self):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(self.range) == 2 and self.range[0] < self.range[
            1], f"illegal range {self.range}"
        if 'score' in kwargs:
            assert self.range[0] <= kwargs['score'] <= self.range[1], \
                f"score {kwargs['score']} is not in the range {self.range}"

    @classmethod
    def assert_vote(cls, vote):
        assert cls.range[0] <= vote <= cls.range[1]


class FivePointVote(DiscreteVote):
    """
    Discrete Vote from 1, 2, 3, 4, 5.
    """
    support = [1, 2, 3, 4, 5]
    TYPE = 'FIVE_POINT'


class TafcVote(DiscreteVote):
    """
    Two-alternative forced choice (2AFC) Vote from {0, 1}.
    """
    support = [0, 1]
    TYPE = '2AFC'


class Zero2HundredVote(ContinuousVote):
    """
    Continuous Vote from the interval [0, 100].
    """
    range = [0, 100]
    TYPE = '0_TO_100'


class ElevenPointVote(DiscreteVote):
    """
    Discrete Vote from 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
    """
    support = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    TYPE = 'ELEVEN_POINT'


class SevenPointVote(DiscreteVote):
    """
    Discrete Vote from 1, 2, 3, 4, 5, 6, 7
    """
    support = [1, 2, 3, 4, 5, 6, 7]
    TYPE = 'SEVEN_POINT'


class ThreePointVote(DiscreteVote):
    """
    Discrete Vote from 1, 2, 3
    """
    support = [1, 2, 3]
    TYPE = 'THREE_POINT'
