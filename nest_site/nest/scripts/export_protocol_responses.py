#!/usr/bin/env python3

import argparse

import django

django.setup()

from nest.io import ExperimentUtils  # noqa: E402, I202


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export protocol-level NEST response records as CSV.")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    controller = ExperimentUtils.get_experiment_controller(args.experiment)
    response_data = controller.denormalize_protocol_responses()
    response_data.to_csv(args.output, index=False)
    print(f"Exported {len(response_data)} response rows to {args.output}")
