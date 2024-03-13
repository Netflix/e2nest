import os

from django.test import TestCase
from django.urls import reverse_lazy
from nest.pages import Acr5cPage, AcrPage, CcrPage, DcrPage, GenericPage, \
    Samviq5dPage, SamviqPage

MEDIA_URL = ""


class TestPage(TestCase):

    def test_generic_page(self):
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
        GenericPage({
            'title': title,
            'text_html': text_html,
            'actions_html': actions_html,
        })

    def test_acr_page(self):
        p = AcrPage({
            'title': "Round 1 of 10",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_show_controls': True,
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], True)
        self.assertEqual(p.context['video_display_percentage'], 100)

    def test_acr_standard_page(self):
        p = AcrPage({
            'title': "Round 1 of 10",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'template_version': 'standard',
            't_gray': 0,
            'num_plays': 2,
            'button': 'Watch the video',
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)

    def test_acr5c_page(self):
        p = Acr5cPage({
            'title': "Round 1 of 10",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)

    def test_acr5c_standard_page(self):
        p = Acr5cPage({
            'title': "Round 1 of 10",
            'video': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'template_version': 'standard',
            't_gray': 0,
            'num_plays': 2,
            'button': 'Watch the video',
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)

    def test_dcr_page(self):
        p = DcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_display_percentage': 50,
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 50)

    def test_ccr_page(self):
        p = CcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_a_to_b_values': [0, 1, 2],
            'video_display_percentage': 100,
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)

        with self.assertRaises(AssertionError) as e:
            _ = CcrPage({
                'title': 'Round 1 of 10',
                'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
                'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
                'video_a_to_b_values': [0, 1],
                'video_display_percentage': 100,
                'stimulusvotegroup_id': 0,
            })
        self.assertTrue('the length of choices and video_a_to_b_values must be equal' in e.exception.args[0])

    def test_ccr_standard_page(self):
        p = CcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'video_a_to_b_values': [0, 1, 2],
            'template_version': "standard",
            'num_plays': 1,
            't_gray': 1000,
            'video_display_percentage': 70,
            'text_color': "#FFFFFF",
            'text_vert_perc': 45,
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 70)

        with self.assertRaises(AssertionError) as e:
            _ = CcrPage({
                'title': 'Round 1 of 10',
                'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
                'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
                'video_a_to_b_values': [0, 1],
                'template_version': "standard",
                'num_plays': 1,
                't_gray': 1000,
                'video_display_percentage': 70,
                'text_color': "#FFFFFF",
                'text_vert_perc': 45,
                'stimulusvotegroup_id': 0,
            })
        self.assertTrue('the length of choices and video_a_to_b_values must be equal' in e.exception.args[0])

    def test_dcr11d_page(self):
        p = DcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'choices':
                ['10 - Imperceptible',
                 '9 - Slightly perceptible somewhere',
                 '8 - Slightly perceptible everywhere',
                 '7 - Perceptible somewhere',
                 '6 - Perceptible everywhere',
                 '5 - Clearly perceptible somewhere',
                 '4 - Clearly perceptible everywhere',
                 '3 - Annoying somewhere',
                 '2 - Annoying everywhere',
                 '1 - Severely annoying somewhere',
                 '0 - Severely annoying everywhere'],
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)

    def test_dcr11d_standard_page(self):
        p = DcrPage({
            'title': 'Round 1 of 10',
            'video_a': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),  # noqa E501
            'video_b': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),  # noqa E501
            'template_version': "standard",
            'num_plays': 1,
            't_gray': 1000,
            'choices':
                ['10 - Imperceptible',
                 '9 - Slightly perceptible somewhere',
                 '8 - Slightly perceptible everywhere',
                 '7 - Perceptible somewhere',
                 '6 - Perceptible everywhere',
                 '5 - Clearly perceptible somewhere',
                 '4 - Clearly perceptible everywhere',
                 '3 - Annoying somewhere',
                 '2 - Annoying everywhere',
                 '1 - Severely annoying somewhere',
                 '0 - Severely annoying everywhere'],
            'stimulusvotegroup_id': 0,
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)

    def test_samviq_page(self):
        p = SamviqPage({
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
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)
        self.assertEqual(p.context['preload_videos'], False)

    def test_samviq5d_page(self):
        p = Samviq5dPage({
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
        })
        self.assertEqual(p.context['video_show_controls'], False)
        self.assertEqual(p.context['video_display_percentage'], 100)
        self.assertEqual(p.context['preload_videos'], False)
