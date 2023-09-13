#!/usr/bin/env python3

import argparse

import django
from nest.helpers import import_python_file

django.setup()

from nest.io import import_sureal_dataset  # noqa: E402, I202


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset", dest="dataset_path", nargs=1, type=str,
        help="input sureal-formatted dataset filepath", required=True)
    parser.add_argument(
        "--scale", dest="scale", nargs=1, type=str,
        help="voting scale, currently support: FIVE_POINT, 0_TO_100, 2AFC",
        required=True)
    parser.add_argument(
        "--new-dataset-name", dest="new_dataset_name", nargs=1, type=str,
        help="new dataset name to overwrite the old one. This is useful when "
             "importing the same dataset twice while needing to keep the "
             "dataset_name unique",
        required=False)
    parser.add_argument(
        "--experimenter", dest="experimenter_username", nargs=1, type=str,
        help="username of experimenter; if not exist, create a dummy one",
        required=False)
    parser.add_argument(
        "--write-config", dest="write_config", action='store_true',
        help="write config file to /media/experiment_config directory",
        required=False)

    args = parser.parse_args()
    dataset_path = args.dataset_path[0]
    scale = args.scale[0]
    new_dataset_name = args.new_dataset_name[0] \
        if args.new_dataset_name is not None else None
    experimenter_username = args.experimenter_username[0] \
        if args.experimenter_username is not None else None
    write_config = args.write_config
    dataset = import_python_file(dataset_path)
    if new_dataset_name is not None:
        dataset.dataset_name = new_dataset_name
    import_sureal_dataset(dataset, scale,
                          experimenter_username=experimenter_username,
                          write_config=write_config)
    exit(0)
