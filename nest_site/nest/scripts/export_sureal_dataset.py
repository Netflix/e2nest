#!/usr/bin/env python3

import argparse

import django
from sureal.dataset_reader import DatasetReader

django.setup()

from nest.io import export_sureal_dataset  # noqa: E402, I202, I100

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--experiment", dest="experiment_title", nargs=1, type=str,
        help="title of experiment to export",
        required=True)
    parser.add_argument(
        "--output-dataset", dest="output_dataset_path", nargs=1, type=str,
        help="output sureal-formatted dataset filepath", required=True)

    args = parser.parse_args()
    experiment_title = args.experiment_title[0]
    output_dataset_path = args.output_dataset_path[0]
    dataset = export_sureal_dataset(experiment_title)
    DatasetReader.write_out_dataset(dataset, output_dataset_path)
    exit(0)
