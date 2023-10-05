import datetime

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from nest.models import CcrThreePointVote, Condition, Content, ElevenPointVote, Experiment, Experimenter, \
    ExperimentRegister, FivePointVote, Round, Session, SevenPointVote, Stimulus, StimulusGroup, StimulusVoteGroup, \
    Subject, TafcVote, VoteRegister, Zero2HundredVote


class TestModels(TestCase):

    def test_saved(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        self.assertFalse(e.saved)
        e.save()
        self.assertTrue(e.saved)
        e2 = Experiment(title='Zhi ACR 2')
        e2.save()
        self.assertTrue(e2.saved)

    def test_deactivate(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        self.assertTrue(e.is_active)
        e.deactivate()
        self.assertFalse(e.is_active)

    def test_deactivate_past(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment",
                       deactivate_date=(timezone.now() -
                                        datetime.timedelta(days=1)))
        self.assertFalse(e.is_active)

    def test_deactivate_future(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment",
                       deactivate_date=(timezone.now() +
                                        datetime.timedelta(days=1)))
        self.assertTrue(e.is_active)

    def test_experiment(self):
        self.assertEqual(len(Experiment.objects.all()), 0)
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        self.assertEqual(len(Experiment.objects.all()), 0)
        e.save()
        self.assertEqual(len(Experiment.objects.all()), 1)
        self.assertEqual(e.title, 'Zhi ACR')
        self.assertEqual(e.description, "Zhi's ACR experiment")
        self.assertEqual(str(e), "Experiment 1 (Zhi ACR)")

    def test_experimenter(self):
        er = Experimenter(name='Zhi')
        er2 = Experimenter(name='Lukas')
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        er.save()
        er2.save()
        e.save()
        ExperimentRegister.objects.create(experiment=e, experimenter=er)
        ExperimentRegister.objects.create(experiment=e, experimenter=er2)
        self.assertEqual(e.experimenters.filter(id=er.id).count(), 1)
        self.assertEqual(e.experimenters.filter(id=er2.id).count(), 1)
        self.assertEqual(er.experiment_set.filter(id=e.id).count(), 1)
        self.assertEqual(er2.experiment_set.filter(id=e.id).count(), 1)
        er3 = Experimenter.find_by_username('Zhi')
        self.assertTrue(er3 is None)

        u = User.objects.create_user('lukas@catflix.com', password='abc123',
                                     is_staff=True)
        er3 = Experimenter(user=u)
        er3.save()
        er4 = Experimenter.find_by_username('lukas@catflix.com')
        self.assertTrue(er4 is not None)

    def test_experimenter_not_staff(self):
        user = User.objects.create_user('user', password='pass', is_staff=False)
        with self.assertRaises(AssertionError):
            Experimenter(name='Zhi', user=user)

    def test_experimenter_create_by_username(self):
        self.assertEqual(len(Experimenter.objects.all()), 0)
        self.assertEqual(len(Subject.objects.all()), 0)
        Experimenter.create_by_username('zli')
        self.assertEqual(len(Subject.objects.all()), 0)
        self.assertEqual(len(Experimenter.objects.all()), 1)
        self.assertEqual(len(User.objects.filter(username='zli', is_staff=True)), 1)
        self.assertEqual(len(User.objects.filter(username='zli', is_staff=False)), 0)
        with self.assertRaises(AssertionError):
            Experimenter.create_by_username('zli')
        Subject.create_by_username('zli')
        self.assertEqual(len(Subject.objects.all()), 1)

    def test_subject(self):
        self.assertEqual(len(Subject.objects.all()), 0)
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        self.assertEqual(str(s), 'Subject None (Lukas, lukas@catflix.com)')
        si.save()
        s.save()
        self.assertEqual(str(s), 'Subject 1 (Lukas, lukas@catflix.com)')
        si2 = User.objects.create_user('zhi@catflix.com', password='xyz456')
        s2 = Subject(name='Zhi', user=si2)
        si2.save()
        s2.save()
        self.assertEqual(len(Subject.objects.all()), 2)
        si3 = User(username='zhi@catflix.com', password='xyz789')
        with self.assertRaises(IntegrityError):
            si3.save()

    def test_subject_without_name(self):
        si4 = User.objects.create_user('lukas4@catflix.com', password='abc1234')
        s4 = Subject(user=si4)
        self.assertEqual(str(s4), 'Subject None (lukas4@catflix.com)')

    def test_subject_find_by_username(self):
        self.assertEqual(len(Subject.objects.all()), 0)
        u = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=u)
        s.save()
        s2 = Subject.find_by_username('lukas@catflix.com')
        self.assertEqual(str(s2), 'Subject 1 (Lukas, lukas@catflix.com)')
        s3 = Subject.find_by_username('zli@catflix.com')
        self.assertTrue(s3 is None)
        u2 = User.objects.create_user('zli@catflix.com', password='abc123')
        s4 = Subject.find_by_username('zli@catflix.com')
        self.assertTrue(s4 is None)
        s5 = Subject(name='zli', user=u2)
        s5.save()
        s6 = Subject.find_by_username('zli@catflix.com')
        self.assertTrue(s6 is not None)
        self.assertEqual(str(s6), 'Subject 2 (zli, zli@catflix.com)')

    def test_subject_create_by_username(self):
        self.assertEqual(len(Subject.objects.all()), 0)
        self.assertEqual(len(Experimenter.objects.all()), 0)
        Subject.create_by_username('zli')
        self.assertEqual(len(Subject.objects.all()), 1)
        self.assertEqual(len(User.objects.filter(username='zli')), 1)
        with self.assertRaises(AssertionError):
            Subject.create_by_username('zli')
        Experimenter.create_by_username('zli')
        self.assertEqual(len(Experimenter.objects.all()), 1)

    def test_session(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        si2 = User.objects.create_user('zhi@catflix.com', password='xyz456')
        s2 = Subject(name='Zhi', user=si2)
        sess = Session(experiment=e, subject=s)
        sess2 = Session(experiment=e, subject=s2)
        self.assertEqual(str(sess),
                         "Session None (Experiment None (Zhi ACR), "
                         "Subject None (Lukas, lukas@catflix.com))")
        e.save()
        si.save()
        s.save()
        si2.save()
        s2.save()
        sess.save()
        sess2.save()
        self.assertEqual(str(sess),
                         "Session 1 (Experiment 1 (Zhi ACR), Subject 1 (Lukas, "
                         "lukas@catflix.com))")
        self.assertEqual(str(sess2),
                         "Session 2 (Experiment 1 (Zhi ACR), Subject 2 (Zhi, "
                         "zhi@catflix.com))")
        self.assertEqual(e.session_set.count(), 2)
        self.assertEqual(s.session_set.count(), 1)
        self.assertEqual(s2.session_set.count(), 1)

    def test_session_delete(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        e.save()
        si.save()
        s.save()
        sess.save()
        Session.objects.get(id=1)
        Session.objects.get(id=1).delete()
        with self.assertRaises(Session.DoesNotExist):
            Session.objects.get(id=1)
        with self.assertRaises(Round.DoesNotExist):
            Round.objects.get(id=1)  # delete cascade: session -> round

    def test_experiment_delete(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        e.save()
        si.save()
        s.save()
        sess.save()
        Experiment.objects.get(id=1)
        Experiment.objects.get(id=1).delete()
        with self.assertRaises(Experiment.DoesNotExist):
            Experiment.objects.get(id=1)
        with self.assertRaises(Session.DoesNotExist):
            Session.objects.get(id=1)  # delete cascade: experiment -> session

    def test_subject_delete(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        e.save()
        si.save()
        s.save()
        sess.save()
        Subject.objects.get(id=s.id)
        Subject.objects.get(id=s.id).delete()
        with self.assertRaises(Subject.DoesNotExist):
            Subject.objects.get(id=s.id)
        sess2 = Session.objects.get(id=sess.id)
        # delete set null: subject -> session:
        self.assertEqual(sess2.subject, None)

    def test_round(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        r = Round(session=sess, response_sec=10)
        e.save()
        si.save()
        s.save()
        sess.save()
        r.save()
        self.assertEqual(str(r),
                         "Round 1 (Session 1 (Experiment 1 (Zhi ACR), "
                         "Subject 1 (Lukas, lukas@catflix.com)), None, None)")
        sg = StimulusGroup(stimulusgroup_id=3)
        sg.save()
        r2 = Round(session=sess, round_id=4, stimulusgroup=sg, response_sec=4)
        r2.save()
        self.assertEqual(str(r2),
                         "Round 2 (Session 1 (Experiment 1 (Zhi ACR), "
                         "Subject 1 (Lukas, lukas@catflix.com)), 4, 3)")
        self.assertEqual(r.response_sec, 10)
        self.assertEqual(r2.response_sec, 4)

    def test_content_dataset(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        e.save()
        c = Content(name='convex hull dataset sparks01', content_id=3, experiment=e)
        c.save()
        self.assertEqual(c.content_id, 3)
        self.assertEqual(c.experiment, e)
        Content.objects.get(id=c.id).delete()
        with self.assertRaises(Content.DoesNotExist):
            Content.objects.get(id=c.id)

    def test_stimulus(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        e.save()
        cont = Content(name='sparks01')
        cond = Condition(name='AVC-Hi 950Kbps', condition_id=1, experiment=e)
        self.assertEqual(cond.condition_id, 1)
        self.assertEqual(cond.experiment, e)
        stim = Stimulus(content=cont, condition=cond, stimulus_id=4, experiment=e)
        cont.save()
        cond.save()
        stim.save()
        self.assertEqual(stim.content, cont)
        self.assertEqual(stim.condition, cond)
        self.assertEqual(stim.experiment, e)
        self.assertEqual(stim.stimulus_id, 4)
        self.assertEqual(str(stim), "Stimulus 1 (Content 1 (sparks01, None), "
                                    "Condition 1 (AVC-Hi 950Kbps), 4)")
        Content.objects.get(id=cont.id).delete()
        Condition.objects.get(id=cond.id).delete()
        stim2 = Stimulus.objects.get(id=stim.id)
        # delete set null: content -> stimulus:
        self.assertEqual(stim2.content, None)
        # delete set null: condition -> stimulus:
        self.assertEqual(stim2.condition, None)

    def test_5point_vote(self):
        v = FivePointVote(score=5)
        v.save()
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        r = Round(session=sess, response_sec=5)
        v2 = FivePointVote(score=3, round=r)
        e.save()
        si.save()
        s.save()
        sess.save()
        r.save()
        v2.save()
        Experiment.objects.get(id=e.id).delete()
        with self.assertRaises(FivePointVote.DoesNotExist):
            # delete cascade: experiment -> session -> round -> vote:
            FivePointVote.objects.get(id=v2.id)

    def test_11point_vote(self):
        v = ElevenPointVote(score=11)
        v.save()
        with self.assertRaises(AssertionError):
            ElevenPointVote(score=0)

    def test_7point_vote(self):
        v = SevenPointVote(score=7)
        v.save()
        with self.assertRaises(AssertionError):
            SevenPointVote(score=0)

    def test_0to100_vote(self):
        v = Zero2HundredVote(score=50.1)
        v.save()
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        r = Round(session=sess)
        v2 = Zero2HundredVote(score=100.0, round=r)
        e.save()
        si.save()
        s.save()
        sess.save()
        r.save()
        v2.save()
        Experiment.objects.get(id=e.id).delete()
        with self.assertRaises(Zero2HundredVote.DoesNotExist):
            # delete cascade: experiment -> session -> round -> vote:
            Zero2HundredVote.objects.get(id=v2.id)

    def test_5p_vote_validation(self):
        FivePointVote(score=2)
        with self.assertRaises(AssertionError):
            FivePointVote(score=0)
        with self.assertRaises(AssertionError):
            FivePointVote(score=1.5)

    def test_2afc_vote_validation(self):
        TafcVote(score=0)
        with self.assertRaises(AssertionError):
            TafcVote(score=2)
        with self.assertRaises(AssertionError):
            TafcVote(score=1.5)

    def test_ccr3p_vote_validation(self):
        CcrThreePointVote(score=0)
        CcrThreePointVote(score=1)
        CcrThreePointVote(score=2)
        with self.assertRaises(AssertionError):
            CcrThreePointVote(score=0.5)
        with self.assertRaises(AssertionError):
            CcrThreePointVote(score=3)

    def test_0to100_vote_validation(self):
        Zero2HundredVote(score=45.9)
        with self.assertRaises(AssertionError):
            TafcVote(score=-1)
        with self.assertRaises(AssertionError):
            TafcVote(score=101.5)

    def test_sg_svg(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        e.save()

        stim1 = Stimulus()
        stim2 = Stimulus()
        stim1.save()
        stim2.save()
        sg = StimulusGroup(stimulusgroup_id=1, experiment=e)
        sg.save()
        svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim1, stim2,
            stimulusgroup=sg, stimulusvotegroup_id=1, experiment=e)
        self.assertEqual(str(sg), 'StimulusGroup 1 (1 : 1,2)')
        self.assertEqual(str(svg), 'StimulusVoteGroup 1 (1,2)')
        self.assertEqual(e.stimulusgroup_set.first(), sg)

        stim3 = Stimulus()
        stim3.save()
        svg2 = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim3, stim2,
            stimulusgroup=sg)
        self.assertEqual(str(sg), 'StimulusGroup 1 (1 : 1,2,3)')
        self.assertEqual(str(svg2), 'StimulusVoteGroup 2 (2,3)')

    def test_svg_without_sg(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        e.save()
        stim1 = Stimulus()
        stim2 = Stimulus()
        stim1.save()
        stim2.save()
        svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim1, stim2, stimulusvotegroup_id=1, experiment=e)

        self.assertEqual(str(svg), 'StimulusVoteGroup 1 (1,2)')
        self.assertTrue(svg.stimulusgroup is None)

        svg2 = StimulusVoteGroup.create_stimulusvotegroup_from_stimulus(
            stim2, stimulusvotegroup_id=1, experiment=e)

        self.assertEqual(str(svg2), 'StimulusVoteGroup 2 (2)')
        self.assertTrue(svg2.stimulusgroup is None)

    def test_5p_vote_stimuli(self):
        e = Experiment(title='Zhi ACR', description="Zhi's ACR experiment")
        si = User.objects.create_user('lukas@catflix.com', password='abc123')
        s = Subject(name='Lukas', user=si)
        sess = Session(experiment=e, subject=s)
        r = Round(session=sess)
        e.save()
        si.save()
        s.save()
        sess.save()
        r.save()

        stim1 = Stimulus()
        stim2 = Stimulus()
        stim1.save()
        stim2.save()

        # create svg with order (stim1, stim2)
        sg = StimulusGroup()
        sg.save()
        svg = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim1, stim2, sg)

        # create svg2 with order (stim2, stim1)
        sg2 = StimulusGroup()
        sg2.save()
        svg2 = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim2, stim1, sg2)

        # create svg3 with order (stim1, stim3)
        stim3 = Stimulus()
        stim3.save()
        sg3 = StimulusGroup()
        sg3.save()
        svg3 = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim1, stim3, sg3)

        self.assertEqual(svg.stimulus.filter(id=stim1.id).count(), 1)
        self.assertEqual(svg.stimulus.filter(id=stim2.id).count(), 1)
        self.assertEqual(stim1.stimulusvotegroup_set.filter(id=svg.id).count(), 1)
        self.assertEqual(stim2.stimulusvotegroup_set.filter(id=svg.id).count(), 1)
        self.assertEqual(VoteRegister.objects
                         .filter(stimulusvotegroup=svg, stimulus=stim1)[0].stimulus_order, 1)
        self.assertEqual(VoteRegister.objects
                         .filter(stimulusvotegroup=svg, stimulus=stim2)[0].stimulus_order, 2)
        self.assertEqual(VoteRegister.objects
                         .filter(stimulusvotegroup=svg, stimulus_order=1)[0].id, 1)
        self.assertEqual(VoteRegister.objects
                         .filter(stimulusvotegroup=svg, stimulus_order=2)[0].id, 2)

        svgs_ = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim1, stim2)
        self.assertEqual(len(svgs_), 1)
        self.assertEqual(svg, svgs_[0])

        svgs2_ = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim2, stim1)
        self.assertEqual(len(svgs2_), 1)
        self.assertEqual(svg2, svgs2_[0])

        svgs3_ = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim1, stim3)
        self.assertEqual(len(svgs3_), 1)
        self.assertEqual(svg3, svgs3_[0])

        # create sg4 and svg4 with order (stim1, stim2). This is to simulate the case
        # that stim, stim2 got reused by another experiment:
        sg4 = StimulusGroup()
        sg4.save()
        svg4 = StimulusVoteGroup.create_stimulusvotegroup_from_stimuli_pair(
            stim1, stim2,
            stimulusgroup=sg4, stimulusvotegroup_id=0, experiment=e)
        svgs4_ = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim1, stim2)
        self.assertEqual(len(svgs4_), 2)
        self.assertTrue(svg in svgs4_)
        self.assertTrue(svg4 in svgs4_)
        self.assertEqual(svg4.stimulusvotegroup_id, 0)
        self.assertEqual(svg4.experiment, e)

        # create another single-stimulus svg
        sg5 = StimulusGroup()
        sg5.save()
        svg5 = StimulusVoteGroup.create_stimulusvotegroup_from_stimulus(
            stim1,
            stimulusgroup=sg5, stimulusvotegroup_id=1, experiment=e)
        svgs5_ = StimulusVoteGroup.find_stimulusvotegroups_from_stimulus(stim1)
        self.assertEqual(len(svgs5_), 4)
        self.assertTrue(svg5 in svgs5_)
        self.assertTrue(svg in svgs5_)
        self.assertTrue(svg4 in svgs5_)
        self.assertTrue(svg3 in svgs5_)
        self.assertFalse(svg2 in svgs5_)
        self.assertEqual(svg5.stimulusvotegroup_id, 1)
        self.assertEqual(svg5.experiment, e)

        # re-check svgs4_
        svgs4_2 = StimulusVoteGroup.find_stimulusvotegroups_from_stimuli_pair(stim1, stim2)
        self.assertEqual(len(svgs4_2), 2)
        self.assertTrue(svg in svgs4_2)
        self.assertTrue(svg4 in svgs4_2)
