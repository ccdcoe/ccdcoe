import logging
import os
from dataclasses import dataclass
from unittest import mock
from unittest.mock import Mock

import pytest
from gitlab import Gitlab
from gitlab.v4.objects import Project

from ccdcoe.deployments.deployment_config import Config
from ccdcoe.deployments.generic.constants import gitlab_boolean
from ccdcoe.deployments.objects.pipeline_vars import PipelineVars
from ccdcoe.deployments.objects.tiers import Tier1, FullTier2
from tests.helpers.capture_logging import catch_logs, records_to_tuples
from tests.test_data_sets.deployment_handler.outputs.get_tier_assignments_providentia.fixtures import (
    get_tier_assignments_providentia,
)
from tests.test_data_sets.deployment_handler.outputs.gitlab_ci.fixtures import gitlab_ci
from tests.test_data_sets.deployment_handler.outputs.host_per_network.fixtures import (
    host_per_network,
)
from tests.test_data_sets.providentia.v3.environment_inventory.environment_inventory import (
    v3_environment_inventory_endpoint,
)
from tests.test_data_sets.providentia.v3.environment_networks.environment_networks import (
    v3_environment_networks_endpoint,
)


@dataclass
class FakeProjectPipeline:
    id: str = "fake_pipeline_id"
    status: str = "fake_pipeline_status"
    ref: str = "fake_pipeline_ref"


class FakeConfig(Config):
    TRIGGER_TOKEN = "test_trigger_token"
    PAT_TOKEN = "test_pat_token"
    GITLAB_URL = "http://localhost:5001"
    NEXUS_HOST = "nexus-hosted.localhost"
    PROVIDENTIA_TOKEN = "test_providentia_token"
    PROVIDENTIA_URL = "http://localhost:5000/api"
    PROJECT_ROOT = "ls"
    PROJECT_VERSION = "ls25"


@pytest.fixture
def mock_config_object():
    with mock.patch(
        "ccdcoe.deployments.deployment_handler.Config", new_callable=FakeConfig
    ):
        yield


class TestDeploymentHandler:
    def test_providentia_v3_settings(self, mock_config_object):
        os.environ["PROVIDENTIA_VERSION"] = "v3"
        from ccdcoe.deployments.deployment_handler import DeploymentHandler

        dh = DeploymentHandler()

        assert dh.providentia.baseurl == "http://localhost:5000/api"
        assert dh.providentia.api_path == "v3"
        assert (
            dh.providentia.headers["Authorization"] == "Bearer test_providentia_token"
        )

    def test_gitlab_settings(self, mock_config_object):
        from ccdcoe.deployments.deployment_handler import DeploymentHandler

        dh = DeploymentHandler()

        gitlab_obj = dh.get_gitlab_obj()

        assert isinstance(gitlab_obj, Gitlab)
        assert gitlab_obj.private_token == "test_pat_token"
        assert gitlab_obj.url == "http://localhost:5001"

        get_project = dh.get_project_by_namespace(namespace="ls")

        assert isinstance(get_project, Project)
        assert get_project._lazy

    @mock.patch(
        "ccdcoe.deployments.deployment_handler.ProvidentiaApi.environment_networks"
    )
    @mock.patch(
        "ccdcoe.deployments.deployment_handler.ProvidentiaApi.environment_inventory"
    )
    def test_deployment_handler(
        self,
        prov_env_inventory,
        prov_env_networks,
        mock_config_object,
        get_tier_assignments_providentia,
        v3_environment_inventory_endpoint,
        gitlab_ci,
        host_per_network,
        v3_environment_networks_endpoint,
    ):
        # mocking return to test_data
        prov_env_inventory.return_value = v3_environment_inventory_endpoint
        prov_env_networks.return_value = v3_environment_networks_endpoint

        from ccdcoe.deployments.deployment_handler import DeploymentHandler

        dh = DeploymentHandler()

        tier_data = dh.get_tier_assignments_providentia()

        # testing output against test_data
        assert tier_data == get_tier_assignments_providentia

        gitlab_ci = dh.get_gitlab_ci_from_tier_assignment()

        # testing output against test_data
        assert gitlab_ci == gitlab_ci

        with catch_logs(level=logging.DEBUG, logger=dh.logger) as handler:
            # creating new gitlab_ci with different settings
            new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(
                skip_hosts=["test"],
                only_hosts=["test2"],
                large_tiers=["TIER2"],
                reverse_deploy_order=True,
                docker_image_count=2,
            )

            # test if warning was displayed
            assert records_to_tuples(handler.records)[-2] == (
                dh.logger.name,
                logging.WARNING,
                "\x1b[33m[*] Warning: Both --skip_hosts and --only_hosts provided; --only_hosts takes precedence\x1b[0m",
            )

        new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(ignore_deploy_order=True)
        assert "needs" not in new_gitlab_ci["tier3b"]

        # testing fetching tiers
        assert isinstance(dh.get_tier(1), Tier1)
        assert isinstance(dh.get_tier(2, True), FullTier2)

        from ccdcoe.deployments.deployment_handler import __UNIQUE_TIERS__

        assert dh.get_tier(retrieve_all=True) == {
            k: v().as_dict() for (k, v) in __UNIQUE_TIERS__.items()
        }
        assert dh.get_tier(retrieve_all=True, show_bear_level=True) == {
            k: v().show_bear_level() for (k, v) in __UNIQUE_TIERS__.items()
        }

        # testing hosts per network
        host_per_network = dh.get_hosts_per_network_providentia()

        assert host_per_network == host_per_network

        all_hosts = []
        for k, v in host_per_network.items():
            if "hosts" in v:
                all_hosts.extend(
                    [
                        x
                        for x in v["hosts"]
                        if x["actor_id"] != "gt" and x["actor_id"] != "for"
                    ]
                )

        assert len(all_hosts) == len(
            [
                x
                for x in v3_environment_inventory_endpoint["result"]
                if x["actor_id"] != "gt" and x["actor_id"] != "for"
            ]
        )

    @mock.patch(
        "ccdcoe.deployments.deployment_handler.ProvidentiaApi.environment_networks"
    )
    @mock.patch(
        "ccdcoe.deployments.deployment_handler.ProvidentiaApi.environment_inventory"
    )
    @pytest.mark.parametrize(
        "deploy_data, mock_pipeline_vars, deploy_msg",
        [
            pytest.param(
                {},
                PipelineVars(
                    REDEPLOY_TIER0=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="LIMITED to Tier 0, skip_vulns: False, skip_hosts: ",
                ),
                "Project pipeline for team 28(LIMITED to Tier 0, skip_vulns: False, skip_hosts: ) deployed -> pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
            pytest.param(
                {"team_number": 26, "tier_level": 4, "only_hosts": "web-target-1"},
                PipelineVars(
                    CICD_TEAM="26",
                    REDEPLOY_TIER4=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="LIMITED to hosts: web-target-1, skip_vulns: False",
                    ONLY_HOSTS="web-target-1",
                ),
                "Project pipeline for team 26(LIMITED to hosts: web-target-1, skip_vulns: False) deployed -> "
                "pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
            pytest.param(
                {"tier_level": 8, "deploy_full_tier": True, "start_tier_level": 4},
                PipelineVars(
                    REDEPLOY_TIER4=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER5=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER6=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER7=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER8=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="FULL from Tier 4 to 8, skip_vulns: False, skip_hosts: ",
                ),
                "Project pipeline for team 28(FULL from Tier 4 to 8, skip_vulns: False, skip_hosts: ) deployed -> "
                "pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
            pytest.param(
                {"tier_level": 8, "deploy_full_tier": True, "actor": "grp1"},
                PipelineVars(
                    REDEPLOY_TIER0=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER1=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER2=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER3=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER4=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER5=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER6=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER7=gitlab_boolean.ENABLED,
                    REDEPLOY_TIER8=gitlab_boolean.ENABLED,
                    ACTOR="grp1",
                    DEPLOY_DESCRIPTION="FULL up to Tier 8, skip_vulns: False, skip_hosts: , actor: grp1",
                ),
                "Project pipeline for team 28(FULL up to Tier 8, skip_vulns: False, skip_hosts: , actor: grp1) "
                "deployed -> pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
            pytest.param(
                {
                    "team_number": 26,
                    "tier_level": 4,
                    "skip_hosts": "web-target-1, web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand3",
                },
                PipelineVars(
                    CICD_TEAM="26",
                    REDEPLOY_TIER4=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="LIMITED to Tier 4, skip_vulns: False, skip_hosts: web-target-1, "
                    "web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, "
                    "wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahostw-TRUNCATED",
                    SKIP_HOSTS="web-target-1, web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand3",
                ),
                "Project pipeline for team 26(LIMITED to Tier 4, skip_vulns: False, skip_hosts: web-target-1, "
                "web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, "
                "wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahostw-TRUNCATED) "
                "deployed -> pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
        ],
    )
    def test_dummy_deployment(
        self,
        prov_env_inventory,
        prov_env_networks,
        deploy_data,
        mock_config_object,
        v3_environment_inventory_endpoint,
        v3_environment_networks_endpoint,
        mock_pipeline_vars,
        deploy_msg,
    ):
        # mocking return to test_data
        prov_env_inventory.return_value = v3_environment_inventory_endpoint
        prov_env_networks.return_value = v3_environment_networks_endpoint

        from ccdcoe.deployments.deployment_handler import DeploymentHandler

        dh = DeploymentHandler()

        mock_deployment = Mock()

        with mock.patch(
            "ccdcoe.deployments.deployment_handler.DeploymentHandler.trigger_deployment_pipeline",
            side_effect=mock_deployment,
        ) as mocked_function:
            mock_deployment.return_value = FakeProjectPipeline()

            data = dh.deploy_team(**deploy_data)

            assert data == deploy_msg
            mocked_function.assert_called_once_with(
                reference="main", variables=mock_pipeline_vars
            )
