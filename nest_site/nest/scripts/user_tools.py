#!/usr/bin/env python3

import argparse

import django

django.setup()

from nest.io import UserUtils  # noqa: E402, I202


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
    args = parser.parse_args()
    usernames = args.usernames[0].split(',')
    action = args.action[0]
    is_staff = args.is_staff
    is_superuser = args.is_superuser
    password = args.password[0] if args.password else None

    if action == 'create_user':
        assert password is None
        for username in usernames:
            UserUtils.create_user(username, is_staff, is_superuser)
    elif action == 'set_password':
        assert is_staff is False
        assert is_superuser is False
        assert password is not None
        for username in usernames:
            UserUtils.set_password(username, password)
    else:
        assert False, f"Unknown action: {action}"

    exit(0)
