import os
import re

from abc import ABCMeta, abstractmethod
from collections.abc import Hashable
from functools import partial
from io import StringIO
from typing import List, Optional

import matplotlib.pyplot as plt
from lxml import etree


# ==== decorators ====

def override(interface_class):
    def overrider(method):
        assert (method.__name__ in dir(interface_class)), \
            f"{method.__name__} does not override any method " \
            f"in {interface_class.__name__}"
        return method
    return overrider


# ==== mixins ====


class TypeVersionEnabled(object):
    """
    Mandate a type name and a version string. Derived class (e.g. an Executor)
    has a unique string combining type and version. The string is useful in
    identifying a Result by which Executor it is generated (e.g. VMAF_V0.1,
    PSNR_V1.0, or VMAF_feature_V0.1).
    """

    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def TYPE(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def VERSION(self):
        raise NotImplementedError

    def __init__(self):
        self._assert_type_version()

    def _assert_type_version(self):

        assert re.match(r"^[a-zA-Z0-9_]+$", self.TYPE), \
            "TYPE can only contains alphabets, numbers and underscore (_)."

        assert re.match(r"^[a-zA-Z0-9._-]+$", self.VERSION), \
            "VERSION can only contains alphabets, numbers, dot (.), " \
            "hyphen(-) and underscore (_)."

    def get_type_version_string(self):
        return "{type}_V{version}".format(type=self.TYPE,
                                          version=self.VERSION)

    def get_cozy_type_version_string(self):
        return "{type} VERSION {version}".format(type=self.TYPE,
                                                 version=self.VERSION)

    @classmethod
    def find_subclass(cls, subclass_type):
        matched_subclasses = []
        for subclass in cls.get_subclasses_recursively():
            if hasattr(subclass, 'TYPE') and subclass.TYPE == subclass_type:
                matched_subclasses.append(subclass)
        assert len(matched_subclasses) == 1, \
            "Must have one and only one subclass of {class_name} with type " \
            "{type}, but got {num}".format(
                class_name=cls.__name__,
                type=subclass_type,
                num=len(matched_subclasses))
        return matched_subclasses[0]

    @classmethod
    def get_subclasses_recursively(cls):
        subclasses = cls.__subclasses__()
        subsubclasses = []
        for subclass in subclasses:
            subsubclasses += subclass.get_subclasses_recursively()
        return subclasses + subsubclasses


# ==== helpers ====


def get_file_name_without_extension(path):
    """

    >>> get_file_name_without_extension('yuv/src01_hrc01.yuv')
    'src01_hrc01'
    >>> get_file_name_without_extension('yuv/src01_hrc01')
    'src01_hrc01'
    >>> get_file_name_without_extension('abc/xyz/src01_hrc01.yuv')
    'src01_hrc01'
    >>> get_file_name_without_extension('abc/xyz/src01_hrc01.sdr.yuv')
    'src01_hrc01.sdr'
    >>> get_file_name_without_extension('abc/xyz/src01_hrc01.sdr.dvi.yuv')
    'src01_hrc01.sdr.dvi'

    """
    return os.path.splitext(path.split("/")[-1])[0]


def import_python_file(filepath):
    """
    Import a python file as a module.
    :param filepath:
    :return:
    """
    filename = get_file_name_without_extension(filepath)
    try:
        from importlib.machinery import SourceFileLoader
        ret = SourceFileLoader(filename, filepath).load_module()
    except ImportError:
        import imp
        ret = imp.load_source(filename, filepath)
    return ret


def empty_object():
    return type('', (), {})()


def my_argmin(a: List[int], shortlist: Optional[List[int]] = None):
    """
    My argmin implementation: return a list of indices chosen from the shortlist
    with the minimum value from a. If shortlist is None, use all indices.

    >>> my_argmin([1, 1, 2, 4])
    [0, 1]
    >>> my_argmin([3, 1, 2, 1])
    [1, 3]
    >>> my_argmin([1, 1, 2, 4], [0, 1, 3])
    [0, 1]
    >>> my_argmin([1, 1, 2, 4], [1, 2, 3])
    [1]
    >>> my_argmin([1, 1, 2, 4], [2, 3])
    [2]
    >>> my_argmin([1, 1, 2, 4], [0, 2, 3])
    [0]
    >>> my_argmin([1, 1, 2, 4], [])
    []
    """
    argmin = list()
    minval = None
    for i, e in enumerate(a):
        if shortlist is None or i in shortlist:
            if minval is None:
                minval = e
                argmin.append(i)
            else:
                if e == minval:
                    argmin.append(i)
                elif e < minval:
                    minval = e
                    argmin = [i]
                else:
                    pass
    return argmin


def indices(a, func):
    """
    Get indices of elements in an array which satisfies func
    >>> indices([1, 2, 3, 4], lambda x: x>2)
    [2, 3]
    >>> indices([1, 2, 3, 4], lambda x: x==2.5)
    []
    >>> indices([1, 2, 3, 4], lambda x: x>1 and x<=3)
    [1, 2]
    >>> indices([1, 2, 3, 4], lambda x: x in [2, 4])
    [1, 3]
    >>> indices([1,2,3,1,2,3,1,2,3], lambda x: x > 2)
    [2, 5, 8]
    """
    return [i for (i, val) in enumerate(a) if func(val)]


class memoized(object):
    """ Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).

    memoized is similar to persist, but if applied to
    class methods, persist will cache on a per-class basis, while memoized
    will cache on a per-object basis.

    Taken from: https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args):
        if not isinstance(args, Hashable):
            return self.func(*args)
        if args in self.cache:
            return self.cache[args]
        else:
            value = self.func(*args)
            self.cache[args] = value
            return value

    def __repr__(self):
        """ Return the function's docstring. """
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """ Support instance methods. """
        return partial(self.__call__, obj)


def map_path_to_noise_rmse(path: str) -> Optional[int]:
    """
    >>> map_path_to_noise_rmse('snowpiercer-filmgrain-subj-test-prep-101a-beamr5-20211020aopalach-__beamr5__1920_1080__ni_denoise_filter_before_scale__qp18_vmaf80.84_psnr36.08_kbps13225.28_fps23.976023976023978.mp4')  # noqa E501
    0
    >>> map_path_to_noise_rmse('snowpiercer-filmgrain-subj-test-prep-101a-beamr5-20211020aopalach-__beamr5__1920_1080__none__qp18_vmaf97.58_psnr38.41_kbps21499.17_fps23.976023976023978.mp4')  # noqa E501
    -1
    >>> map_path_to_noise_rmse('snowpiercer-filmgrain-subj-test-prep-101c-beamr5-20211020aopalach-__beamr5__1920_1080__ni_denoise_with_target_noise_rmse_5_filter_before_scale__qp18_vmaf87.62_psnr37.06_kbps13956.47_fps23.976023976023978.mp4')  # noqa E501
    5
    >>> map_path_to_noise_rmse('snowpiercer-filmgrain-subj-test-prep-101c-beamr5-20211020aopalach-__beamr5__1920_1080__ni_denoise_with_target_noise_rmse_10_filter_before_scale__qp18_vmaf94.54_psnr38.15_kbps18356.45_fps23.976023976023978.mp4')  # noqa E501
    10
    >>> map_path_to_noise_rmse('CTS3E1_B__15_55_16_0__SdrX264MainCrfVE__384_216__qp20_vmaf42.63_psnr27.55_kbps308.96_fps23.976.mp4')
    -1
    """
    import re
    mo = re.search(r"ni_denoise_with_target_noise_rmse_([0-9]*)", path)
    if mo:
        rmse = int(mo.group(1))
        assert rmse >= 0
        return rmse
    mo = re.search(r"_none_", path)
    if mo:
        return -1
    mo = re.search(r"ni_denoise_filter_before_scale", path)
    if mo:
        return 0
    return -1


def map_filename_to_type(path: str) -> Optional[str]:
    """
    >>> map_filename_to_type('/media/mp4/test1a1b/training/reference/documentary-now-season-1-the-e-filmgrain-subj-test-prep-101a-beamr5-20211020aopalach-__beamr5__1920_1080__none__qp18_vmaf95.07_psnr38.65_kbps16175.49_fps23.976023976023978.mp4')  # noqa E501
    'training'
    >>> map_filename_to_type('/media/mp4/test1a1b/testing/reference/friends-season-2-the-one-with--filmgrain-subj-test-prep-101a-beamr5-20211020aopalach-__beamr5__1920_1080__none__qp18_vmaf95.85_psnr47.4_kbps10704.94_fps23.976023976023978.mp4')  # noqa E501
    'testing'
    >>> map_filename_to_type('/media/mp4/test1a1b/reliability/PeeWeeS2Store-underVMAF-A-filmgrain-subj-test-prep-26-beamr5-20211007-__beamr5__960_540__none__qp37_vmaf26.91_psnr27.9_kbps283.91_fps29.97002997002997.mp4')  # noqa E501
    'reliability'
    >>> map_filename_to_type('snowpiercer-filmgrain-subj-test-prep-101a-beamr5-20211020aopalach-__beamr5__1920_1080__ni_denoise_filter_before_scale__qp18_vmaf80.84_psnr36.08_kbps13225.28_fps23.976023976023978.mp4')  # noqa E501
    Traceback (most recent call last):
    ...
    AssertionError
    >>> map_filename_to_type('CTS3E1_B__15_55_16_0__SdrX264MainCrfVE__384_216__qp20_vmaf42.63_psnr27.55_kbps308.96_fps23.976.mp4')
    Traceback (most recent call last):
    ...
    AssertionError
    """
    if '/training/' in path:
        return 'training'
    elif '/testing/' in path:
        return 'testing'
    elif '/reliability/' in path:
        return 'reliability'
    else:
        assert False


def map_participantid_to_test(participantid: str) -> Optional[str]:
    """
    >>> map_participantid_to_test('Netflix_Noise_0')
    '1a'
    >>> map_participantid_to_test('Netflix_Noise_1')
    '1b'
    >>> map_participantid_to_test('Netflix_Noise_2')
    '1a'
    >>> map_participantid_to_test('Netflix_Noise_3')
    '1b'
    >>> map_participantid_to_test('xyz')
    Traceback (most recent call last):
    ...
    AssertionError
    """
    mo = re.match(r"^Netflix_Noise_([0-9]*)", participantid)
    assert mo is not None
    pid = int(mo.group(1))
    if pid % 2 == 0:
        return '1a'
    else:
        return '1b'


def sanity_same_content(enc_filepath: str, ref_filepath: str) -> bool:
    """
    >>> sanity_same_content("/Users/zli/Data/noise_study/projects_6sec_07262021/encode/selected_x264eaas_prefilter_0/oishinbo_season_2_episode_43__4_3_4_9__SdrX264MainCrfVE__1920_1080__qp22_enable_audio_False_vmaf90.64_phonevmaf99.79_psnr41.30_kbps2456.31.mp4",  # noqa E501
    ... "/Users/zli/Data/noise_study/projects_6sec_07262021/encode/selected_beamr5fixed/oishinbo_season_2_episode_43/oishinbo-season-2-episode-43-filmgrain-subj-test-prep-102c-beamr5-20211020aopalach-__beamr5__1920_1080__ni_denoise_with_target_noise_rmse_2_filter_before_scale__qp37_vmaf80.53_psnr39.58_kbps155.77_fps23.976023976023978.mp4")  # noqa E501
    True
    >>> sanity_same_content("/Users/zli/Data/noise_study/projects_6sec_07262021/encode/selected_x264eaas_prefilter_0/oishinbo_season_2_episode_43__4_3_4_9__SdrX264MainCrfVE__1920_1080__qp22_enable_audio_False_vmaf90.64_phonevmaf99.79_psnr41.30_kbps2456.31.mp4",  # noqa E501
    ... "/Users/zli/Data/noise_study/projects_6sec_07262021/encode/selected_beamr5fixed/groundhog_day/groundhog-day-filmgrain-subj-test-prep-102-4-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp23_vmaf84.8_psnr35.36_kbps11438.17_fps23.976023976023978.mp4")  # noqa E501
    False
    >>> sanity_same_content("/Users/zli/Data/noise_study/projects_6sec_07262021/encode/selected_beamr5fixed/the_walking_dead_season_6_the_/the-walking-dead-season-6-the--filmgrain-subj-test-prep-102a-beamr5-20211020aopalach-__beamr5__1920_1080__none__qp22_vmaf81.55_psnr36.88_kbps6048.37_fps23.976023976023978.mp4",  # noqa E501
    ... "/Users/zli/Data/noise_study/projects_6sec_07262021/encode/selected_beamr5fixed/the_guy_in_the_grave_next_door/the-guy-in-the-grave-next-door-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp28_vmaf86.0_psnr36.22_kbps7769.82_fps24.0.mp4")  # noqa E501
    False
    >>> sanity_same_content("/Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test1a1b/testing/the-walking-dead-season-6-the--filmgrain-subj-test-prep-101c-beamr5-20211020aopalach-__beamr5__1920_1080__ni_denoise_with_target_noise_rmse_5_filter_before_scale__qp18_vmaf84.35_psnr38.63_kbps12859.57_fps23.976023976023978.mp4",  # noqa E501
    ... " /Users/zli/Data/noise_study/projects_6sec_07262021/other/encode_selection/test1a1b/testing/reference/the-walking-dead-season-6-the--filmgrain-subj-test-prep-101a-beamr5-20211020aopalach-__beamr5__1920_1080__none__qp18_vmaf89.07_psnr39.53_kbps19680.52_fps23.976023976023978.mp4")  # noqa E501
    True
    """
    enc_filename = os.path.splitext(os.path.basename(enc_filepath))[0]
    ref_filename = os.path.splitext(os.path.basename(ref_filepath))[0]
    enc_set = {_get_first_nontrivial_word(enc_filename, '-'),
               _get_first_nontrivial_word(enc_filename, '_')}
    ref_set = {_get_first_nontrivial_word(ref_filename, '-'),
               _get_first_nontrivial_word(ref_filename, '_')}
    return len(enc_set.intersection(ref_set).difference({'the', 'in'})) > 0


def _get_first_nontrivial_word(enc_filename, splitter='-'):
    words = enc_filename.split(splitter)
    words = list(filter(lambda w: w.lower() not in ['the', 'in', 'a'], words))
    assert len(words) > 0
    return words[0]


def map_filename_to_bitrate_kbps(path: str) -> Optional[float]:
    """
    >>> map_filename_to_bitrate_kbps('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    98.74
    >>> map_filename_to_bitrate_kbps('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_kbps7292.57.mp4')  # noqa E501
    7292.57
    >>> map_filename_to_bitrate_kbps('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_mbps7292.57.mp4')  # noqa E501
    """
    basename = os.path.basename(path)
    basename_no_ext = os.path.splitext(basename)[0]
    mo = re.search(r"_kbps([0-9.]+)", basename_no_ext)
    if mo is None:
        return None
    bitrate_kbps = float(mo.group(1))
    return bitrate_kbps


def map_filename_to_vmaf(path: str) -> Optional[float]:
    """
    >>> map_filename_to_vmaf('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    22.85
    >>> map_filename_to_vmaf('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_kbps7292.57.mp4')  # noqa E501
    99.51
    >>> map_filename_to_vmaf('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmat99.51_phonevmaf100.00_psnr38.85_mbps7292.57.mp4')  # noqa E501
    """
    basename = os.path.basename(path)
    basename_no_ext = os.path.splitext(basename)[0]
    mo = re.search(r"_vmaf([0-9.]+)", basename_no_ext)
    if mo is None:
        return None
    vmaf = float(mo.group(1))
    return vmaf


def map_filename_to_phonevmaf(path: str) -> Optional[float]:
    """
    >>> map_filename_to_phonevmaf('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    37.4
    >>> map_filename_to_phonevmaf('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_kbps7292.57.mp4')  # noqa E501
    100.0
    >>> map_filename_to_phonevmaf('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmat100.00_psnr38.85_mbps7292.57.mp4')  # noqa E501
    """
    basename = os.path.basename(path)
    basename_no_ext = os.path.splitext(basename)[0]
    mo = re.search(r"_phonevmaf([0-9.]+)", basename_no_ext)
    if mo is None:
        return None
    phonevmaf = float(mo.group(1))
    return phonevmaf


def map_filename_to_qp(path: str) -> Optional[float]:
    """
    >>> map_filename_to_qp('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    >>> map_filename_to_qp('ELE1NX122021/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp34_vmaf75.97_psnr33.34_kbps1774.05_fps23.976023976023978.mp4')  # noqa E501
    34
    >>> map_filename_to_qp('ELE1NX122021/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp31_vmaf81.11_psnr33.89_kbps2924.92_fps23.976023976023978.mp4')  # noqa E501
    31
    """
    basename = os.path.basename(path)
    basename_no_ext = os.path.splitext(basename)[0]
    mo = re.search(r"_qp([0-9]+)", basename_no_ext)
    if mo is None:
        return None
    qp = int(mo.group(1))
    return qp


def map_filename_to_title(path: str, length: int = 4) -> str:
    """
    >>> map_filename_to_title('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    'Mast'
    >>> map_filename_to_title('ELE1NX122021/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp34_vmaf75.97_psnr33.34_kbps1774.05_fps23.976023976023978.mp4')  # noqa E501
    'taxi'
    >>> map_filename_to_title('ELE1NX122021/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp31_vmaf81.11_psnr33.89_kbps2924.92_fps23.976023976023978.mp4')  # noqa E501
    'taxi'
    >>> map_filename_to_title('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_kbps7292.57.mp4')  # noqa E501
    'IpMa'
    >>> map_filename_to_title('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_kbps7292.57.mp4', 6)  # noqa E501
    'IpMan2'
    """
    basename = os.path.basename(path)
    basename_no_ext = os.path.splitext(basename)[0]
    return basename_no_ext[:length]


def map_filename_to_height(path: str) -> Optional[float]:
    """
    >>> map_filename_to_height('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    342
    >>> map_filename_to_height('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmaf100.00_psnr38.85_kbps7292.57.mp4')  # noqa E501
    1080
    >>> map_filename_to_height('/media/mp4/joint_av_quality_v1/reference/IpMan2__frm57060to57300__SdrVp9Eve2pVE__1920_1080__7500_audio_kbps_192_videoChunksizeInSeconds_10_vmaf99.51_phonevmat100.00_psnr38.85_mbps7292.57.mp4')  # noqa E501
    1080
    >>> map_filename_to_height('/media/mp4/joint_av_quality_v1/MasterOfNoneS1E2__frm20000to20252__SdrVp9Eve2pVE__608_342__100_videoChunksizeInSeconds_10_vmaf22.85_phonevmaf37.40_psnr28.98_kbps98.74.mp4')  # noqa E501
    342
    >>> map_filename_to_height('ELE1NX122021/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160__none__qp34_vmaf75.97_psnr33.34_kbps1774.05_fps23.976023976023978.mp4')  # noqa E501
    2160
    >>> map_filename_to_height('ELE1NX122021/test2/training/taxi-driver-filmgrain-subj-test-prep-102-beamr5-20211020aopalach-__beamr5__3840_2160_none__qp31_vmaf81.11_psnr33.89_kbps2924.92_fps23.976023976023978.mp4')  # noqa E501
    """
    basename = os.path.basename(path)
    basename_no_ext = os.path.splitext(basename)[0]
    mo = re.search(r"__([0-9]+)_([0-9]+)__", basename_no_ext)
    if mo is None:
        return None
    height = int(mo.group(2))
    return height


def get_cmap(n, name='hsv'):
    """
    Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.
    """
    return plt.cm.get_cmap(name, n)


def validate_xml(html):
    """
    Return True if html is a valid xml; otherwise return false

    >>> validate_xml(" <p> You have completed the test. Please take a moment to complete a post-test survey at: <a href=\\"https://forms.gle/oEBBS52D2BHeuCTN8\\" target=\\"_blank\\" rel=\\"noopener noreferrer\\"> https://forms.gle/oEBBS52D2BHeuC </a>.</p> ")  # noqa E501
    True
    >>> validate_xml(" <p> You have completed the test. Please take a moment to complete a post-test survey at: <a href=\\"https://forms.gle/oEBBS52D2BHeuCTN8\\" target=\\"_blank\\" rel=\\"noopener noreferrer\\"> https://forms.gle/oEBBS52D2BHeuC </a>.</pp> ")  # noqa E501
    False

    """
    try:
        etree.parse(StringIO(html), etree.HTMLParser(recover=False))
    except etree.XMLSyntaxError:
        return False
    return True


class DummyClass(object):
    pass
