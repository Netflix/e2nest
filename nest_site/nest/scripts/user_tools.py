#!/usr/bin/env python3

import argparse

import django

django.setup()

from nest.io import UserUtils, ExperimentUtils  # noqa: E402, I202


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--usernames", dest="usernames", nargs=1, type=str,
        help="list of usernames, separated by comma "
             "(e.g. zli@catflix.com,lkrasula@catflix.com)",
        required=True)
    parser.add_argument(
        "--action", dest="action", nargs=1, type=str,
        help="action to take, options: create_user, set_password",
        required=True)
    parser.add_argument(
        "--is_staff", dest="is_staff", action='store_true',
        help="set user as is_staff")
    parser.add_argument(
        "--is_superuser", dest="is_superuser", action='store_true',
        help="set user as is_superuser")
    parser.add_argument(
        "--password", dest="password", nargs=1, type=str,
        help="password")
    parser.add_argument(
        "--experiment", dest="experiment_title", nargs=1, type=str,
        help="experiment title to add session", required=False)
    args = parser.parse_args()
    usernames = args.usernames[0].split(',')
    action = args.action[0]
    is_staff = args.is_staff
    is_superuser = args.is_superuser
    password = args.password[0] if args.password else None
    experiment_title = args.experiment_title[0] if args.experiment_title else None

    if action == 'create_user':
        assert password is None
        assert experiment_title is None
        for username in usernames:
            UserUtils.create_user(username, is_staff, is_superuser)
    elif action == 'set_password':
        assert is_staff is False
        assert is_superuser is False
        assert password is not None
        assert experiment_title is None
        for username in usernames:
            UserUtils.set_password(username, password)
    elif action == 'create_user_and_password_and_add_session':
        assert experiment_title is not None
        assert password is not None
        for username in usernames:
            UserUtils.create_user(username, is_staff, is_superuser)
            UserUtils.set_password(username, password)
            ExperimentUtils.add_session_to_experiment(
                experiment_title=experiment_title,
                subject_username=username)
    else:
        assert False, f"Unknown action: {action}"

    exit(0)
