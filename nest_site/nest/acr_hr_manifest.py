import csv
import hashlib
import html
import json
import mimetypes
import os

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urljoin, urlsplit


SCORED_ROLES = {'bridge', 'test'}
VALID_ROLES = SCORED_ROLES | {'familiarization'}
REQUIRED_COLUMNS = {
    'role', 'path', 'source_id', 'condition_id', 'recommended_rating'}
RATING_LABELS = {
    '5': 'Excellent',
    '4': 'Good',
    '3': 'Fair',
    '2': 'Poor',
    '1': 'Bad',
}


def _sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as media_file:
        for chunk in iter(lambda: media_file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _media_url(base_url, relative_path):
    encoded_path = quote(str(PurePosixPath(relative_path)), safe='/')
    return urljoin(base_url.rstrip('/') + '/', encoded_path)


def _read_manifest(manifest_path, media_root, media_base_url):
    media_root = Path(media_root).resolve()
    rows = []
    with Path(manifest_path).open(newline='', encoding='utf-8-sig') as manifest:
        reader = csv.DictReader(manifest)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                'manifest is missing columns: ' + ', '.join(sorted(missing)))

        for line_number, raw_row in enumerate(reader, start=2):
            row = {key: (value or '').strip()
                   for key, value in raw_row.items()}
            role = row['role'].lower()
            if role not in VALID_ROLES:
                raise ValueError(
                    f'line {line_number}: role must be one of '
                    f'{sorted(VALID_ROLES)}, not {row["role"]!r}')
            if not row['path']:
                raise ValueError(f'line {line_number}: path is required')
            if not row['source_id']:
                raise ValueError(f'line {line_number}: source_id is required')
            if role in SCORED_ROLES and not row['condition_id']:
                raise ValueError(
                    f'line {line_number}: condition_id is required for {role}')
            if role == 'familiarization' and \
                    row['recommended_rating'] not in RATING_LABELS:
                raise ValueError(
                    f'line {line_number}: recommended_rating must be an '
                    f'integer from 1 to 5 for familiarization media')

            relative_path = Path(row['path'])
            if relative_path.is_absolute():
                raise ValueError(
                    f'line {line_number}: path must be relative to media root')
            # Explicit media symlinks let large assets be organized into a
            # study without copying them. absolute() still normalizes "..".
            local_path = Path(os.path.abspath(media_root / relative_path))
            try:
                local_path.relative_to(media_root)
            except ValueError as error:
                raise ValueError(
                    f'line {line_number}: path leaves media root') from error
            if not local_path.is_file():
                raise ValueError(
                    f'line {line_number}: media file does not exist: '
                    f'{local_path}')

            mime_type = mimetypes.guess_type(local_path.name)[0]
            if not mime_type or not mime_type.startswith('video/'):
                raise ValueError(
                    f'line {line_number}: cannot identify a video MIME type '
                    f'for {local_path.name}')

            rows.append({
                **row,
                'role': role,
                'type': mime_type,
                'url': _media_url(media_base_url, relative_path.as_posix()),
                'sha256': _sha256(local_path),
            })

    if not any(row['role'] in SCORED_ROLES for row in rows):
        raise ValueError('manifest must contain at least one bridge or test row')
    return rows


def _practice_addition(row, index, count):
    label = row.get('label') or f'Familiarization example {index} of {count}'
    safe_label = html.escape(label)
    safe_url = html.escape(row['url'], quote=True)
    video_id = f'familiarization-video-{index}'
    play_id = f'familiarization-play-{index}'
    continue_id = f'familiarization-continue-{index}'
    status_id = f'familiarization-status-{index}'
    recommendation_id = f'familiarization-recommendation-{index}'
    rating_id = f'familiarization-rating-{index}'
    rating_name = f'familiarization-choice-{index}'
    recommended_rating = row['recommended_rating']
    recommended_label = RATING_LABELS[recommended_rating]
    rating_options = ''.join(
        f'<div><input type="radio" name="{rating_name}" '
        f'id="{rating_name}-{value}" value="{value}">'
        f'<label for="{rating_name}-{value}">{value} &ndash; '
        f'{RATING_LABELS[value]}</label></div>'
        for value in ['5', '4', '3', '2', '1'])
    next_label = 'Start scored session' if index == count \
        else 'Next familiarization example'
    return {
        'position': {'round_id': 0, 'before_or_after': 'before'},
        'context': {
            'title': safe_label,
            'text_html': (
                '<p>This example is for familiarization only. Its score is '
                'not recorded. A recommended calibration rating will appear '
                'after playback.</p>'
                f'<p><button type="button" class="button" id="{play_id}">'
                'Play video</button></p>'
                f'<div id="{rating_id}" style="display:none">'
                '<p>How would you rate the overall picture quality?</p>'
                f'{rating_options}</div>'
                f'<p id="{recommendation_id}" style="display:none">'
                f'<b>Recommended rating: {recommended_rating} &ndash; '
                f'{recommended_label}.</b></p>'
                f'<p id="{status_id}" style="display:none"></p>'),
            'actions_html': (
                f'<p id="{continue_id}" style="display:none">'
                '<a class="button" href="{action_url}" id="start">'
                f'{next_label}</a></p>'),
            'extrastyle_html': (
                f'#{video_id} {{ position: fixed; inset: 0; width: 100vw; '
                'height: 100vh; object-fit: contain; background: black; '
                'display: none; z-index: 10000; }'),
            'extrabody_html': (
                f'<video id="{video_id}" playsinline muted preload="auto" '
                'controlsList="nodownload nofullscreen noremoteplayback" '
                f'src="{safe_url}"></video>'),
            'script_html': (
                'window.addEventListener("load", function () {'
                f'var video = document.getElementById("{video_id}");'
                f'var play = document.getElementById("{play_id}");'
                f'var proceed = document.getElementById("{continue_id}");'
                f'var status = document.getElementById("{status_id}");'
                f'var recommendation = document.getElementById("{recommendation_id}");'
                f'var ratingPanel = document.getElementById("{rating_id}");'
                'var container = document.getElementById("container");'
                'var finishPlayback = function (playedSuccessfully) {'
                'video.pause(); video.style.display = "none";'
                'document.body.style.backgroundColor = "white";'
                'container.style.display = "block";'
                'play.disabled = true;'
                'if (playedSuccessfully) {'
                'ratingPanel.style.display = "block";'
                'recommendation.style.display = "block";'
                'proceed.style.display = "block";}'
                'else { proceed.style.display = "block"; }};'
                'play.addEventListener("click", function () {'
                'container.style.display = "none";'
                'document.body.style.backgroundColor = "black";'
                'video.style.display = "block"; video.currentTime = 0;'
                'var playback = video.play();'
                'if (playback !== undefined) {'
                'playback.catch(function () {'
                'status.textContent = "The video could not be played. You may continue.";'
                'status.style.display = "block"; finishPlayback(false);});}});'
                'video.addEventListener("ended", function () { finishPlayback(true); });'
                'video.addEventListener("error", function () {'
                'status.textContent = "The video could not be played. You may continue.";'
                'status.style.display = "block"; finishPlayback(false);});});'),
        },
    }


def build_config(manifest_path, media_root, media_base_url, title, site_id,
                 protocol_version='acr-hr-v1', description=None):
    rows = _read_manifest(manifest_path, media_root, media_base_url)
    scored = [row for row in rows if row['role'] in SCORED_ROLES]
    familiarization = [
        row for row in rows if row['role'] == 'familiarization']

    source_ids = []
    for row in scored:
        if row['source_id'] not in source_ids:
            source_ids.append(row['source_id'])
    content_ids = {source_id: index
                   for index, source_id in enumerate(source_ids)}

    stimuli = []
    for stimulus_id, row in enumerate(scored):
        stimuli.append({
            'stimulus_id': stimulus_id,
            'content_id': content_ids[row['source_id']],
            'source_id': row['source_id'],
            'condition_id': row['condition_id'],
            'stimulus_role': row['role'],
            'type': row['type'],
            'path': row['url'],
            'sha256': row['sha256'],
        })

    additions = [{
        'position': {'round_id': 0, 'before_or_after': 'before'},
        'context': {
            'title': 'Instructions',
            'text_html': (
                '<p>Rate the overall picture quality of each video from '
                '<b>Bad</b> to <b>Excellent</b>. Penalize altered structure, '
                'text, faces, unstable detail, and temporal inconsistency.</p>'
                '<p>Each scored clip plays once. At the rating screen, you '
                'may replay that clip up to five times.</p>'),
            'actions_html': (
                '<p><a class="button" href="{action_url}" id="start">'
                f'{"Continue to familiarization" if familiarization else "Start scored session"}'
                '</a></p>'),
        },
    }]
    additions.extend(
        _practice_addition(row, index, len(familiarization))
        for index, row in enumerate(familiarization, start=1))

    stimulus_groups = [{
        'stimulusgroup_id': stimulus['stimulus_id'],
        'stimulusvotegroup_ids': [stimulus['stimulus_id']],
    } for stimulus in stimuli]
    vote_groups = [{
        'stimulusvotegroup_id': stimulus['stimulus_id'],
        'stimulus_ids': [stimulus['stimulus_id']],
    } for stimulus in stimuli]

    return {
        'stimulus_config': {
            'contents': [
                {'content_id': content_id, 'name': source_id}
                for source_id, content_id in content_ids.items()
            ],
            'stimuli': stimuli,
            'stimulusvotegroups': vote_groups,
            'stimulusgroups': stimulus_groups,
        },
        'experiment_config': {
            'title': title,
            'description': description or (
                'ACR-HR experiment generated from a media manifest.'),
            'methodology': 'acr',
            'vote_scale': 'FIVE_POINT',
            'rounds_per_session': len(stimuli),
            'random_seed': None,
            'avoid_consecutive_content': True,
            'prioritized': [],
            'blocklist_stimulusgroup_ids': [],
            'protocol_metadata': {
                'site_id': site_id,
                'protocol_version': protocol_version,
                'playback_software_version': 'e2nest-acr-hr-reviewable-v1',
                'media_delivery_mode': 'local-media',
                'email_login_enabled': True,
            },
            'additions': additions,
            'round_context': {
                'template_version': 'reviewable',
                't_gray': 1000,
                'video_display_percentage': 100,
                'video_show_controls': False,
                'max_replays_per_clip': 5,
                'instruction_html': '',
                'question': 'Rate the overall picture quality of this video.',
                'choices': [
                    '5 - Excellent', '4 - Good', '3 - Fair',
                    '2 - Poor', '1 - Bad',
                ],
            },
            'done_context': {
                'text_html': '<p>You have completed this experiment.</p>',
            },
        },
    }


def write_config(config, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as output:
        json.dump(config, output, indent=2)
        output.write('\n')


def local_media_server_address(media_base_url):
    parsed = urlsplit(media_base_url)
    if parsed.scheme != 'http':
        raise ValueError('--serve-media requires an http media base URL')
    if parsed.hostname not in {'localhost', '127.0.0.1'}:
        raise ValueError(
            '--serve-media only supports localhost or 127.0.0.1')
    if parsed.path not in {'', '/'} or parsed.query or parsed.fragment:
        raise ValueError(
            '--serve-media requires a media base URL without a path, query, '
            'or fragment')
    try:
        port = parsed.port or 80
    except ValueError as error:
        raise ValueError(f'invalid media server port: {error}') from error
    return '127.0.0.1', port


def serve_local_media(media_root, media_base_url):
    server = create_local_media_server(media_root, media_base_url)
    print(f'Serving {Path(media_root).resolve()} at {media_base_url}')
    print('Press Ctrl-C to stop the local-media server.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping local-media server.')
    finally:
        server.server_close()


def create_local_media_server(media_root, media_base_url):
    address = local_media_server_address(media_base_url)
    handler = partial(
        SimpleHTTPRequestHandler, directory=str(Path(media_root).resolve()))
    return ThreadingHTTPServer(address, handler)
