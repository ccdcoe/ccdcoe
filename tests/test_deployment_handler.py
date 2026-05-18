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

        result_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment()

        # verify the default output has the expected stages and job names
        assert result_gitlab_ci["stages"] == [
            "Tier2", "Tier3", "Tier4", "Tier5", "Tier6", "Tier7", "Tier8", "Tier9"
        ]
        expected_jobs = [
            "tier2a", "tier2b",
            "tier3a_core", "tier3b_core", "tier3c_core", "tier3d", "tier3e", "tier3f",
            "tier4a", "tier4b", "tier5a", "tier5b",
            "tier6a", "tier7a", "tier8a", "tier9a",
        ]
        assert [k for k in result_gitlab_ci if k != "stages"] == expected_jobs

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
        assert "needs" not in new_gitlab_ci["tier4a"]
        assert "CoreTiers" not in new_gitlab_ci["stages"]

        # --- deploy.sh is the last script entry in standard jobs ---
        default_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment()
        assert "deploy.sh" in default_gitlab_ci["tier2a"]["script"][-1]

        # --- forward needs wiring: same-stage jobs chain sequentially ---
        assert default_gitlab_ci["tier2b"]["needs"][0]["job"] == "tier2a"
        assert default_gitlab_ci["tier3b_core"]["needs"][0]["job"] == "tier3a_core"
        assert default_gitlab_ci["tier4b"]["needs"][0]["job"] == "tier4a"

        # --- runner tags: slim by default, fat/moad via large_tiers/clustered_tiers ---
        assert default_gitlab_ci["tier2a"]["tags"][0] is dh.config.TAG_RUNNER_SLIM
        ci_large = dh.get_gitlab_ci_from_tier_assignment(large_tiers=["TIER3"])
        assert ci_large["tier3f"]["tags"][0] is dh.config.TAG_RUNNER_FAT
        ci_clustered = dh.get_gitlab_ci_from_tier_assignment(clustered_tiers=["tier3f"])
        assert ci_clustered["tier3f"]["tags"][0] is dh.config.TAG_RUNNER_MOAD

        # --- skip_hosts: named host removed from matrix (raw name without team suffix) ---
        ci_skip = dh.get_gitlab_ci_from_tier_assignment(skip_hosts=["fw1-grp1"])
        assert "fw1-grp1_t28" not in ci_skip["tier2a"]["parallel"]["matrix"][0]["HOST"]
        assert "fw1-grp2_t28" in ci_skip["tier2a"]["parallel"]["matrix"][0]["HOST"]

        # --- only_hosts in a regular (non-standalone) deployment ---
        ci_only = dh.get_gitlab_ci_from_tier_assignment(only_hosts=["fw1-grp1"])
        assert ci_only["tier2a"]["parallel"]["matrix"][0]["HOST"] == ["fw1-grp1_t28"]
        assert ci_only["tier2b"]["parallel"]["matrix"][0]["HOST"] == []

        # --- actor filtering: only hosts belonging to the given actor are included ---
        # actor comparison is uppercase, matching host_actor.upper()
        ci_actor = dh.get_gitlab_ci_from_tier_assignment(actor=["GRP1"])
        assert "fw1-grp1_t28" in ci_actor["tier2a"]["parallel"]["matrix"][0]["HOST"]
        assert "fw1-grp2_t28" not in ci_actor["tier2a"]["parallel"]["matrix"][0]["HOST"]
        assert "dc1-grp1_t28" in ci_actor["tier3a_core"]["parallel"]["matrix"][0]["HOST"]
        # tier6a only has a 'gt' actor host — should be excluded
        assert ci_actor["tier6a"]["parallel"]["matrix"][0]["HOST"] == []

        new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(
            only_hosts=["test2"], standalone_deployment=True
        )
        assert new_gitlab_ci["stages"] == ["Tier0"]
        assert "test2" in new_gitlab_ci["tier0a"]["parallel"]["matrix"][0]["HOST"]

        new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(core_level=2)
        assert new_gitlab_ci["stages"][0] == "CoreTiers"
        assert new_gitlab_ci["stages"][1] == "Tier3"

        # --- core_level + reverse_deploy_order: CoreTiers stage appears last ---
        ci_core_rev = dh.get_gitlab_ci_from_tier_assignment(core_level=2, reverse_deploy_order=True)
        assert ci_core_rev["stages"][-1] == "CoreTiers"
        assert ci_core_rev["stages"][0] == "Tier9"

        # --- reverse_deploy_order: each job needs the next one, last job has no needs ---
        ci_rev = dh.get_gitlab_ci_from_tier_assignment(reverse_deploy_order=True)
        assert ci_rev["tier2a"]["needs"][0]["job"] == "tier2b"
        assert ci_rev["tier2b"]["needs"][0]["job"] == "tier3a_core"
        assert "needs" not in ci_rev["tier9a"]

        new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(
            core_level=2, windows_tier=3
        )
        assert new_gitlab_ci["stages"][0] == "CoreTiers"
        assert "order.sh" in new_gitlab_ci["tier3_core"]["script"][-1]
        assert new_gitlab_ci["tier3_core"]["needs"][0]["job"] == "tier2b"
        assert "dc1-grp1_t28 mail-grp1_t28 dc2-grp1_t28" in new_gitlab_ci["tier3_core"]["parallel"]["matrix"][1]["HOST"]

        # --- windows _core + required_tiers: tier3_core listed → no allow_failure;
        #     tier2a listed → no allow_failure; tier2b not listed → allow_failure ---
        ci_win_req = dh.get_gitlab_ci_from_tier_assignment(
            core_level=2, windows_tier=3, required_tiers=["tier2a", "tier3_core"]
        )
        assert "allow_failure" not in ci_win_req["tier3_core"]
        assert "allow_failure" not in ci_win_req["tier2a"]
        assert ci_win_req["tier2b"]["allow_failure"] is True

        with catch_logs(level=logging.DEBUG, logger=dh.logger) as handler:
            # creating new gitlab_ci with different settings
            new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(
                only_hosts=["test2"],
                large_tiers=["TIER2"],
                docker_image_count=2,
                windows_tier=2,
            )

            # test if warning was displayed
            assert records_to_tuples(handler.records)[3] == (
                dh.logger.name,
                logging.WARNING,
                "\x1b[33m[*] Tier 2 defined as Windows tier, but no Windows core hosts found, check your tier assignments\x1b[0m",
            )

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

        # required_tiers: all tiers should have allow_failure when not listed
        new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(
            required_tiers=["tier2a", "tier3"]
        )
        # tier2a is explicitly required
        assert "allow_failure" not in new_gitlab_ci["tier2a"]
        # tier2b is not required
        assert new_gitlab_ci["tier2b"]["allow_failure"] is True
        # tier3* are covered by the 'tier3' prefix
        assert "allow_failure" not in new_gitlab_ci["tier3a_core"]
        assert "allow_failure" not in new_gitlab_ci["tier3b_core"]
        assert "allow_failure" not in new_gitlab_ci["tier3d"]
        assert "allow_failure" not in new_gitlab_ci["tier3f"]
        # tier4+ are not required
        assert new_gitlab_ci["tier4a"]["allow_failure"] is True
        assert new_gitlab_ci["tier5a"]["allow_failure"] is True

        # required_tiers=None (default) must not add allow_failure to any job
        new_gitlab_ci = dh.get_gitlab_ci_from_tier_assignment(required_tiers=None)
        for key in ["tier2a", "tier2b", "tier3a_core", "tier4a"]:
            assert "allow_failure" not in new_gitlab_ci[key]

        # --- §4 windows needs wiring (core_level=2): tier3d gets needs for tier3_core ---
        ci_win_core = dh.get_gitlab_ci_from_tier_assignment(core_level=2, windows_tier=3)
        tier3d_needs_jobs = [n["job"] for n in ci_win_core["tier3d"].get("needs", [])]
        assert "tier3_core" in tier3d_needs_jobs
        assert "tier3c" in tier3d_needs_jobs  # chained from _wire_in_loop_needs

        # --- windows_tier without core_level: tier3_core job is in stage Tier3 ---
        ci_win_no_core = dh.get_gitlab_ci_from_tier_assignment(windows_tier=3)
        assert "tier3_core" in ci_win_no_core
        assert ci_win_no_core["tier3_core"]["stage"] == "Tier3"
        assert "CoreTiers" not in ci_win_no_core["stages"]
        # tier3d should need tier3c (inline) and tier3_core (§4 post-loop)
        tier3d_needs_no_core = [n["job"] for n in ci_win_no_core["tier3d"].get("needs", [])]
        assert "tier3_core" in tier3d_needs_no_core
        assert "tier3c" in tier3d_needs_no_core

        # --- docker_image_count + nova_version: image URL uses chosen count and env ---
        import random
        random.seed(42)
        ci_img = dh.get_gitlab_ci_from_tier_assignment(docker_image_count=3, nova_version="STAGING")
        assert "staging" in ci_img["tier2a"]["image"].lower()
        assert dh.config.NEXUS_HOST in ci_img["tier2a"]["image"]

        # --- dry_run=True: each job gets variables.DRY_RUN == "true" ---
        ci_dry = dh.get_gitlab_ci_from_tier_assignment(dry_run=True)
        assert ci_dry["tier2a"].get("variables", {}).get("DRY_RUN") == "true"
        assert ci_dry["tier9a"].get("variables", {}).get("DRY_RUN") == "true"
        # dry_run=False (default) must NOT add variables key
        assert "variables" not in default_gitlab_ci["tier2a"]

        # --- skip_hosts on a sequenced host: host_base is matched before || suffix ---
        ci_skip_seq = dh.get_gitlab_ci_from_tier_assignment(skip_hosts=["ws1-grp3"])
        tier3f_all_hosts = ci_skip_seq["tier3f"]["parallel"]["matrix"][0]["HOST"]
        assert not any("ws1-grp3" in h for h in tier3f_all_hosts), (
            "sequenced host ws1-grp3 should have been removed by skip_hosts"
        )
        assert any("ws2-grp1" in h for h in tier3f_all_hosts)

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
                    DEPLOY_DESCRIPTION="REDEPLOY Team 28 - LIMITED to Tier 0 - ",
                ),
                "Project pipeline for team 28(REDEPLOY Team 28 - LIMITED to Tier 0 - ) deployed -> pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
            pytest.param(
                {"team_number": 26, "tier_level": 4, "only_hosts": "web-target-1"},
                PipelineVars(
                    CICD_TEAM="26",
                    REDEPLOY_TIER4=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="REDEPLOY Team 26 - LIMITED to Tier 4 - LIMITED to hosts: web-target-1 - ",
                    ONLY_HOSTS="web-target-1",
                ),
                "Project pipeline for team 26(REDEPLOY Team 26 - LIMITED to Tier 4 - LIMITED to hosts: web-target-1 - ) deployed -> "
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
                    DEPLOY_DESCRIPTION="REDEPLOY Team 28 - FULL from Tier 4 to 8 - ",
                ),
                "Project pipeline for team 28(REDEPLOY Team 28 - FULL from Tier 4 to 8 - ) deployed -> "
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
                    DEPLOY_DESCRIPTION="REDEPLOY Team 28 - FULL up to Tier 8 - ACTOR: grp1 - ",
                ),
                "Project pipeline for team 28(REDEPLOY Team 28 - FULL up to Tier 8 - ACTOR: grp1 - ) "
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
                    DEPLOY_DESCRIPTION="REDEPLOY Team 26 - LIMITED to Tier 4 - SKIP hosts: web-target-1, web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahost-TRUNCATED",
                    SKIP_HOSTS="web-target-1, web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand3",
                ),
                "Project pipeline for team 26(REDEPLOY Team 26 - LIMITED to Tier 4 - SKIP hosts: web-target-1, web-target-2, wowthisisahostwithaverylongnameforsomereasonicannotunderstand, wowthisisahostwithaverylongnameforsomereasonicannotunderstand2, wowthisisahost-TRUNCATED) "
                "deployed -> pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
            pytest.param(
                {
                    "team_number": 26,
                    "tier_level": 4,
                    "skip_vulns": True,
                },
                PipelineVars(
                    CICD_TEAM="26",
                    REDEPLOY_TIER4=gitlab_boolean.ENABLED,
                    SKIP_VULNS=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="REDEPLOY Team 26 - LIMITED to Tier 4 - SKIP_VULNS - ",
                ),
                "Project pipeline for team 26(REDEPLOY Team 26 - LIMITED to Tier 4 - SKIP_VULNS - ) "
                "deployed -> pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
        ],
    )
    def test_dummy_team_deployment(
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

            with catch_logs(level=logging.INFO, logger=dh.logger) as handler:
                data = dh.deploy_team(**deploy_data)

                assert data is not None
                assert isinstance(data, FakeProjectPipeline)

                logged_messages = [record.message for record in handler.records]

                assert any(
                    deploy_msg in message for message in logged_messages
                ), f"Expected message '{deploy_msg}' not found in logs: {logged_messages}"

            mocked_function.assert_called_once_with(
                reference="main", variables=mock_pipeline_vars
            )

    @pytest.mark.parametrize(
        "job_name, required_tiers, expected",
        [
            # --- exact matches ---
            ("tier1a", ["tier1a"], True),
            ("tier1b", ["tier1a"], False),
            # --- parent prefix: sublevel letters ---
            ("tier1a", ["tier1"], True),
            ("tier1b", ["tier1"], True),
            # --- parent prefix: _core jobs ---
            ("tier3_core", ["tier3"], True),
            ("tier3a_core", ["tier3"], True),
            ("tier3ab_core", ["tier3"], True),
            # --- exact match for _core jobs ---
            ("tier3a_core", ["tier3a"], True),
            ("tier3b_core", ["tier3a"], False),
            # --- must NOT match digit after prefix (e.g. tier1 vs tier10a) ---
            ("tier10a", ["tier1"], False),
            ("tier10_core", ["tier1"], False),
            # --- multiple entries in required list ---
            ("tier2b", ["tier1", "tier2"], True),
            ("tier4a", ["tier1", "tier2"], False),
            # --- empty required list ---
            ("tier1a", [], False),
        ],
    )
    def test_tier_matches_required(self, job_name, required_tiers, expected):
        from ccdcoe.deployments.deployment_handler import DeploymentHandler

        assert DeploymentHandler._tier_matches_required(job_name, required_tiers) is expected
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
                {"only_hosts": "web-target-1"},
                PipelineVars(
                    CICD_TEAM="SA",
                    REDEPLOY_TIER0=gitlab_boolean.ENABLED,
                    DEPLOY_DESCRIPTION="REDEPLOY Standalone - LIMITED to hosts: web-target-1",
                    ONLY_HOSTS="web-target-1",
                    STANDALONE_DEPLOYMENT=gitlab_boolean.ENABLED,
                ),
                "Project pipeline for standalone deployment(REDEPLOY Standalone - LIMITED to hosts: web-target-1) deployed -> "
                "pipeline id fake_pipeline_id status: fake_pipeline_status ref: fake_pipeline_ref",
            ),
        ],
    )
    def test_dummy_standalone_deployment(
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

            with catch_logs(level=logging.INFO, logger=dh.logger) as handler:

                data = dh.deploy_standalone(**deploy_data)

                assert data is not None
                assert isinstance(data, FakeProjectPipeline)

                logged_messages = [record.message for record in handler.records]

                assert any(
                    deploy_msg in message for message in logged_messages
                ), f"Expected message '{deploy_msg}' not found in logs: {logged_messages}"

            mocked_function.assert_called_once_with(
                reference="main", variables=mock_pipeline_vars
            )
