# AV2 AI-extension ACR-HR demonstration

This PoC demonstrates the proposed hidden-reference, single-stimulus workflow
with 15 scored SDR stimuli and two unscored practice clips. The media comes
from `/data/ICME_HDR_SDR`.

The encoded conditions are **stand-ins only**. They are not AV2 or
AI-extension outputs and the resulting scores must not be used as codec
results.

## Features demonstrated

- Five-category ACR with a hidden reference presented like every other clip
- Two unscored practice clips whose contents do not occur in the scored set
- Independent playlist randomization with no adjacent clips from one source
- Up to five optional replays per clip
- Neutral-gray pre-playback interval and a clear white rating screen
- Playback completion, replay count, timing, site, protocol,
  and stimulus metadata in the response export
- SUREAL export through the existing NEST workflow

## Run locally

Organize the media by its role. Calibration directory names begin with their
recommended rating. Scored media is grouped by source, and each filename is
its condition identifier:

```text
my-media/
├── calibration/
│   ├── 2-poor/campfire.mp4
│   └── 4-good/knitting.mp4
├── bridge/
│   └── face-close/hidden-reference.mp4
└── actual/
    └── face-close/
        ├── anchor-op1.mp4
        └── ai-extension-op1.mp4
```

The files may be symlinks to existing media, so organizing a study does not
require copying or transcoding large assets.

After installing the repository, one command discovers these sets, initializes
the database, creates the named experiment, starts NEST and the local-media
server, and opens the login page:

```bash
subjective_study_aom run \
  --experiment av2-ai-extension \
  --media-root /path/to/my-media
```

NEST serves the study interface on port 8000 by default. If that port is in
use, select another loopback port, for example `--study-port 8001`. The media
server port remains independently configurable with `--media-base-url`.

Enter any valid email address. Scores are retained in `nest_site/db.sqlite3`.
Press Ctrl-C in the terminal to stop both servers.

This command uses NEST's **local-media option**. The experiment configuration
points to `localhost:8093`, so each viewing workstation loads its pre-positioned
media locally even when the NEST application is hosted centrally.

Use a viewing client with HEVC decoding support. The command does not transcode or
otherwise alter the supplied media files.

## Use your own media (CLI)

Experimenters do not need to write NEST JSON. Copy the example manifest
[`resource/experiment_config/acr_hr_media_manifest.csv`](resource/experiment_config/acr_hr_media_manifest.csv)
and enter one row per media file:

| Column | Meaning |
| --- | --- |
| `role` | `familiarization` (unscored), `bridge` (scored and shared across sites), or `test` (scored) |
| `path` | File path relative to `--media-root` |
| `source_id` | Stable source-content name; use the same value for conditions derived from the same source |
| `condition_id` | Stable processing-condition name; required for `bridge` and `test` rows |
| `label` | Optional viewer-facing title for a familiarization example |
| `recommended_rating` | Calibration rating from 1 (Bad) to 5 (Excellent); required for familiarization rows |

Install the repository once from its root so the command is available in the
active virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
```

Then run:

```bash
subjective_study_aom \
  --manifest my_media_manifest.csv \
  --media-root /path/to/my/media \
  --output resource/experiment_config/my_experiment.json \
  --title my_experiment \
  --site-id my_site \
  --experimenter my_username \
  --serve-media
```

The command checks that every file exists, computes its SHA-256 checksum, and
generates the complete ACR-HR configuration. It does not copy, modify, or
transcode media. With `--experimenter`, it also creates the experiment in the
NEST database. With `--serve-media`, it serves the media on `127.0.0.1` and
keeps running until Ctrl-C. The checksum and role are retained in the protocol
response export; sites can compare bridge checksums to verify that they used
identical stimuli.

If `--serve-media` is omitted, serve the same media root separately on each
viewing workstation:

```bash
python3 -m http.server 8093 --bind 127.0.0.1 --directory /path/to/my/media
```

The manifest interface remains available for cases that need explicit metadata
instead of the directory convention. For another site, keep the manifest,
experiment name, protocol version, and media identical while changing only
`--site-id`.

## Export the common response fields

```bash
cd nest_site
PYTHONPATH=. DJANGO_SETTINGS_MODULE=nest_site.settings \
python nest/scripts/export_protocol_responses.py \
  --experiment av2_ai_extension_acr_hr_demo \
  --output av2_ai_extension_acr_hr_demo.responses.csv
```

The same CSV is available from the NEST experiment administration page using
the **Protocol responses — Download CSV** action.

For a second site, deploy the same experiment configuration after changing
`protocol_metadata.site_id`. The site-specific CSV files retain the same
stimulus IDs and schema and can be concatenated for centralized validation.
