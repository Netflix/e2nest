import os

from nest_site.settings import MEDIA_URL


dataset_name = 'cvxhull_subjexp'
yuv_fmt = 'notyuv'
quality_width = 1920
quality_height = 1080

ref_videos = [{'content_id': 0,
  'content_name': 'CTS3E1_B',
  'path': os.path.join(MEDIA_URL, "mp4/samples/Meridian/Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4")},
]

dis_videos = [
 {'asset_id': 0,
  'content_id': 0,
  'os': [],
  'path': os.path.join(MEDIA_URL, "mp4", "samples", "Meridian", "Meridian_A__8_18_8_23__SdrVvhevce2pVE__3840_2160__6000_enable_audio_False_vmaf103.58_phonevmaf104.85_psnr50.40_kbps6702.77.mp4"),
 },
 {'asset_id': 1,
  'content_id': 0,
  'os': [],
  'path': os.path.join(MEDIA_URL, "mp4", "samples", "Meridian", "Meridian_A__8_18_8_23__SdrVvhevce2pVE__960_540__500_enable_audio_False_vmaf87.25_phonevmaf98.62_psnr45.35_kbps559.20.mp4"),
 },
]
