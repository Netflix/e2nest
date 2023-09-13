#!/usr/bin/env python3

import argparse

import django
django.setup()

from nest.io import ExperimentUtils  # noqa: E402, I202

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action", dest="action", nargs=1, type=str,
        help="action to take, options: validate_config, create_experiment, "
             "delete_experiment, add_session, delete_session, "
             "update_first_session_subject, reset_unfinished_first_session",
        required=True)
    parser.add_argument(
        "--config", dest="config_filepath", nargs=1, type=str,
        help="path to config file for creating experiment", required=False)
    parser.add_argument(
        "--experiment", dest="experiment_title", nargs=1, type=str,
        help="experiment title to add session", required=False)
    parser.add_argument(
        "--username", dest="username", nargs=1, type=str,
        help="specify the username of either subject or experimenter; if not "
             "exist, create one. In the case the action is create_experiment, "
             "the username is for the experimenter associated; for all other "
             "action, the username is for the test subject",
        required=False)
    parser.add_argument(
        "--session_id", dest="session_id", nargs=1, type=int,
        help="specify the session ID",
        required=False)
    args = parser.parse_args()
    action = args.action[0]
    config_filepath = args.config_filepath[0] if args.config_filepath else None
    experiment_title = args.experiment_title[0] if args.experiment_title else None
    username = args.username[0] if args.username else None
    session_id = args.session_id[0] if args.session_id else None

    if action == 'validate_config':
        assert config_filepath is not None
        assert experiment_title is None
        assert username is None
        assert session_id is None
        ExperimentUtils.validate_config(
            experiment_config_filepath=config_filepath)
        print(f"config file is valid: {config_filepath}")
    elif action == 'create_experiment':
        assert config_filepath is not None
        assert experiment_title is None, 'experiment_title is specified through config file'
        assert username is not None
        assert session_id is None
        ExperimentUtils.create_experiment(
            experiment_config_filepath=config_filepath,
            experimenter_username=username)
    elif action == 'delete_experiment':
        assert config_filepath is None
        assert experiment_title is not None
        assert username is None
        assert session_id is None
        ExperimentUtils.delete_experiment_by_title(
            experiment_title=experiment_title,
            is_test=False)
    elif action == 'add_session':
        assert config_filepath is None
        assert experiment_title is not None
        assert username is not None
        assert session_id is None
        ExperimentUtils.add_session_to_experiment(
            experiment_title=experiment_title,
            subject_username=username)
    elif action == 'delete_session':
        assert config_filepath is None
        assert experiment_title is not None
        assert username is None
        assert session_id is not None
        ExperimentUtils.delete_session_by_id(
            session_id=session_id,
            experiment_title=experiment_title)
    elif action == 'update_first_session_subject':
        assert config_filepath is None
        assert experiment_title is not None
        assert username is not None
        assert session_id is None
        ec = ExperimentUtils.get_experiment_controller(experiment_title)
        first_session = ec.experiment.session_set.first()
        ExperimentUtils.update_subject_for_session(
            experiment_title=experiment_title,
            session_id=first_session.id,
            subject_username=username)
    elif action == 'reset_unfinished_first_session':
        assert config_filepath is None
        assert experiment_title is not None
        assert username is None
        assert session_id is None
        ec = ExperimentUtils.get_experiment_controller(experiment_title)
        first_session = ec.experiment.session_set.first()
        ExperimentUtils.reset_unfinished_session(
            experiment_title=experiment_title,
            session_id=first_session.id)
    else:
        assert False, f"Unknown action: {action}"

    exit(0)
