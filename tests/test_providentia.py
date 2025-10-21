from dataclasses import dataclass
from typing import Any

import pytest
from requests import Response

from ccdcoe.deployments.deployment_config import Config
from ccdcoe.http_apis.providentia.providentia_api import ProvidentiaApi
from tests.helpers.skip_if import not_reachable

# noinspection PyUnusedImports
from tests.test_data_sets.providentia.v3 import *

reachable = pytest.mark.skipif(
    not_reachable(url=Config.PROVIDENTIA_URL.rstrip("/api")),
    reason="Skipping; cannot reach providentia instance",
)


@dataclass
class RequestParam:
    endpoint: str
    endpoint_kwargs: dict[str, Any]
    fixture: str


providentia_v3_fixtures = [
    RequestParam(
        endpoint="environments",
        endpoint_kwargs={},
        fixture="v3_environments_endpoint",
    ),
    RequestParam(
        endpoint="environment",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_endpoint",
    ),
    RequestParam(
        endpoint="environment_hosts",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_hosts_endpoint",
    ),
    RequestParam(
        endpoint="environment_hosts_id",
        endpoint_kwargs={
            "environment": "dummy",
            "host_id": "web-target-1",
        },
        fixture="v3_environment_hosts_id_endpoint",
    ),
    RequestParam(
        endpoint="environment_inventory",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_inventory_endpoint",
    ),
    RequestParam(
        endpoint="environment_networks",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_networks_endpoint",
    ),
    RequestParam(
        endpoint="environment_tags",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_tags_endpoint",
    ),
    RequestParam(
        endpoint="environment_actors",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_actors_endpoint",
    ),
    RequestParam(
        endpoint="environment_services",
        endpoint_kwargs={"environment": "dummy"},
        fixture="v3_environment_services_endpoint",
    ),
    RequestParam(
        endpoint="environment_services_id",
        endpoint_kwargs={
            "service_id": "test",
            "environment": "dummy",
        },
        fixture="v3_environment_services_id_endpoint",
    ),
]


@pytest.fixture(params=providentia_v3_fixtures)
def all_providentia_v3_fixtures(request):
    request.param.fixture = request.getfixturevalue(request.param.fixture)
    yield request.param


@reachable
class TestProvidentiaApi:
    @pytest.mark.parametrize(
        "endpoint, endpoint_kwargs",
        [
            pytest.param("environments", {"return_response_object": True}),
            pytest.param(
                "environment", {"environment": "dummy", "return_response_object": True}
            ),
            pytest.param(
                "environment_hosts",
                {"environment": "dummy", "return_response_object": True},
            ),
            pytest.param(
                "environment_hosts_id",
                {
                    "environment": "dummy",
                    "host_id": "web-target-1",
                    "return_response_object": True,
                },
            ),
            pytest.param(
                "environment_inventory",
                {"environment": "dummy", "return_response_object": True},
            ),
            pytest.param(
                "environment_networks",
                {"environment": "dummy", "return_response_object": True},
            ),
            pytest.param(
                "environment_tags",
                {"environment": "dummy", "return_response_object": True},
            ),
            pytest.param(
                "environment_actors",
                {"environment": "dummy", "return_response_object": True},
            ),
            pytest.param(
                "environment_services",
                {"environment": "dummy", "return_response_object": True},
            ),
            pytest.param(
                "environment_services_id",
                {
                    "service_id": "test",
                    "environment": "dummy",
                    "return_response_object": True,
                },
            ),
        ],
    )
    def test_providentia_v3_endpoint_response(self, endpoint, endpoint_kwargs):
        config = Config
        pa = ProvidentiaApi(
            baseurl=config.PROVIDENTIA_URL,
            api_path=config.PROVIDENTIA_VERSION,
            api_key=config.PROVIDENTIA_TOKEN,
        )

        r = getattr(pa, endpoint)(**endpoint_kwargs)

        assert isinstance(r, Response)
        assert r.status_code == 200

    def test_providentia_v3_endpoint_data(
        self,
        all_providentia_v3_fixtures,
    ):
        config = Config
        pa = ProvidentiaApi(
            baseurl=config.PROVIDENTIA_URL,
            api_path=config.PROVIDENTIA_VERSION,
            api_key=config.PROVIDENTIA_TOKEN,
        )

        r = getattr(pa, all_providentia_v3_fixtures.endpoint)(
            **all_providentia_v3_fixtures.endpoint_kwargs
        )

        # for certain endpoints owner data is REDACTED; bring this data in line with the test data
        if all_providentia_v3_fixtures.endpoint == "environment_inventory":
            cleared_results = []
            for each in r["result"]:
                each["owner"] = "REDACTED"
                cleared_results.append(each)
            r["result"] = cleared_results

        if all_providentia_v3_fixtures.endpoint == "environment_hosts_id":
            r["result"]["owner"] = "REDACTED"

        assert r == all_providentia_v3_fixtures.fixture
