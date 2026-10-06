import argparse
import csv
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
import webbrowser

from pathlib import Path

from nest.acr_hr_manifest import (
    build_config,
    create_local_media_server,
    local_media_server_address,
    serve_local_media,
    write_config,
)


EXPERIMENT_NAME_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$')
MANIFEST_FIELDS = [
    'role', 'path', 'source_id', 'condition_id', 'label',
    'recommended_rating',
]


def create_parser():
    parser = argparse.ArgumentParser(
        prog='subjective_study_aom',
        description='Run an AOM subjective study or build an ACR-HR '
                    'experiment. Media is never copied or transcoded.')
    parser.add_argument(
        'command', nargs='?', choices=['run'],
        help='create and run a study from organized media directories')
    parser.add_argument(
        '--experiment',
        help='experiment name for the run command')
    parser.add_argument('--manifest')
    parser.add_argument('--media-root')
    parser.add_argument('--output')
    parser.add_argument('--title')
    parser.add_argument('--site-id')
    parser.add_argument(
        '--study-port', type=int, default=8000,
        help='loopback port for the NEST study interface (default: 8000)')
    parser.add_argument(
        '--media-base-url', default='http://localhost:8093',
        help='URL from which the viewing workstation serves media')
    parser.add_argument('--protocol-version', default='acr-hr-v1')
    parser.add_argument('--description')
    parser.add_argument(
        '--experimenter',
        help='create the generated experiment in NEST for this username')
    parser.add_argument(
        '--serve-media', action='store_true',
        help='serve media on loopback after building/creating the experiment; '
             'runs until Ctrl-C')
    return parser


def local_study_urls(study_port):
    if not 1 <= study_port <= 65535:
        raise ValueError('--study-port must be between 1 and 65535')
    base_url = f'http://127.0.0.1:{study_port}'
    return f'{base_url}/login/', f'{base_url}/logout/?next=/login/'


def find_nest_repository(start=None):
    """Find a checkout containing the NEST manage.py from the current path."""
    start = Path(start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / 'nest_site' / 'manage.py').is_file():
            return candidate
    raise ValueError('run this command from inside an e2nest repository')


def create_experiment_in_repository(
        config_path, experimenter, repository=None):
    repository = Path(repository) if repository else find_nest_repository()
    site_root = repository / 'nest_site'
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(site_root)
    environment.setdefault('DJANGO_SETTINGS_MODULE', 'nest_site.settings')
    command = [
        sys.executable,
        str(site_root / 'nest' / 'scripts' / 'experiment_tools.py'),
        '--action', 'create_experiment',
        '--config', str(Path(config_path).resolve()),
        '--username', experimenter,
    ]
    try:
        subprocess.run(
            command, cwd=site_root, env=environment, check=True)
    except subprocess.CalledProcessError as error:
        raise ValueError(
            f'NEST experiment creation failed with exit code '
            f'{error.returncode}') from error


def discover_media_layout(media_root):
    media_root = Path(media_root).resolve()
    if not media_root.is_dir():
        raise ValueError(f'media root is not a directory: {media_root}')
    rows = []

    calibration_root = media_root / 'calibration'
    if not calibration_root.is_dir():
        raise ValueError('media root must contain a calibration directory')
    for rating_dir in sorted(calibration_root.iterdir()):
        if not rating_dir.is_dir():
            continue
        rating_match = re.match(r'^([1-5])(?:\D.*)?$', rating_dir.name)
        if rating_match is None:
            raise ValueError(
                f'calibration quality directory must start with 1-5: '
                f'{rating_dir.name}')
        for media_path in sorted(rating_dir.iterdir()):
            if media_path.is_file():
                rows.append({
                    'role': 'familiarization',
                    'path': media_path.relative_to(media_root).as_posix(),
                    'source_id': f'calibration-{media_path.stem}',
                    'condition_id': '',
                    'label': media_path.stem.replace('_', ' '),
                    'recommended_rating': rating_match.group(1),
                })

    scored_keys = set()
    for directory_name, role in [('bridge', 'bridge'), ('actual', 'test')]:
        role_root = media_root / directory_name
        if not role_root.is_dir():
            raise ValueError(
                f'media root must contain a {directory_name} directory')
        for source_dir in sorted(role_root.iterdir()):
            if not source_dir.is_dir():
                continue
            for media_path in sorted(source_dir.iterdir()):
                if not media_path.is_file():
                    continue
                key = (source_dir.name, media_path.stem)
                if key in scored_keys:
                    raise ValueError(
                        f'duplicate source and condition: {key[0]}/'
                        f'{key[1]}')
                scored_keys.add(key)
                rows.append({
                    'role': role,
                    'path': media_path.relative_to(media_root).as_posix(),
                    'source_id': source_dir.name,
                    'condition_id': media_path.stem,
                    'label': '',
                    'recommended_rating': '',
                })

    role_counts = {
        role: sum(row['role'] == role for row in rows)
        for role in ['familiarization', 'bridge', 'test']
    }
    for role, directory_name in [
            ('familiarization', 'calibration'),
            ('bridge', 'bridge'), ('test', 'actual')]:
        if role_counts[role] == 0:
            raise ValueError(
                f'{directory_name} directory does not contain any media')
    return rows


def _write_manifest(rows, path):
    with Path(path).open('w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _migrate_study_database(site_root, environment):
    subprocess.run(
        [sys.executable, str(site_root / 'manage.py'), 'migrate', '--noinput',
         '--run-syncdb'],
        cwd=site_root, env=environment, check=True)


def _prepare_study(repository, config_path, config):
    repository = Path(repository)
    site_root = repository / 'nest_site'
    environment = os.environ.copy()
    environment['PYTHONPATH'] = str(site_root)
    environment.setdefault('DJANGO_SETTINGS_MODULE', 'nest_site.settings')
    title = config['experiment_config']['title']
    environment['NEST_ACTIVE_EMAIL_EXPERIMENT'] = title
    _migrate_study_database(site_root, environment)

    database_path = site_root / 'db.sqlite3'
    with sqlite3.connect(database_path) as database:
        exists = database.execute(
            'SELECT 1 FROM nest_experiment WHERE title = ?',
            (title,)).fetchone() is not None
    if not exists:
        create_experiment_in_repository(
            config_path, 'study-admin', repository=repository)
    else:
        installed_path = site_root / 'media' / 'experiment_config' / \
            f'{title}.json'
        with installed_path.open(encoding='utf-8') as installed_file:
            installed_config = json.load(installed_file)
        if installed_config != config:
            raise ValueError(
                f'experiment {title!r} already exists with different media; '
                'choose a new --experiment name')
    return site_root, environment, database_path, title


def _run_servers(site_root, environment, database_path, media_root,
                 media_base_url, title, study_port):
    study_url, study_start_url = local_study_urls(study_port)
    media_server = create_local_media_server(media_root, media_base_url)
    media_thread = threading.Thread(
        target=media_server.serve_forever, daemon=True)
    media_thread.start()

    print(f'\nAOM subjective study {title!r}: {study_url}')
    print('Enter any valid email address to begin.')
    print(f'Scores are saved in {database_path}')
    print('Press Ctrl-C to stop the study.\n')
    # Going through logout makes switching between locally run experiments
    # deterministic even if the browser still has an older NEST session.
    browser_timer = threading.Timer(
        1.0, webbrowser.open, args=(study_start_url,))
    browser_timer.daemon = True
    browser_timer.start()
    server = subprocess.Popen(
        [sys.executable, str(site_root / 'manage.py'), 'runserver',
         f'127.0.0.1:{study_port}', '--noreload'],
        cwd=site_root, env=environment)
    try:
        return_code = server.wait()
        if return_code:
            raise ValueError(f'NEST server exited with code {return_code}')
    except KeyboardInterrupt:
        print('\nStopping the study.')
        server.terminate()
        server.wait()
    finally:
        browser_timer.cancel()
        media_server.shutdown()
        media_server.server_close()
        media_thread.join()


def run_study(experiment, media_root, site_id, media_base_url,
              protocol_version, study_port=8000):
    if EXPERIMENT_NAME_PATTERN.fullmatch(experiment) is None:
        raise ValueError(
            '--experiment must use only letters, numbers, hyphens, and '
            'underscores, and must begin with a letter or number')
    local_study_urls(study_port)
    repository = find_nest_repository()
    rows = discover_media_layout(media_root)
    with tempfile.TemporaryDirectory(prefix='subjective-study-aom-') as work:
        manifest_path = Path(work) / 'manifest.csv'
        config_path = Path(work) / f'{experiment}.json'
        _write_manifest(rows, manifest_path)
        config = build_config(
            manifest_path=manifest_path,
            media_root=media_root,
            media_base_url=media_base_url,
            title=experiment,
            site_id=site_id,
            protocol_version=protocol_version)
        write_config(config, config_path)
        site_root, environment, database_path, title = _prepare_study(
            repository, config_path, config)
        print(
            f'Loaded {len(config["stimulus_config"]["stimuli"])} scored '
            f'clips and {len(config["experiment_config"]["additions"]) - 1} '
            'calibration clips.')
        _run_servers(
            site_root, environment, database_path, media_root,
            media_base_url, title, study_port)
    return experiment


def _require_build_arguments(parser, args):
    missing = [name for name in
               ['manifest', 'media_root', 'output', 'title', 'site_id']
               if not getattr(args, name)]
    if missing:
        parser.error(
            'the following arguments are required: ' +
            ', '.join(f'--{name.replace("_", "-")}' for name in missing))


def main(argv=None):
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == 'run':
        missing = [name for name in ['experiment', 'media_root']
                   if not getattr(args, name)]
        if missing:
            parser.error(
                'run requires ' + ', '.join(
                    f'--{name.replace("_", "-")}' for name in missing))
        try:
            run_study(
                experiment=args.experiment,
                media_root=args.media_root,
                site_id=args.site_id or 'local-site',
                media_base_url=args.media_base_url,
                protocol_version=args.protocol_version,
                study_port=args.study_port)
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            parser.error(f'could not run study: {error}')
        return

    _require_build_arguments(parser, args)

    try:
        if args.serve_media:
            local_media_server_address(args.media_base_url)
        config = build_config(
            manifest_path=args.manifest,
            media_root=args.media_root,
            media_base_url=args.media_base_url,
            title=args.title,
            site_id=args.site_id,
            protocol_version=args.protocol_version,
            description=args.description)
        write_config(config, args.output)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    scored_count = config['experiment_config']['rounds_per_session']
    practice_count = len(config['experiment_config']['additions']) - 1
    print(f'Created {args.output}: {scored_count} scored stimuli and '
          f'{practice_count} familiarization examples')

    if args.experimenter:
        try:
            create_experiment_in_repository(args.output, args.experimenter)
        except ValueError as error:
            parser.error(f'could not create NEST experiment: {error}')
        print(f'Created NEST experiment {args.title!r} for experimenter '
              f'{args.experimenter!r}')

    if args.serve_media:
        try:
            serve_local_media(args.media_root, args.media_base_url)
        except OSError as error:
            parser.error(f'could not start local-media server: {error}')


if __name__ == '__main__':
    main()
