import json
import random

import numpy as np
from django.test import TestCase
from nest.config import ExperimentConfig, NestConfig, StimulusConfig
from nest.control import ExperimentController, SessionStatus
from nest.helpers import indices
from nest.models import Content, Experiment, Round, Session, Stimulus, \
    StimulusGroup, StimulusVoteGroup, Subject


class TestOrder(TestCase):

    def test_random_seed(self):
        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=[4, 3, 2, 1, 0],
            subject_id=1,
            ordering_so_far=list(),
            prioritized=list(),
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d, {0: 4,
                             1: 0,
                             2: 1,
                             3: 2,
                             4: 1,
                             5: 0,
                             6: 4,
                             7: 3})

    def test_super_sg(self):
        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=[4, 3, 2, 1, 0],
            subject_id=1,
            ordering_so_far=list(),
            prioritized=list(),
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
            super_stimulusgroup_ids=[0, 0, 0, 1, 1]
        )
        self.assertEqual(d, {0: 0,
                             1: 1,
                             2: 0,
                             3: 1,
                             4: 3,
                             5: 4,
                             6: 4,
                             7: 2})

    def test_partial_prioritized(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 4},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d, {0: 0,
                             1: 2,
                             2: 3,
                             3: 3,
                             4: 1,
                             5: 4,
                             6: 0,
                             7: 4})

    def test_partial_prioritized_super_sg(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 4},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
            super_stimulusgroup_ids=[0, 0, 0, 1, 1]
        )
        self.assertEqual(d, {0: 0,
                             1: 2,
                             2: 1,
                             3: 0,
                             4: 4,
                             5: 4,
                             6: 3,
                             7: 3})

    def test_partial_prioritized2(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': None, 'stimulusgroup_id': 0},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 0},
            {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 0},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=[4, 3, 2, 1, 0],
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        # 'round_id': None means it could randomly appear among the rounds
        self.assertEqual(d, {0: 4,
                             1: 3,
                             2: 1,
                             3: 2,
                             4: 0,
                             5: 0,
                             6: 4,
                             7: 1})

    def test_partial_prioritized2_super_sg(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': None, 'stimulusgroup_id': 0},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 0},
            {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 0},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=[4, 3, 2, 1, 0],
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
            super_stimulusgroup_ids=[0, 0, 0, 1, 1]
        )
        # 'round_id': None means it could randomly appear among the rounds
        self.assertEqual(d, {0: 4,
                             1: 2,
                             2: 3,
                             3: 4,
                             4: 1,
                             5: 0,
                             6: 1,
                             7: 0})

    def test_partial_prioritized3(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': None, 'stimulusgroup_id': 0},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 0},
            {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 0},
        ]
        blacklist_sgids = [0]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=[4, 3, 2, 1, 0],
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=blacklist_sgids,
        )
        # 'round_id': None means it could randomly appear among the rounds
        # included in blocklist_stimulusgroup_ids means it won't appears in
        # other rounds rather than specified in the prioritized list.
        # in this example, sg 0 appears once due to the second row of the
        # prioritized list, and then it's blocked for the rest of the rounds
        self.assertEqual(d, {0: 4,
                             1: 1,
                             2: 2,
                             3: 3,
                             4: 1,
                             5: 0,
                             6: 4,
                             7: 2})

    def test_partial_prioritized3_super_sg(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': None, 'stimulusgroup_id': 0},
            {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 0},
            {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 0},
        ]
        blacklist_sgids = [0]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=[4, 3, 2, 1, 0],
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=blacklist_sgids,
            super_stimulusgroup_ids=[0, 0, 0, 1, 1]
        )
        self.assertEqual(d, {0: 4,
                             1: 1,
                             2: 0,
                             3: 1,
                             4: 4,
                             5: 3,
                             6: 2,
                             7: 2})

    def test_full_prioritized(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
            {'session_idx': 0, 'round_id': 1, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 2, 'stimulusgroup_id': 2},
            {'session_idx': 0, 'round_id': 3, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 4, 'stimulusgroup_id': 2},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 6, 'stimulusgroup_id': 2},
            {'session_idx': 0, 'round_id': 7, 'stimulusgroup_id': 4},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d, {0: 0,
                             1: 4,
                             2: 2,
                             3: 4,
                             4: 2,
                             5: 4,
                             6: 2,
                             7: 4})

    def test_full_prioritized_super_sg(self):
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
            {'session_idx': 0, 'round_id': 1, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 2, 'stimulusgroup_id': 2},
            {'session_idx': 0, 'round_id': 3, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 4, 'stimulusgroup_id': 2},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 6, 'stimulusgroup_id': 2},
            {'session_idx': 0, 'round_id': 7, 'stimulusgroup_id': 4},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
            super_stimulusgroup_ids=[0, 0, 0, 1, 1]
        )
        self.assertEqual(d, {0: 0,
                             1: 4,
                             2: 2,
                             3: 4,
                             4: 2,
                             5: 4,
                             6: 2,
                             7: 4})

    def test_ordering_so_far(self):
        ordering_so_far = [
            {'subject': 0, 'stimulusgroups': {0: 1,
                                              1: 4,
                                              2: 4,
                                              3: 1,
                                              4: 2,
                                              5: 4,
                                              6: 3,
                                              7: 4}},
            {'subject': 1, 'stimulusgroups': {0: 0,
                                              1: 4,
                                              2: 2,
                                              3: 4,
                                              4: 2,
                                              5: 4,
                                              6: 2,
                                              7: 4}},
        ]
        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=2,
            ordering_so_far=ordering_so_far,
            prioritized=list(),
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d, {0: 3,
                             1: 1,
                             2: 1,
                             3: 0,
                             4: 3,
                             5: 2,
                             6: 4,
                             7: 0})

    def test_partial_prioritized_repeated_element(self):
        prioritized = [
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 3},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d, {0: 4,
                             1: 4,
                             2: 0,
                             3: 1,
                             4: 3,
                             5: 3,
                             6: 2,
                             7: 2})

    def test_partial_prioritized_training(self):
        # to set sg 0 as training:
        # 1) add it to the prioritized list
        # 2) mark it in the blocklist_stimulusgroup_ids,
        #    s.t. it won't appear elsewhere
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
            {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 4},
        ]

        d = ExperimentController._order(
            rounds_per_session=8,
            stimulusgroup_ids=list(range(5)),
            subject_id=1,
            ordering_so_far=list(),
            prioritized=prioritized,
            random_seed=3,
            blocklist_stimulusgroup_ids=[0],
        )
        self.assertEqual(d, {0: 0,
                             1: 2,
                             2: 4,
                             3: 3,
                             4: 1,
                             5: 4,
                             6: 2,
                             7: 3})

    def test_split_list_two_different_subjects(self):
        pl = list()
        d1 = ExperimentController._order(
            rounds_per_session=5,
            stimulusgroup_ids=list(range(10)),
            subject_id=1,
            ordering_so_far=pl,
            prioritized=list(),
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d1, {0: 9,
                              1: 7,
                              2: 2,
                              3: 3,
                              4: 4})
        pl.append({'subject': 1, 'stimulusgroups': d1})
        d2 = ExperimentController._order(
            rounds_per_session=5,
            stimulusgroup_ids=list(range(10)),
            subject_id=2,
            ordering_so_far=pl,
            prioritized=list(),
            random_seed=3,
            blocklist_stimulusgroup_ids=list(),
        )
        # exactly complementary to d1 as the assignment tries to equalize the
        # votes per sg
        self.assertEqual(d2, {0: 5,
                              1: 8,
                              2: 6,
                              3: 1,
                              4: 0})
        pl.append({'subject': 2, 'stimulusgroups': d2})

        d3a = ExperimentController._order(
            rounds_per_session=5,
            stimulusgroup_ids=list(range(10)),
            subject_id=2,  # repeated subject
            ordering_so_far=pl,
            prioritized=list(),
            random_seed=2,
            blocklist_stimulusgroup_ids=list(),
        )
        # exactly complementary to d2 as it's the same subject for a second
        # session and the assignment tries to avoid sg repetitions for the
        # subject
        self.assertEqual(d3a, {0: 9,
                               1: 2,
                               2: 7,
                               3: 4,
                               4: 3})

        # a different subject, the assignment should be random
        d3b = ExperimentController._order(
            rounds_per_session=5,
            stimulusgroup_ids=list(range(10)),
            subject_id=3,  # new subject
            ordering_so_far=pl,
            prioritized=list(),
            random_seed=2,
            blocklist_stimulusgroup_ids=list(),
        )
        self.assertEqual(d3b, {0: 2,
                               1: 0,
                               2: 5,
                               3: 4,
                               4: 3})

    def test_experiment_order_realistic(self):

        random.seed(0)

        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},  # training
            {'session_idx': None, 'round_id': 5, 'stimulusgroup_id': 1},  # reliability
            {'session_idx': None, 'round_id': 10, 'stimulusgroup_id': 1},  # reliability
        ]
        blacklist_sgids = [0, 1]
        num_sg = 102  # training + reliability + 100 sgs
        rounds_per_session = 37  # 100/3 ~= 34, plus 1 training, 2 reliability
        subj_ids = list(range(1, 25)) * 3  # 24 votes per sg, need 3 people to scan through sgs
        random.shuffle(subj_ids)

        pl = list()
        ds = list()
        seed = 0
        for subj_id in subj_ids:
            d = ExperimentController._order(
                rounds_per_session=rounds_per_session,
                stimulusgroup_ids=list(range(num_sg)),
                subject_id=subj_id,
                ordering_so_far=pl,
                prioritized=prioritized,
                random_seed=seed,
                blocklist_stimulusgroup_ids=blacklist_sgids,
            )
            pl.append({'subject': subj_id, 'stimulusgroups': d})
            ds.append(d)
            seed += 1

        # ll is 2d array with (session_id, round_id) -> sg_id
        ll = list()
        for d in ds:
            ll.append([d[rid] for rid in sorted(d.keys())])
        ll = np.vstack(ll)

        # sg_id of 0th session evaluated:
        self.assertEqual(
            list(ll[0, :]),
            [0, 81, 16, 71, 18, 1, 42, 36, 68, 61, 1, 98, 20, 70, 7, 38, 77,
             86, 60, 57, 50, 43, 40, 84, 88, 99, 24, 30, 53, 56, 51, 15, 12,
             100, 21, 101, 66]
        )

        # sg_id of last session evaluated:
        self.assertEqual(
            list(ll[-1, :]),
            [0, 53, 42, 31, 17, 1, 28, 91, 96, 35, 1, 52, 20, 85, 10, 62, 93,
             60, 59, 99, 63, 68, 37, 41, 67, 74, 49, 66, 55, 21, 22, 14, 23,
             29, 72, 78, 69]
        )

        # plm is 2d array with (session_id, sg_id) -> count of sg tested
        plm = np.zeros([len(subj_ids), num_sg])
        for sess_id, (subj_id, d) in enumerate(zip(subj_ids, ds)):
            for rid, sgid in d.items():
                plm[sess_id, sgid] += 1

        # number of votes per sg:
        self.assertEqual(
            list(np.sum(plm, axis=0)),
            [72.0, 144.0, 24.0, 24.0, 24.0, 24.0, 24.0, 24.0, 24.0, 24.0, 25.0,
             24.0, 25.0, 25.0, 26.0, 24.0, 24.0, 25.0, 26.0, 25.0, 24.0, 25.0,
             24.0, 24.0, 24.0, 24.0, 25.0, 24.0, 24.0, 25.0, 24.0, 25.0, 25.0,
             24.0, 25.0, 25.0, 25.0, 24.0, 24.0, 24.0, 24.0, 24.0, 26.0, 24.0,
             24.0, 25.0, 24.0, 25.0, 24.0, 25.0, 24.0, 24.0, 25.0, 26.0, 24.0,
             25.0, 26.0, 24.0, 25.0, 25.0, 25.0, 24.0, 24.0, 25.0, 24.0, 24.0,
             25.0, 25.0, 25.0, 24.0, 26.0, 24.0, 25.0, 24.0, 24.0, 24.0, 24.0,
             24.0, 24.0, 24.0, 24.0, 24.0, 24.0, 24.0, 26.0, 25.0, 24.0, 26.0,
             24.0, 25.0, 25.0, 24.0, 24.0, 25.0, 24.0, 24.0, 25.0, 24.0, 24.0,
             25.0, 24.0, 24.0]

        )

        # number of votes per session:
        self.assertEqual(
            list(np.sum(plm, axis=1)),
            [37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37.]
        )

        # number of times subject 1 (first subject) evaluated on each sg:
        self.assertEqual(
            list(np.sum(plm[indices(subj_ids, lambda x: x == 1), :], axis=0)),
            [3.0, 6.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        )

        # number of times subject 2 evaluated on each sg:
        self.assertEqual(
            list(np.sum(plm[indices(subj_ids, lambda x: x == 2), :], axis=0)),
            [3.0, 6.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 2.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        )

        # number of times subject 24 (last subject) evaluated on each sg:
        self.assertEqual(
            list(np.sum(plm[indices(subj_ids, lambda x: x == 24), :], axis=0)),
            [3.0, 6.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        )

    def test_experiment_order_realistic_decoy_in_random_round(self):

        random.seed(0)

        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},  # training
            {'session_idx': None, 'round_id': None, 'stimulusgroup_id': 1},  # reliability
        ]
        blacklist_sgids = [0, 1]
        num_sg = 102  # training + reliability + 100 sgs
        rounds_per_session = 37  # 100/3 ~= 34, plus 1 training, 2 reliability
        subj_ids = list(range(1, 25)) * 3  # 24 votes per sg, need 3 people to scan through sgs
        random.shuffle(subj_ids)

        pl = list()
        ds = list()
        seed = 0
        for subj_id in subj_ids:
            d = ExperimentController._order(
                rounds_per_session=rounds_per_session,
                stimulusgroup_ids=list(range(num_sg)),
                subject_id=subj_id,
                ordering_so_far=pl,
                prioritized=prioritized,
                random_seed=seed,
                blocklist_stimulusgroup_ids=blacklist_sgids,
            )
            pl.append({'subject': subj_id, 'stimulusgroups': d})
            ds.append(d)
            seed += 1

        # ll is 2d array with (session_id, round_id) -> sg_id
        ll = list()
        for d in ds:
            ll.append([d[rid] for rid in sorted(d.keys())])
        ll = np.vstack(ll)

        # sg_id of 0th session evaluated:
        self.assertEqual(
            list(ll[0, :]),
            [0, 36, 30, 101, 50, 7, 21, 93, 51, 15, 57, 38, 61, 81, 42, 77, 71,
             18, 53, 68, 70, 20, 98, 66, 40, 88, 16, 99, 86, 12, 24, 100, 1,
             56, 43, 60, 84]
        )

        # sg_id of last session evaluated:
        self.assertEqual(
            list(ll[-1, :]),
            [0, 84, 77, 80, 72, 64, 23, 15, 66, 44, 83, 13, 38, 82, 59, 3, 45,
             7, 91, 42, 97, 58, 98, 21, 1, 78, 16, 11, 94, 20, 25, 47, 68, 62,
             55, 96, 60]
        )

        # plm is 2d array with (session_id, sg_id) -> count of sg tested
        plm = np.zeros([len(subj_ids), num_sg])
        for sess_id, (subj_id, d) in enumerate(zip(subj_ids, ds)):
            for rid, sgid in d.items():
                plm[sess_id, sgid] += 1

        # number of votes per sg:
        self.assertEqual(
            list(np.sum(plm, axis=0)),
            [72.0, 72.0, 25.0, 25.0, 25.0, 25.0, 24.0, 25.0, 25.0, 25.0, 25.0,
             25.0, 25.0, 25.0, 25.0, 26.0, 25.0, 25.0, 25.0, 25.0, 26.0, 25.0,
             26.0, 25.0, 25.0, 26.0, 26.0, 25.0, 25.0, 26.0, 25.0, 27.0, 25.0,
             26.0, 25.0, 25.0, 26.0, 25.0, 25.0, 26.0, 25.0, 25.0, 26.0, 25.0,
             25.0, 25.0, 24.0, 26.0, 25.0, 25.0, 25.0, 25.0, 27.0, 25.0, 25.0,
             25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0,
             25.0, 25.0, 25.0, 25.0, 25.0, 26.0, 26.0, 25.0, 25.0, 25.0, 25.0,
             26.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 26.0, 25.0, 25.0, 24.0,
             25.0, 27.0, 25.0, 25.0, 25.0, 26.0, 25.0, 25.0, 25.0, 25.0, 26.0,
             25.0, 25.0, 25.0]
        )

        # number of votes per session:
        self.assertEqual(
            list(np.sum(plm, axis=1)),
            [37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37., 37.,
             37., 37., 37., 37., 37., 37., 37.]
        )

        # number of times subject 1 (first subject) evaluated on each sg:
        self.assertEqual(
            list(np.sum(plm[indices(subj_ids, lambda x: x == 1), :], axis=0)),
            [3.0, 3.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0,
             1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
             1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        )


class TestExperimentController(TestCase):

    @staticmethod
    def _populate_stimulusgroups(ec: ExperimentController):
        sg: dict
        for sg in ec.experiment_config.stimulus_config.stimulusgroups:
            StimulusGroup.objects.create(
                experiment=ec.experiment,
                stimulusgroup_id=sg['stimulusgroup_id'])

    def test_exp_order(self):
        e = Experiment(
            title='Zhi ACR',
            description="Zhi's ACR experiment",
        )
        e.save()
        scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4",  # noqa E501
                    "stimulus_id": 1,
                    "type": "video/mp4",
                    "content_id": 0,
                }
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
                {
                    "stimulus_ids": [
                        1
                    ],
                    "stimulusvotegroup_id": 1
                }
            ],
            'stimulusgroups': [
                {'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [1]},
                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0]},
                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 5, 'stimulusvotegroup_ids': [0]},
            ],
        })
        pcfg = ExperimentConfig(
            stimulus_config=scfg,
            config={
                'title': 'test',
                'description': 'test',
                "methodology": "acr",
                'vote_scale': 'FIVE_POINT',
                'rounds_per_session': 8,
                'random_seed': 3,
                'prioritized': [
                    {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
                    {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 5},
                    {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 5},
                    {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 5},
                ]
            })
        ec = ExperimentController(experiment=e, experiment_config=pcfg)
        self.assertEqual(ec.experiment.title, 'Zhi ACR')

        stimulusgroups = ec.get_and_assert_current_stimulusgroups()
        self.assertEqual(len(stimulusgroups), 0)

        self._populate_stimulusgroups(ec)

        s = Subject()
        s.save()
        sess = ec.add_session(s)
        stimulusgroups = ec.get_and_assert_current_stimulusgroups()
        self.assertEqual(stimulusgroups[0].round_set.count(), 2)
        self.assertEqual(stimulusgroups[1].round_set.count(), 2)
        self.assertEqual(stimulusgroups[2].round_set.count(), 1)
        self.assertEqual(stimulusgroups[3].round_set.count(), 1)
        self.assertEqual(stimulusgroups[4].round_set.count(), 2)
        self.assertEqual(sess.subject, s)

        s2 = Subject()
        s2.save()
        ec.add_session(s2)
        self.assertEqual(stimulusgroups[0].round_set.count(), 4)
        self.assertEqual(stimulusgroups[1].round_set.count(), 3)
        self.assertEqual(stimulusgroups[2].round_set.count(), 3)
        self.assertEqual(stimulusgroups[3].round_set.count(), 2)
        self.assertEqual(stimulusgroups[4].round_set.count(), 4)

        sinfo = ec.get_session_info(sess)
        self.assertEqual(
            sinfo,
            {'session_id': 1, 'subject': '1',
             'rounds': [
                 {'round_id': 0, 'stimulusgroup_id': 0, 'stimulusvotegroups': []},
                 {'round_id': 5, 'stimulusgroup_id': 5, 'stimulusvotegroups': []},
                 {'round_id': 1, 'stimulusgroup_id': 0, 'stimulusvotegroups': []},
                 {'round_id': 2, 'stimulusgroup_id': 4, 'stimulusvotegroups': []},
                 {'round_id': 3, 'stimulusgroup_id': 3, 'stimulusvotegroups': []},
                 {'round_id': 4, 'stimulusgroup_id': 2, 'stimulusvotegroups': []},
                 {'round_id': 6, 'stimulusgroup_id': 5, 'stimulusvotegroups': []},
                 {'round_id': 7, 'stimulusgroup_id': 4, 'stimulusvotegroups': []}]
             })

        stiminfo = ec.get_stimuli_info()
        self.assertEqual(
            stiminfo,
            {'contents': [{'content_id': 0, 'name': 'CTS3E1_B__15_55_16_0'}],
             'stimuli': [{'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4', 'stimulus_id': 0, 'type': 'video/mp4', 'content_id': 0},  # noqa E501
                         {'path': '/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4', 'stimulus_id': 1, 'type': 'video/mp4', 'content_id': 0}],  # noqa E501
             'stimulusvotegroups': [{'stimulus_ids': [0], 'stimulusvotegroup_id': 0},
                                    {'stimulus_ids': [1], 'stimulusvotegroup_id': 1}],
             'stimulusgroups': [{'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0]},
                                {'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [1]},
                                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0]},
                                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0]},
                                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 5, 'stimulusvotegroup_ids': [0]}]}
        )

    def test_exp_order_realistic(self):

        random_seed = 0

        random.seed(random_seed)
        prioritized = [
            {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},  # training
            {'session_idx': None, 'round_id': 5, 'stimulusgroup_id': 1},  # reliability
            {'session_idx': None, 'round_id': 10, 'stimulusgroup_id': 1},  # reliability
        ]
        blacklist_sgids = [0, 1]
        num_sg = 42  # training + reliability + 40 sgs
        rounds_per_session = 30
        subj_ids = list(range(1, 21)) * 2
        random.shuffle(subj_ids)

        # (30 - 3) = 27 votes / session
        # 20 * 2 = 40 sessions
        # total number of votes = 27 * 40 = 1080
        # total number of test sgs = 40
        # average votes per sg = 1080 / 40 = 27

        for sid in range(1, 21):
            s = Subject()
            s.save()

        e = Experiment(
            title='Zhi ACR 2',
            description="Zhi's ACR experiment",
        )
        e.save()

        scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
            ],
            'stimulusgroups': [{'stimulusgroup_id': sgid,
                                'stimulusvotegroup_ids': [0]}
                               for sgid in range(num_sg)]
        })
        pcfg = ExperimentConfig(
            stimulus_config=scfg,
            config={
                'title': 'test',
                'description': 'test',
                "methodology": "acr",
                'vote_scale': 'FIVE_POINT',
                'rounds_per_session': rounds_per_session,
                'random_seed': random_seed,
                'prioritized': prioritized,
                'blocklist_stimulusgroup_ids': blacklist_sgids,
            })
        ec = ExperimentController(experiment=e, experiment_config=pcfg)

        self._populate_stimulusgroups(ec)

        for session_id, subj_id in enumerate(subj_ids):
            # print(f"add session {session_id} for subject {subj_id}")
            s = Subject.objects.get(id=subj_id)
            ec.add_session(s)

        stimulusgroups = ec.get_and_assert_current_stimulusgroups()
        self.assertEqual(len(stimulusgroups), 42)

        self.assertEqual(StimulusGroup.objects.get(stimulusgroup_id=0).round_set.count(), 40)
        self.assertEqual(StimulusGroup.objects.get(stimulusgroup_id=1).round_set.count(), 80)
        self.assertEqual(StimulusGroup.objects.get(stimulusgroup_id=2).round_set.count(), 27)
        self.assertEqual(StimulusGroup.objects.get(stimulusgroup_id=3).round_set.count(), 27)
        self.assertEqual(StimulusGroup.objects.get(stimulusgroup_id=40).round_set.count(), 27)
        self.assertEqual(StimulusGroup.objects.get(stimulusgroup_id=41).round_set.count(), 26)

        # test on ExperimentController._populate_stimulus_info():
        # retrieve sg instead of creating
        eo2 = ExperimentController(experiment=e, experiment_config=pcfg)

        stimulusgroups = eo2.get_and_assert_current_stimulusgroups()
        self.assertEqual(len(stimulusgroups), 42)

    def test_session_status(self):
        e = Experiment(
            title='Zhi ACR',
            description="Zhi's ACR experiment",
        )
        e.save()
        scfg = StimulusConfig({
            "contents": [
                {
                    "content_id": 0,
                    "name": "CTS3E1_B__15_55_16_0",
                }
            ],
            "stimuli": [
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4",  # noqa E501
                    "stimulus_id": 0,
                    "type": "video/mp4",
                    "content_id": 0,
                },
                {
                    "path": "/media/mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4",  # noqa E501
                    "stimulus_id": 1,
                    "type": "video/mp4",
                    "content_id": 0,
                }
            ],
            "stimulusvotegroups": [
                {
                    "stimulus_ids": [
                        0
                    ],
                    "stimulusvotegroup_id": 0
                },
                {
                    "stimulus_ids": [
                        1
                    ],
                    "stimulusvotegroup_id": 1
                }
            ],
            'stimulusgroups': [
                {'info': {'flavors': ['training']}, 'stimulusgroup_id': 0, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 4, 'stimulusvotegroup_ids': [1]},
                {'stimulusgroup_id': 2, 'stimulusvotegroup_ids': [0]},
                {'stimulusgroup_id': 3, 'stimulusvotegroup_ids': [0]},
                {'info': {'flavors': ['decoy']}, 'stimulusgroup_id': 5, 'stimulusvotegroup_ids': [0]},
            ],
        })
        pcfg = ExperimentConfig(
            stimulus_config=scfg,
            config={
                'title': 'test',
                'description': 'test',
                "methodology": "acr",
                'vote_scale': 'FIVE_POINT',
                'rounds_per_session': 8,
                'random_seed': 3,
                'prioritized': [
                    {'session_idx': None, 'round_id': 0, 'stimulusgroup_id': 0},
                    {'session_idx': 0, 'round_id': 5, 'stimulusgroup_id': 5},
                    {'session_idx': 1, 'round_id': 5, 'stimulusgroup_id': 5},
                    {'session_idx': 2, 'round_id': 5, 'stimulusgroup_id': 5},
                ]
            })
        ec = ExperimentController(experiment=e, experiment_config=pcfg)

        self._populate_stimulusgroups(ec)

        subj = Subject()
        subj.save()
        sess = Session(experiment=e, subject=subj)  # limbo session
        # self.assertEqual(ec.get_session_status(sess), SessionStatus.UNINITIALIZED)  # (6/13/2023: no longer the case)
        with self.assertRaises(ValueError):
            ec.get_session_status(sess)

        subj2 = Subject()
        subj2.save()
        ec.add_session(subj2)
        sess2 = e.session_set.get(subject=subj2)
        self.assertEqual(ec.get_session_status(sess2), SessionStatus.INITIALIZED)


class TestInsertAdditionsIntoSteps(TestCase):

    def test_1(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "z"}}
        ExperimentController._insert_addition_into_steps(addition, steps)
        self.assertEqual(steps, [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ])

    def test_2(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 1, 'before_or_after': 'after'}, 'context': {'title': "w"}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "c"}}
        ExperimentController._insert_addition_into_steps(addition, steps)
        self.assertEqual(steps, [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "c"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 1, 'before_or_after': 'after'}, 'context': {'title': "w"}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ])

    def test_3(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 5, 'before_or_after': 'before'}, 'context': {'title': "c"}}
        with self.assertRaises(AssertionError):
            ExperimentController._insert_addition_into_steps(addition, steps)

    def test_3a(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': -1, 'before_or_after': 'before'}, 'context': {'title': "z"}}
        with self.assertRaises(AssertionError):
            ExperimentController._insert_addition_into_steps(addition, steps)

    def test_4(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}}
        ExperimentController._insert_addition_into_steps(addition, steps)
        self.assertEqual(steps, [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ])

    def test_5(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 1, 'before_or_after': 'after'}, 'context': {'title': "w"}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
            {'position': {'round_id': 4, 'before_or_after': 'after'}, 'context': {'title': "q"}},
        ]
        addition = \
            {'position': {'round_id': 4, 'before_or_after': 'after'}, 'context': {'title': "c"}}
        ExperimentController._insert_addition_into_steps(addition, steps)
        self.assertEqual(steps, [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 1, 'before_or_after': 'after'}, 'context': {'title': "w"}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
            {'position': {'round_id': 4, 'before_or_after': 'after'}, 'context': {'title': "q"}},
            {'position': {'round_id': 4, 'before_or_after': 'after'}, 'context': {'title': "c"}},
        ])

    def test_6(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 1, 'before_or_after': 'after'}, 'context': {'title': "w"}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 5, 'before_or_after': 'after'}, 'context': {'title': "c"}}
        with self.assertRaises(AssertionError):
            ExperimentController._insert_addition_into_steps(addition, steps)

    def test_7(self):
        steps = [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "x"}},
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "y"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "a"}},
            {'position': {'round_id': 1, 'before_or_after': 'before'}, 'context': {'title': "b"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 1, 'before_or_after': 'after'}, 'context': {'title': "w"}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': -1, 'before_or_after': 'after'}, 'context': {'title': "c"}}
        with self.assertRaises(AssertionError):
            ExperimentController._insert_addition_into_steps(addition, steps)

    def test_8(self):
        steps = [
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "z"}}
        ExperimentController._insert_addition_into_steps(addition, steps)
        self.assertEqual(steps, [
            {'position': {'round_id': 0, 'before_or_after': 'before'}, 'context': {'title': "z"}},
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ])

    def test_9(self):
        steps = [
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ]
        addition = \
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}}
        ExperimentController._insert_addition_into_steps(addition, steps)
        self.assertEqual(steps, [
            {'position': {'round_id': 0}, 'content': {'stimulusgroup_id': 0}},
            {'position': {'round_id': 0, 'before_or_after': 'after'}, 'context': {'title': "z"}},
            {'position': {'round_id': 1}, 'content': {'stimulusgroup_id': 1}},
            {'position': {'round_id': 2}, 'content': {'stimulusgroup_id': 2}},
            {'position': {'round_id': 3}, 'content': {'stimulusgroup_id': 3}},
            {'position': {'round_id': 4}, 'content': {'stimulusgroup_id': 4}},
        ])


class TestExperimentControllerWithConfig(TestCase):

    def test_ec_with_config(self):
        config_filepath = NestConfig.tests_resource_path('cvxhull_subjexp_toy_x.json')
        with open(config_filepath, 'rt') as fp:
            config = json.load(fp)
        scfg = StimulusConfig(config['stimulus_config'])
        ecfg = ExperimentConfig(stimulus_config=scfg,
                                config=config['experiment_config'])
        e = Experiment(
            title='Zhi ACR',
            description="Zhi's ACR experiment",
        )
        e.save()
        ec = ExperimentController(experiment=e, experiment_config=ecfg)
        ec.populate_stimuli()

        subj = Subject.objects.create()
        ec.add_session(subj)
        sess = e.session_set.get(subject=subj)
        self.assertEqual(ec.get_session_status(sess), SessionStatus.INITIALIZED)
        cs = Content.objects.all()
        sgs = StimulusGroup.objects.all()
        svgs = StimulusVoteGroup.objects.all()
        stims = Stimulus.objects.all()
        self.assertEqual(len(cs), 1)
        self.assertEqual(cs[0].content_id, 0)
        self.assertEqual(stims[0].content, cs[0])
        self.assertEqual(stims[1].content, cs[0])
        self.assertEqual(svgs[0].stimulusvotegroup_id, 0)
        self.assertEqual(svgs[1].stimulusvotegroup_id, 1)
        self.assertEqual(StimulusVoteGroup.find_stimulusvotegroups_from_stimulus(stims[0]), [svgs[0]])
        self.assertEqual(StimulusVoteGroup.find_stimulusvotegroups_from_stimulus(stims[1]), [svgs[1]])
        self.assertEqual(svgs[0].stimulusgroup, sgs[0])
        self.assertEqual(svgs[1].stimulusgroup, sgs[1])

        self.assertEqual(Round.objects.count(), 2)
        ec.delete_session(sess.id)
        self.assertEqual(Round.objects.count(), 0)
