"""
This file is ment to be run to update the test_data set for the unit-tests of the CCDCOE package; a live connection
to an active providentia instance with test data is required!
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from ccdcoe.deployments.deployment_handler import DeploymentHandler

__LOCATION__ = os.path.dirname(os.path.realpath(__file__))


@dataclass
class ProvidentiaEndpoints:
    endpoint: str
    kwargs: dict


def store_data(path: str, data: dict):
    # create paths if not there
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(json.dumps(data))


if __name__ == "__main__":
    dh = DeploymentHandler()

    # patching PROJECT_VERSION to dummy
    dh.config.PROJECT_VERSION = "dummy"

    data_holder = {}

    providentia_endpoints = [
        ProvidentiaEndpoints("environments", {}),
        ProvidentiaEndpoints("environment", {"environment": "dummy"}),
        ProvidentiaEndpoints(
            "environment_hosts",
            {"environment": "dummy"},
        ),
        ProvidentiaEndpoints(
            "environment_hosts_id",
            {
                "environment": "dummy",
                "host_id": "web-target-1",
            },
        ),
        ProvidentiaEndpoints(
            "environment_inventory",
            {"environment": "dummy"},
        ),
        ProvidentiaEndpoints(
            "environment_networks",
            {"environment": "dummy"},
        ),
        ProvidentiaEndpoints(
            "environment_tags",
            {"environment": "dummy"},
        ),
        ProvidentiaEndpoints(
            "environment_actors",
            {"environment": "dummy"},
        ),
        ProvidentiaEndpoints(
            "environment_services",
            {"environment": "dummy"},
        ),
        ProvidentiaEndpoints(
            "environment_services_id",
            {
                "service_id": "test",
                "environment": "dummy",
            },
        ),
    ]

    for providentia_endpoint in providentia_endpoints:

        print(f"Fetching {providentia_endpoint.endpoint} data...")

        data_holder[providentia_endpoint.endpoint] = getattr(
            dh.providentia, providentia_endpoint.endpoint
        )(**providentia_endpoint.kwargs)

    print("Clearing owner information...")
    # clear owner in data
    cleared_results = []
    for each in data_holder["environment_inventory"]["result"]:
        each["owner"] = "REDACTED"
        cleared_results.append(each)
    data_holder["environment_inventory"]["result"] = cleared_results

    data_holder["environment_hosts_id"]["result"]["owner"] = "REDACTED"

    print("Updating providentia data on disk...")
    for k, v in data_holder.items():
        store_data(
            os.path.join(
                __LOCATION__,
                "providentia",
                dh.config.PROVIDENTIA_VERSION,
                k,
                "test_data.json",
            ),
            v,
        )
    print("Done with providentia data!")

    data_holder = {}

    print("Processing host_per_network data...")

    host_per_network = dh.get_hosts_per_network_providentia()

    for k, v in host_per_network.items():
        if "hosts" in v:
            cleared_results = []
            for each in v["hosts"]:
                each["owner"] = "REDACTED"
                cleared_results.append(each)
            v["hosts"] = cleared_results

    data_holder["host_per_network"] = host_per_network

    print("Processing gitlab_ci data...")
    data_holder["gitlab_ci"] = dh.get_gitlab_ci_from_tier_assignment()

    print("Processing tier assignments data...")
    data_holder["get_tier_assignments_providentia"] = (
        dh.get_tier_assignments_providentia()
    )

    print("Updating deployment handler outputs data on disk...")
    for k, v in data_holder.items():
        store_data(
            os.path.join(
                __LOCATION__,
                "deployment_handler",
                "outputs",
                k,
                "test_data.json",
            ),
            v,
        )
    print("Done with deployment handler data!")
