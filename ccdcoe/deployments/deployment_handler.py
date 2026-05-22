import datetime
import inspect
import logging
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Tuple

import gitlab
from gitlab import Gitlab
from gitlab.v4.objects import Project, ProjectPipeline, ProjectPipelineSchedule
from tqdm import tqdm

from ccdcoe.deployments.deployment_config import Config
from ccdcoe.deployments.generic.constants import deploy_modes, gitlab_boolean
from ccdcoe.deployments.objects.pipeline_details import (
    PipelineDetails,
    PipelineScheduleDetails,
)
from ccdcoe.deployments.objects.pipeline_vars import PipelineVars
from ccdcoe.deployments.objects.tiers import (
    Tiers,
    Tier1,
    Tier0,
    Tier2,
    Tier3,
    Tier4,
    Tier5,
    Tier6,
    Tier7,
    Tier8,
    Tier9,
    FullTier1,
    FullTier4,
    FullTier2,
    FullTier3,
    FullTier5,
    FullTier6,
    FullTier7,
    FullTier8,
    FullTier9,
)
from ccdcoe.generic.utils import getenv_str
from ccdcoe.http_apis.providentia.providentia_api import ProvidentiaApi
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

__UNIQUE_TIERS__ = {
    0: Tier0,
    1: Tier1,
    2: Tier2,
    3: Tier3,
    4: Tier4,
    5: Tier5,
    6: Tier6,
    7: Tier7,
    8: Tier8,
    9: Tier9,
}
__FULL_TIERS__ = {
    0: Tier0,
    1: FullTier1,
    2: FullTier2,
    3: FullTier3,
    4: FullTier4,
    5: FullTier5,
    6: FullTier6,
    7: FullTier7,
    8: FullTier8,
    9: FullTier9,
}

team_regex = re.compile(r"Team (\d+)")


@dataclass
class PipelineFilter:
    pipelines: list[ProjectPipeline]

    def filter_pipelines(
        self, team_number: int
    ) -> list[ProjectPipeline]:  # pragma: no cover
        filtered_pipelines = []
        for pipeline in self.pipelines:
            m = team_regex.search(pipeline.name)
            if m is not None:
                if int(m.groups()[0]) == team_number:
                    filtered_pipelines.append(pipeline)
        return filtered_pipelines

    def filter_pipelines_return_details(
        self, team_number: int
    ) -> list[PipelineDetails]:  # pragma: no cover
        filtered_pipelines = []
        for pipeline in self.pipelines:
            m = team_regex.search(pipeline.name)
            if m is not None:
                if int(m.groups()[0]) == team_number:
                    filtered_pipelines.append(
                        PipelineDetails(
                            pipeline.id,
                            pipeline.name,
                            pipeline.ref,
                            pipeline.status,
                            pipeline.web_url,
                            pipeline.updated_at,
                        )
                    )
        return filtered_pipelines

    def pipelines_return_details(self):
        filtered_pipelines = []
        for pipeline in self.pipelines:
            filtered_pipelines.append(
                PipelineDetails(
                    pipeline.id,
                    pipeline.name,
                    pipeline.ref,
                    pipeline.status,
                    pipeline.web_url,
                    pipeline.updated_at,
                )
            )
        return filtered_pipelines


class DeploymentHandler(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.config = Config

        self.providentia = ProvidentiaApi(
            baseurl=self.config.PROVIDENTIA_URL,
            api_path=self.config.PROVIDENTIA_VERSION,
            api_key=self.config.PROVIDENTIA_TOKEN,
        )

    def __repr__(self):
        return "<<DeploymentHandler>>"

    def get_gitlab_obj(self) -> Gitlab:
        return Gitlab(url=self.config.GITLAB_URL, private_token=self.config.PAT_TOKEN)

    def get_project_by_namespace(
        self, namespace: str, lazy: bool = True, **kwargs
    ) -> Project:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        with self.get_gitlab_obj() as gl:
            project = gl.projects.get(namespace, lazy=lazy, **kwargs)

        return project

    def trigger_deployment_pipeline(
        self, reference: str = "main", variables: PipelineVars = None, **kwargs
    ) -> ProjectPipeline:  # pragma: no cover

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        if variables is not None:
            if not isinstance(variables, PipelineVars):
                raise TypeError(f"'variables' is not a PipelineVars object...")
        try:

            pipeline_project = self.get_project_by_namespace(
                self.config.PROJECT_NAMESPACE
            )
            variables_dict = {k: str(v) for k, v in variables.as_dict().items()}

            variables_dict["CI_CONFIG_PATH"] = getenv_str(
                "CI_CONFIG_PATH", ".gitlab-ci.yml"
            )

            return pipeline_project.trigger_pipeline(
                ref=reference,
                token=self.config.TRIGGER_TOKEN,
                variables=variables_dict,
                **kwargs,
            )
        except gitlab.exceptions.GitlabCreateError as e:
            self.logger.error(f"Pipeline could not be triggered -> {e}")
        except Exception as e:
            self.logger.error(f"Uncaught exception while triggering pipeline -> {e}")

    def custom_deployment(
        self, reference: str = "main", variables: dict[str, Any] = None, **kwargs
    ) -> ProjectPipeline:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        if variables is not None:
            try:
                variables = PipelineVars(**variables)
            except ValueError:
                raise
            except Exception as e:
                self.logger.error(f"Uncaught exception parsing variables -> {e}")

        return self.trigger_deployment_pipeline(
            reference=reference, variables=variables, **kwargs
        )

    # noinspection PyArgumentList
    def get_tier(
        self,
        tier_level: int = 0,
        give_back_full: bool = False,
        retrieve_all: bool = False,
        show_bear_level: bool = False,
    ) -> Tiers | dict[int, dict[str, str]]:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        if retrieve_all:
            if show_bear_level:
                return {k: v().show_bear_level() for (k, v) in __UNIQUE_TIERS__.items()}
            else:
                return {k: v().as_dict() for (k, v) in __UNIQUE_TIERS__.items()}
        else:
            if give_back_full:
                return __FULL_TIERS__[tier_level]()
            else:
                return __UNIQUE_TIERS__[tier_level]()

    def deploy_team(
        self,
        reference: str = "main",
        team_number: int = 28,
        tier_level: int = 0,
        start_tier_level: int = 0,
        deploy_full_tier: bool = False,
        deploy_mode: str = deploy_modes.REDEPLOY,
        skip_vulns: bool = False,
        snapshot: bool = True,
        snap_name: str = "CLEAN",
        skip_hosts: str = "",
        only_hosts: str = "",
        actor: str = "",
        large_tiers: str = "",
        standalone_tiers: str = "",
        ignore_deploy_order: bool = False,
        reverse_deploy_order: bool = False,
        docker_image_count: int = 1,
        nova_version: str = "PRODUCTION",
        core_level: int = 0,
        windows_tier: str = "",
        return_pipeline_object: bool = True,
        ansible_extra_vars: str = "",
        dry_run: bool = False,
    ) -> ProjectPipeline:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        try:
            the_tier = self.get_tier(
                tier_level=tier_level, give_back_full=deploy_full_tier
            )

            if only_hosts:
                only_hosts_list = only_hosts.split(",")

                tier_assignments = self.get_tier_assignments_providentia()
                tiers = list(tier_assignments.keys())
                for tl in range(0, len(__UNIQUE_TIERS__)):
                    setattr(the_tier, f"REDEPLOY_TIER{tl}", gitlab_boolean.DISABLED)
                for i, tier in enumerate(tiers):
                    # Extract just the base tier name (e.g., "Tier3" from "Tier3A_CORE")
                    match = re.search(r"tier\d+", tier, re.IGNORECASE)
                    if match:
                        top_level_tier = match.group(0)
                    else:
                        # Fallback to original behavior if pattern doesn't match
                        top_level_tier = re.sub(r"[a-zA-Z_]+$", "", tier)
                    for host in tier_assignments[tier]:
                        if list(host.keys())[0] in only_hosts_list:
                            setattr(
                                the_tier,
                                f"REDEPLOY_{top_level_tier.upper()}",
                                gitlab_boolean.ENABLED,
                            )

            if start_tier_level != 0:
                for tl in range(0, start_tier_level):
                    setattr(the_tier, f"REDEPLOY_TIER{tl}", gitlab_boolean.DISABLED)

            tier_data = the_tier.as_dict()
            tier_data["CICD_TEAM"] = team_number
            tier_data["DEPLOY_MODE"] = deploy_mode
            tier_data["SKIP_VULNS"] = skip_vulns
            tier_data["SNAPSHOT"] = snapshot
            tier_data["SNAPSHOT_NAME"] = snap_name
            tier_data["SKIP_HOSTS"] = skip_hosts
            tier_data["ONLY_HOSTS"] = only_hosts
            tier_data["ACTOR"] = actor
            tier_data["LARGE_TIERS"] = large_tiers
            tier_data["STANDALONE_TIERS"] = standalone_tiers
            tier_data["IGNORE_DEPLOY_ORDER"] = ignore_deploy_order
            tier_data["REVERSE_DEPLOY_ORDER"] = reverse_deploy_order
            tier_data["DOCKER_IMAGE_COUNT"] = docker_image_count
            tier_data["NOVA_VERSION"] = nova_version
            tier_data["CORE_LEVEL"] = core_level
            tier_data["WINDOWS_TIER"] = windows_tier
            tier_data["ANSIBLE_EXTRA_VARS"] = ansible_extra_vars
            tier_data["DRY_RUN"] = dry_run

            if dry_run:
                description = f"DRY RUN {deploy_mode.upper()} Team {team_number} - "
            else:
                description = f"{deploy_mode.upper()} Team {team_number} - "

            if deploy_full_tier:
                if start_tier_level == 0:
                    description += f"FULL up to Tier {tier_level} - "
                else:
                    description += (
                        f"FULL from Tier {start_tier_level} to {tier_level} - "
                    )
            else:
                description += f"LIMITED to Tier {tier_level} - "

            if skip_vulns:
                description += f"SKIP_VULNS - "

            if only_hosts:
                description += f"LIMITED to hosts: {only_hosts} - "

            if skip_hosts:
                description += f"SKIP hosts: {skip_hosts} - "

            if actor:
                description += f"ACTOR: {actor} - "

            if nova_version == "STAGING":
                description += f"NOVA_VERSION: STAGING - "

            if ansible_extra_vars != "":
                description += f"EXTRA_VARS: {ansible_extra_vars} - "

            if len(description) >= 255:
                description = (
                    description[:220] + "-TRUNCATED"
                )  # accounting for 'deploy_mode Team xx' as well

            tier_data["DEPLOY_DESCRIPTION"] = description

            project_pipeline = self.custom_deployment(
                reference=reference, variables=tier_data
            )
            if project_pipeline is not None:
                msg = (
                    f"Project pipeline for team {team_number}({description}) deployed -> "
                    f"pipeline id {project_pipeline.id} status: {project_pipeline.status} ref: {project_pipeline.ref}"
                )
                self.logger.info(msg)
                if return_pipeline_object:
                    return project_pipeline
                else:
                    return msg
        except Exception as e:
            self.logger.error(f"Uncaught exception -> {e}")

    def deploy_standalone(
        self,
        reference: str = "main",
        deploy_mode: str = deploy_modes.REDEPLOY,
        skip_vulns: bool = False,
        snapshot: bool = True,
        snap_name: str = "CLEAN",
        only_hosts: str = "",
        return_pipeline_object: bool = True,
        ansible_extra_vars: str = "",
    ) -> ProjectPipeline:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        try:
            the_tier = self.get_tier()

            tier_data = the_tier.as_dict()
            tier_data["CICD_TEAM"] = "SA"
            tier_data["DEPLOY_MODE"] = deploy_mode
            tier_data["SKIP_VULNS"] = skip_vulns
            tier_data["SNAPSHOT"] = snapshot
            tier_data["SNAPSHOT_NAME"] = snap_name
            tier_data["ONLY_HOSTS"] = only_hosts
            tier_data["STANDALONE_DEPLOYMENT"] = gitlab_boolean.ENABLED
            tier_data["ANSIBLE_EXTRA_VARS"] = ansible_extra_vars

            description = f"{deploy_mode.upper()} Standalone - "

            if skip_vulns:
                description += f"SKIP_VULNS - "

            if only_hosts:
                description += f"LIMITED to hosts: {only_hosts}"

            if ansible_extra_vars != "":
                description += f"EXTRA_VARS: {ansible_extra_vars} - "

            if len(description) >= 255:
                description = (
                    description[:220] + "-TRUNCATED"
                )  # accounting for 'deploy_mode Team xx' as well

            tier_data["DEPLOY_DESCRIPTION"] = description

            project_pipeline = self.custom_deployment(
                reference=reference, variables=tier_data
            )
            if project_pipeline is not None:
                msg = (
                    f"Project pipeline for standalone deployment({description}) deployed -> "
                    f"pipeline id {project_pipeline.id} status: {project_pipeline.status} ref: {project_pipeline.ref}"
                )
                self.logger.info(msg)
                if return_pipeline_object:
                    return project_pipeline
                else:
                    return msg
        except Exception as e:
            self.logger.error(f"Uncaught exception -> {e}")

    def get_last_deployment_pipeline(
        self,
        reference: str = "main",
        team_number: int = 28,
        update_delta_in_hours: int = 4,
        return_pipeline_details: bool = True,
    ) -> ProjectPipeline | list[PipelineDetails] | None:  # pragma: no cover
        """
        in order to limit the amount of records coming back; a time cap is used; so this command only fetches the
        results from pipelines that are updated the last 4 hours (default; can be controlled via the \
        'update_delta_in_hours' variable). If that yields more then 1 result; it will return the last entry.
        """
        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        date_time = datetime.datetime.now()
        date_time_delta = datetime.timedelta(hours=update_delta_in_hours)

        iso_formatted_delta = (date_time - date_time_delta).isoformat()

        the_project = self.get_project_by_namespace(self.config.PROJECT_NAMESPACE)

        pipelines = the_project.pipelines.list(
            ref=reference,
            get_all=True,
            updated_after=iso_formatted_delta,
        )

        pf = PipelineFilter(pipelines=pipelines)

        if len(pipelines) == 0:
            return None

        if return_pipeline_details:
            return pf.filter_pipelines_return_details(team_number=team_number)
        else:
            return pipelines[0]

    def get_pipeline_by_id(
        self,
        pipeline_id: int | str,
    ) -> ProjectPipeline | None:  # pragma: no cover

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        try:
            the_project = self.get_project_by_namespace(self.config.PROJECT_NAMESPACE)

            pipeline = the_project.pipelines.get(pipeline_id)

            self.logger.debug(f"Fetched pipeline with id {pipeline_id}: {pipeline}")
            return pipeline

        except gitlab.exceptions.GitlabGetError as e:
            self.logger.error(
                f"Pipeline with id {pipeline_id} could not be fetched -> {e}"
            )
            return None

    def get_deployment_status(
        self,
        reference: str = "main",
        team_number: int | list[int] = 28,
        fetch_all: bool = False,
        pipeline_id: int | str = None,
    ) -> Tuple[list[str], list[str]]:  # pragma: no cover

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        header_list = ["ID", "Name", "Status", "Branch", "Updated", "Url"]
        entry_list = []
        if fetch_all:
            for i in tqdm(
                range(
                    self.config.DEPLOYMENT_RANGE_LOWER,
                    self.config.DEPLOYMENT_RANGE_UPPER + 1,
                ),
                desc="Fetching deployment status",
            ):
                details_obj = self.get_last_deployment_pipeline(
                    reference=reference, team_number=i, return_pipeline_details=True
                )
                if details_obj is not None:
                    entry_list.extend([x.get_entry_list() for x in details_obj])
        else:
            if pipeline_id is None:
                if isinstance(team_number, int):
                    team_number = [team_number]
                if len(team_number) == 1:
                    for each in team_number:
                        details_obj = self.get_last_deployment_pipeline(
                            reference=reference,
                            team_number=each,
                            return_pipeline_details=True,
                        )
                        if details_obj is not None:
                            entry_list.extend([x.get_entry_list() for x in details_obj])
                else:
                    for each in tqdm(
                        team_number,
                        desc="Fetching deployment status",
                    ):
                        details_obj = self.get_last_deployment_pipeline(
                            reference=reference,
                            team_number=each,
                            return_pipeline_details=True,
                        )
                        if details_obj is not None:
                            entry_list.extend([x.get_entry_list() for x in details_obj])
            else:
                pipeline_obj = self.get_pipeline_by_id(pipeline_id=pipeline_id)
                if pipeline_obj is not None:
                    details_obj = PipelineDetails(
                        pipeline_obj.id,
                        pipeline_obj.name,
                        pipeline_obj.ref,
                        pipeline_obj.status,
                        pipeline_obj.web_url,
                        pipeline_obj.updated_at,
                    )
                    entry_list.extend([details_obj.get_entry_list()])

        return header_list, entry_list

    def get_hosts_per_network_providentia(
        self,
    ) -> dict[dict, dict[str, Any] | list[dict[str, Any]]]:

        self.logger.info(f"Fetching all networks...")
        all_networks = self.providentia.environment_networks(
            self.config.PROVIDENTIA_ENVIRONMENT
        )

        target_networks = [
            network
            for network in all_networks["result"]
            if network["actor"] not in ["gt", "for", "rt"] and network["id"] != "vpn_bt"
        ]

        self.logger.info(f"Found {len(target_networks)} networks...")

        host_per_network = defaultdict(dict)

        for network in target_networks:
            host_per_network[network["id"]] = {"network_details": network}

        host_per_network = dict(host_per_network)

        self.logger.info(f"Fetching all hosts...")

        host_inventory = self.providentia.environment_inventory(
            self.config.PROVIDENTIA_ENVIRONMENT
        )

        all_hosts = [
            x
            for x in host_inventory["result"]
            if x["actor_id"] != "gt" or x["actor_id"] != "for"
        ]

        for host in all_hosts:
            try:
                if "hosts" not in host_per_network[host["connection_network"]]:
                    host_per_network[host["connection_network"]]["hosts"] = []

                host_per_network[host["connection_network"]]["hosts"].append(host)
            except KeyError:
                continue

        return dict(sorted(host_per_network.items()))

    def get_tier_assignments_providentia(self):

        tier_regex = re.compile(r"custom_tier.*")

        self.logger.info(f"Fetching inventory from providentia...")

        the_inventory = self.providentia.environment_inventory(
            self.config.PROVIDENTIA_ENVIRONMENT
        )

        ret_dict = defaultdict(list)

        for host in the_inventory["result"]:
            tag_list = sorted(
                list(filter(tier_regex.match, host["tags"])), reverse=True
            )
            if len(tag_list) != 0:
                if len(tag_list) > 1:
                    self.logger.error(
                        f"Found multiple tags for {host['id']} -> {tag_list}; "
                        f"only processing the first (lowest tier!!) entry!!"
                    )
                # match on tier tag
                tier_level = tag_list[0].replace("custom_", "").title()
                if len(tier_level) > 7:
                    # tier with 2 sub-levels do some additional work....
                    top_tier_level = tier_level[:4]
                    sub_level = tier_level[5:7].upper()
                    second_sub_level = tier_level[8:].upper()
                    full_tier_level = (
                        top_tier_level + sub_level + "_" + second_sub_level
                    )
                elif len(tier_level) > 6:
                    # tier with sub-level do some additional work....
                    top_tier_level = tier_level[:4]
                    sub_level = tier_level[-2:].upper()
                    full_tier_level = top_tier_level + sub_level
                else:
                    top_tier_level = tier_level[:4]
                    sub_level = tier_level[-1]
                    full_tier_level = top_tier_level + sub_level
                if host["sequence_total"] is not None:
                    host_id = f"{host['id']}||{host['sequence_total']}"
                else:
                    host_id = host["id"]

                ret_dict[full_tier_level].append({host_id: {"actor": host["actor_id"]}})

        full_dict = dict(ret_dict)

        for key, value in full_dict.items():
            full_dict[key] = sorted(value, key=lambda d: list(d.keys())[0])

        # for key, value in full_dict.items():
        #     full_dict[key] = sorted(value)

        return dict(sorted(full_dict.items()))

    # Matches valid suffixes after a tier prefix:
    # - '' (exact), 'a', 'ab', ... (sublevel letters)
    # - '_core' (e.g. tier3_core)
    # - 'a_core', 'ab_core', ... (e.g. tier3a_core, tier3ab_core)
    _TIER_SUFFIX_RE = re.compile(r"^[a-zA-Z]*(_core)?$")

    @classmethod
    def _tier_matches_required(cls, job_name: str, required_tiers: list[str]) -> bool:
        """
        Return True if job_name is covered by any entry in required_tiers.
        Supports:
        - Exact match:          'tier1a'  matches 'tier1a'
        - Sublevel prefix:      'tier1'   matches 'tier1a', 'tier1b', ...
        - Core-job prefix:      'tier3'   matches 'tier3a_core'
        - Exact core match:     'tier3a'  matches 'tier3a_core'
        Does NOT match digits after the prefix (e.g. 'tier1' does NOT match 'tier10a').
        """
        for req in required_tiers:
            if job_name == req:
                return True
            if job_name.startswith(req):
                suffix = job_name[len(req) :]
                if cls._TIER_SUFFIX_RE.match(suffix) and suffix != "":
                    return True
        return False

    @staticmethod
    def _build_deploy_script() -> list[str]:
        return [
            r'printf "\e[1m\e[36m--- Deploy job variables ---\n'
            r"HOST:                 $HOST\n"
            r"DEPLOY_MODE:          $DEPLOY_MODE\n"
            r"SKIP_VULNS:           $SKIP_VULNS\n"
            r"SNAPSHOT:             $SNAPSHOT\n"
            r"SNAPSHOT_NAME:        $SNAPSHOT_NAME\n"
            r"ANSIBLE_EXTRA_VARS:   $ANSIBLE_EXTRA_VARS\n"
            r"DRY_RUN:              $DRY_RUN\n"
            r'----------------------------\n\e[0m"',
            "bash /app/deploy.sh"
            ' --host "$HOST"'
            ' --mode "$DEPLOY_MODE"'
            ' --skip-vulns "$SKIP_VULNS"'
            ' --snapshot "$SNAPSHOT"'
            ' --snapshot-name "$SNAPSHOT_NAME"'
            ' --extra-vars "$ANSIBLE_EXTRA_VARS"'
            ' --dry-run "$DRY_RUN"',
        ]

    @staticmethod
    def _build_order_script() -> list[str]:
        return [
            r'printf "\e[1m\e[36m--- Order job variables ---\n'
            r"HOST:                 $HOST"
            r"SKIP_VULNS:           $SKIP_VULNS"
            r"ANSIBLE_EXTRA_VARS:   $ANSIBLE_EXTRA_VARS"
            r"DRY_RUN:              $DRY_RUN"
            r'----------------------------\n\e[0m"',
            "bash /app/order.sh"
            ' --host "$HOST"'
            ' --skip-vulns "$SKIP_VULNS"'
            ' --extra-vars "$ANSIBLE_EXTRA_VARS"'
            ' --dry-run "$DRY_RUN"',
        ]

    # generate_gitlab_ci — helpers
    @dataclass
    class _CIGenerateOpts:
        """Normalised options bag passed between generate_gitlab_ci helpers."""

        skip_hosts: list
        only_hosts: list
        actor: list
        large_tiers: list
        standalone_tiers: list
        clustered_tiers: list
        required_tiers: list | None
        ignore_deploy_order: bool
        reverse_deploy_order: bool
        docker_image_count: int
        standalone_deployment: bool
        core_level: int
        nova_version: str
        windows_tier: str
        dry_run: bool

    def _normalize_generate_inputs(
        self,
        skip_hosts,
        only_hosts,
        actor,
        large_tiers,
        standalone_tiers,
        clustered_tiers,
        required_tiers,
        ignore_deploy_order,
        reverse_deploy_order,
        docker_image_count,
        standalone_deployment,
        core_level,
        nova_version,
        windows_tier,
        dry_run,
    ) -> "_CIGenerateOpts":
        """Validate and normalise raw arguments into a _CIGenerateOpts instance."""
        if skip_hosts is not None and only_hosts is not None:
            if any(skip_hosts) and any(only_hosts):
                self.logger.warning(
                    "Warning: Both --skip_hosts and --only_hosts provided; --only_hosts takes precedence"
                )
                skip_hosts = []  # only_hosts takes precedence

        return self._CIGenerateOpts(
            skip_hosts=skip_hosts or [],
            only_hosts=only_hosts or [],
            actor=actor or [],
            large_tiers=large_tiers or [],
            standalone_tiers=standalone_tiers or [],
            clustered_tiers=clustered_tiers or [],
            required_tiers=required_tiers,
            ignore_deploy_order=ignore_deploy_order,
            reverse_deploy_order=reverse_deploy_order,
            docker_image_count=docker_image_count,
            standalone_deployment=standalone_deployment,
            core_level=core_level,
            nova_version=nova_version,
            windows_tier="" if windows_tier is None else str(windows_tier),
            dry_run=dry_run,
        )

    @staticmethod
    def _compute_stages(
        data: dict, core_level: int, reverse_deploy_order: bool
    ) -> list[str]:
        """Derive the ordered list of GitLab CI stage names."""
        tiers = list(data.keys())
        top_level_tiers = list(set(re.sub(r"[a-zA-Z_]*$", "", tier) for tier in tiers))
        top_level_tiers.sort(key=lambda x: int(re.search(r"\d+", x).group()))

        if core_level > 0:
            non_core_tiers = [
                tier
                for tier in top_level_tiers
                if int(re.sub(r"\D", "", tier)) > core_level
            ]
            if reverse_deploy_order:
                non_core_tiers.reverse()
                return non_core_tiers + ["CoreTiers"]
            return ["CoreTiers"] + non_core_tiers

        stages = top_level_tiers
        if reverse_deploy_order:
            stages.reverse()
        return stages

    def _build_host_list(
        self,
        data: dict,
        tier: str,
        job_name: str,
        top_level_tier: str,
        top_level_tier_number: str,
        opts: "_CIGenerateOpts",
    ) -> tuple[list[str], list[dict], bool]:
        """
        Iterate over the hosts in a tier and produce:
          - host_list:  the flat list of host patterns for the CI matrix
          - win_entries: any Windows-core host entries collected for later
          - needs_fat_runner: True when a sequenced host expanded the list
        """
        host_list: list[str] = []
        win_entries: list[dict] = []
        needs_fat_runner = False

        is_win_core_tier = (
            top_level_tier_number == opts.windows_tier and "CORE" in tier.upper()
        )

        for host_entry in data[tier]:
            host, host_actor_dict = list(host_entry.items())[0]
            host = host.strip()
            host_actor = host_actor_dict["actor"].strip()

            if host_actor.upper() not in opts.actor and any(opts.actor):
                continue

            in_only = (any(opts.only_hosts) and host in opts.only_hosts) or (
                any(opts.only_hosts)
                and "||" in host
                and host.split("||")[0] in opts.only_hosts
            )
            host_base = host.split("||")[0] if "||" in host else host
            in_default = not any(opts.only_hosts) and host_base not in opts.skip_hosts
            if not (in_only or in_default):
                continue

            add_team_suffix = top_level_tier.upper() not in opts.standalone_tiers
            team_nr = (
                "{0:02d}".format(int(getenv_str("CICD_TEAM", "28")))
                if add_team_suffix
                else ""
            )

            if "||" in host:
                needs_fat_runner = True
                hostname, count_str = host.split("||")
                count = int(count_str)
                all_hosts = [f"hostname_{idx:02}" for idx in range(1, count + 1)]

                is_clustered = job_name in opts.clustered_tiers
                step = (
                    len(all_hosts)
                    if is_clustered
                    else self.config.DEPLOYMENT_SEQUENCE_STEP
                )
                grouped = [
                    all_hosts[i : i + step] for i in range(0, len(all_hosts), step)
                ]

                for group in grouped:
                    numbers = [int(x.split("_")[-1]) for x in group]

                    tens_groups: dict = defaultdict(list)
                    for n in numbers:
                        tens_groups[n // 10].append(n)

                    group_patterns = []
                    for _, nums in sorted(tens_groups.items()):
                        nums.sort()
                        if len(nums) == 1:
                            group_patterns.append(f"{nums[0]:02}")
                        else:
                            start, end = nums[0], nums[-1]
                            if start // 10 == end // 10:
                                group_patterns.append(
                                    f"0[{start % 10}-{end % 10}]"
                                    if start < 10
                                    else f"{start // 10}[{start % 10}-{end % 10}]"
                                )
                            else:
                                group_patterns.append("|".join(f"{n:02}" for n in nums))

                    pattern = (
                        group_patterns[0]
                        if len(group_patterns) == 1
                        else "(" + "|".join(group_patterns) + ")"
                    )
                    entry = f"{hostname}_{pattern}"
                    if add_team_suffix:
                        entry += f"_t{team_nr}"
                    host_list.append(entry)
            else:
                entry = host
                if add_team_suffix:
                    entry += f"_t{team_nr}"
                host_list.append(entry)

            if is_win_core_tier:
                win_entries.append({"host": entry, "actor": host_actor})

        return host_list, win_entries, needs_fat_runner

    def _select_runner_tag(
        self,
        job_name: str,
        top_level_tier: str,
        needs_fat_runner: bool,
        opts: "_CIGenerateOpts",
    ) -> str:
        """Pick the appropriate GitLab runner tag for a job."""
        if job_name in opts.clustered_tiers:
            return self.config.TAG_RUNNER_MOAD
        if top_level_tier.upper() in opts.large_tiers or needs_fat_runner:
            return self.config.TAG_RUNNER_FAT
        return self.config.TAG_RUNNER_SLIM

    def _select_docker_image(self, opts: "_CIGenerateOpts") -> str:
        """Pick (and randomly load-balance) the executor Docker image."""
        if opts.docker_image_count >= 1:
            n = random.randint(1, opts.docker_image_count)
            return (
                f"{self.config.NEXUS_HOST}/{self.config.PROJECT_VERSION}"
                f"-cicd-image-{n}-{opts.nova_version.lower()}:latest"
            )
        return self.config.EXECUTOR_DOCKER_IMAGE

    def _build_deploy_job(
        self,
        job_name: str,
        job_stage: str,
        docker_image: str,
        job_tag: str,
        deploy_rule: list,
        host_list: list[str],
        required_tiers: list[str] | None,
        dry_run: bool = False,
    ) -> dict:
        """Assemble the full job dict for a standard deploy job."""
        job: dict = {
            "stage": job_stage,
            "image": docker_image,
            "tags": [job_tag],
            "before_script": [
                "sudo bash /app/move_needed_files.sh",
                'echo "$VAULT_PASS" >> /app/.vault_pass',
            ],
            "rules": deploy_rule,
            "script": self._build_deploy_script(),
            "parallel": {"matrix": [{"HOST": host_list}]},
            "dependencies": [],  # no artifacts needed
            "retry": {
                "max": 2,
                "when": [
                    "runner_system_failure",
                    "stuck_or_timeout_failure",
                    "script_failure",
                    "api_failure",
                ],
                "exit_codes": [1, 137],
            },
        }
        if dry_run:
            job["variables"] = {"DRY_RUN": "true"}
        if bool(required_tiers) and not self._tier_matches_required(
            job_name, required_tiers
        ):
            job["allow_failure"] = True
        return job

    def _wire_in_loop_needs(
        self,
        jobs: dict,
        job_name: str,
        job_stage: str,
        loop_index: int,
    ) -> None:
        """Wire sequential `needs` for a job during the main tier loop (forward order only)."""
        if loop_index == 0:
            return

        my_job_index = list(jobs.keys()).index(job_name)
        job_keys_so_far = list(jobs.keys())

        previous_job = None
        for prev_idx in range(my_job_index - 1, -1, -1):
            candidate = job_keys_so_far[prev_idx]
            if jobs[candidate]["parallel"]["matrix"][0]["HOST"]:
                previous_job = candidate
                break

        if previous_job is None:
            return

        current_is_core = job_stage == "CoreTiers"
        previous_is_core = jobs[previous_job]["stage"] == "CoreTiers"

        if (
            current_is_core
            and previous_is_core
            or not current_is_core
            and previous_is_core
        ):
            jobs[job_name]["needs"] = [
                {
                    "job": previous_job,
                    "optional": True,
                }
            ]
        elif (
            not current_is_core
            and not previous_is_core
            and job_stage == jobs[previous_job]["stage"]
        ):
            jobs[job_name]["needs"] = [{"job": previous_job, "optional": True}]

    def _build_windows_core_jobs(
        self,
        win_host_list_core: list[dict],
        docker_image: str,
        opts: "_CIGenerateOpts",
    ) -> dict:
        """Build and return the Windows _core order job dict (empty dict if not applicable)."""
        if not opts.windows_tier:
            return {}
        if not win_host_list_core:
            self.logger.warning(
                f"Tier {opts.windows_tier} defined as Windows tier, but no Windows core "
                f"hosts found, check your tier assignments"
            )
            return {}

        win_core_actors: dict = defaultdict(list)
        for entry in win_host_list_core:
            win_core_actors[entry["actor"]].append(entry["host"])
        for act in win_core_actors:
            self.logger.debug(
                f"Windows Core Hosts to be deployed for actor {act}: {win_core_actors[act]}"
            )

        job_name = f"tier{opts.windows_tier}_core"
        job_tag = (
            self.config.TAG_RUNNER_FAT
            if f"TIER{opts.windows_tier}" in opts.large_tiers
            else self.config.TAG_RUNNER_SLIM
        )

        job: dict = {
            "stage": f"Tier{opts.windows_tier}",
            "image": docker_image,
            "tags": [job_tag],
            "before_script": [
                "sudo bash /app/move_needed_files.sh",
                'echo "$VAULT_PASS" >> /app/.vault_pass',
            ],
            "rules": [
                {
                    "if": (
                        f'$REDEPLOY_TIER{opts.windows_tier} == "true"'
                        f' && ($DEPLOY_MODE == "redeploy" || $DEPLOY_MODE == "deploy")'
                    ),
                    "when": "on_success",
                }
            ],
            "script": self._build_order_script(),
            "dependencies": [],  # no artifacts needed
            "retry": {
                "max": 2,
                "when": [
                    "runner_system_failure",
                    "stuck_or_timeout_failure",
                    "script_failure",
                    "api_failure",
                ],
                "exit_codes": [1, 137],
            },
            "parallel": {
                "matrix": [
                    {"HOST": " ".join(win_core_actors[act])} for act in win_core_actors
                ]
            },
        }
        if opts.dry_run:
            job["variables"] = {"DRY_RUN": "true"}
        if bool(opts.required_tiers) and not self._tier_matches_required(
            job_name, opts.required_tiers
        ):
            job["allow_failure"] = True

        return {job_name: job}

    def _wire_post_loop_needs(
        self,
        jobs: dict,
        opts: "_CIGenerateOpts",
        windows_core_job_names: list[str],
    ) -> None:
        """
        Wire all post-loop `needs` relationships:
          1. Reverse order  — each job needs the next one
          2. Core-level     — first non-core job of each stage needs the last core job
          3. Windows _core  — windows core job needs the last core job
          4. Non-core win   — first non-core windows job needs the windows _core job
        """
        win_job_name = f"tier{opts.windows_tier}_core" if opts.windows_tier else None

        # 1. Reverse deploy order — mutually exclusive with everything else
        if not opts.ignore_deploy_order and opts.reverse_deploy_order:
            job_keys = [k for k in jobs if k != win_job_name]
            for idx, job_key in enumerate(job_keys):
                if idx < len(job_keys) - 1:
                    jobs[job_key]["needs"] = [
                        {"job": job_keys[idx + 1], "optional": True}
                    ]
            return

        if opts.ignore_deploy_order:
            return

        # 2. Forward order with core_level: wire first non-core job per stage to last core job
        if opts.core_level > 0:
            last_core_job = next(
                (
                    jn
                    for jn, jc in reversed(list(jobs.items()))
                    if jc["stage"] == "CoreTiers"
                    and jc["parallel"]["matrix"][0]["HOST"]
                ),
                None,
            )
            if last_core_job:
                non_core_first: dict[str, str] = {}
                for jn, jc in jobs.items():
                    stage = jc["stage"]
                    if stage != "CoreTiers" and stage not in non_core_first:
                        non_core_first[stage] = jn
                for first_job in non_core_first.values():
                    jobs[first_job].setdefault(
                        "needs", [{"job": last_core_job, "optional": True}]
                    )

        # 3. Windows _core job needs the last core job
        if opts.core_level > 0 and win_job_name and win_job_name in jobs:
            last_core_job = next(
                (
                    jn
                    for jn, jc in reversed(list(jobs.items()))
                    if jc["stage"] == "CoreTiers"
                    and jc["parallel"]["matrix"][0]["HOST"]
                ),
                None,
            )
            if last_core_job:
                jobs[win_job_name]["needs"] = [{"job": last_core_job, "optional": True}]

        # 4. First non-CORE windows job needs the windows _core job;
        #    propagate that dep to any sibling that already needs a CORE job
        if (
            opts.windows_tier
            and windows_core_job_names
            and win_job_name
            and win_job_name in jobs
        ):
            first_non_core_win = next(
                (
                    jn
                    for jn, jc in jobs.items()
                    if jc["stage"] == f"Tier{opts.windows_tier}"
                    and jn != win_job_name
                    and jn not in windows_core_job_names
                ),
                None,
            )
            if first_non_core_win:
                jobs[first_non_core_win].setdefault("needs", []).append(
                    {"job": win_job_name, "optional": True}
                )
                for jn, jc in jobs.items():
                    if (
                        jc["stage"] == f"Tier{opts.windows_tier}"
                        and jn not in (win_job_name, first_non_core_win)
                        and jn not in windows_core_job_names
                        and "needs" in jc
                        and any(
                            need["job"] in windows_core_job_names
                            for need in jc["needs"]
                        )
                    ):
                        jc["needs"].append({"job": win_job_name, "optional": True})

    def generate_gitlab_ci(
        self,
        data: dict[str, list[dict[str, dict[str, Any]]]],
        skip_hosts: list[str] = None,
        only_hosts: list[str] = None,
        actor: list[str] = None,
        large_tiers: list[str] = None,
        standalone_tiers: list[str] = None,
        ignore_deploy_order: bool = False,
        reverse_deploy_order: bool = False,
        docker_image_count: int = 1,
        standalone_deployment: bool = False,
        core_level: int = 0,
        nova_version: str = "PRODUCTION",
        windows_tier: str = None,
        clustered_tiers: list[str] = None,
        required_tiers: list[str] = None,
        dry_run: bool = False,
    ) -> dict[str, list]:

        opts = self._normalize_generate_inputs(
            skip_hosts,
            only_hosts,
            actor,
            large_tiers,
            standalone_tiers,
            clustered_tiers,
            required_tiers,
            ignore_deploy_order,
            reverse_deploy_order,
            docker_image_count,
            standalone_deployment,
            core_level,
            nova_version,
            windows_tier,
            dry_run,
        )

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        stages = self._compute_stages(data, opts.core_level, opts.reverse_deploy_order)
        gitlab_ci: dict = {"stages": stages}

        jobs: dict = {}
        win_host_list_core: list[dict] = []
        windows_core_job_names: list[str] = []
        docker_image = self._select_docker_image(opts)

        for i, tier in enumerate(data.keys()):
            top_level_tier = re.sub(r"[a-zA-Z_]*$", "", tier)
            top_level_tier_number = re.sub(r"\D", "", top_level_tier)

            is_win_core = (
                top_level_tier_number == opts.windows_tier and "CORE" in tier.upper()
            )
            job_name = (
                re.sub(r"\_(.*)", "", tier).lower() if is_win_core else tier.lower()
            )

            deploy_rule = (
                [
                    {
                        "if": (
                            f'$REDEPLOY_{top_level_tier.upper()} == "true"'
                            f' && $DEPLOY_MODE != "redeploy" && $DEPLOY_MODE != "deploy"'
                        ),
                        "when": "on_success",
                    }
                ]
                if is_win_core
                else [
                    {
                        "if": f'$REDEPLOY_{top_level_tier.upper()} == "true"',
                        "when": "on_success",
                    }
                ]
            )

            host_list, win_entries, needs_fat_runner = self._build_host_list(
                data, tier, job_name, top_level_tier, top_level_tier_number, opts
            )
            win_host_list_core.extend(win_entries)

            job_tag = self._select_runner_tag(
                job_name, top_level_tier, needs_fat_runner, opts
            )
            job_stage = (
                top_level_tier
                if opts.core_level == 0 or int(top_level_tier_number) > opts.core_level
                else "CoreTiers"
            )

            jobs[job_name] = self._build_deploy_job(
                job_name,
                job_stage,
                docker_image,
                job_tag,
                deploy_rule,
                host_list,
                opts.required_tiers,
                opts.dry_run,
            )

            if is_win_core:
                windows_core_job_names.append(job_name)

            if not opts.ignore_deploy_order:
                self._wire_in_loop_needs(jobs, job_name, job_stage, i)

        jobs.update(
            self._build_windows_core_jobs(win_host_list_core, docker_image, opts)
        )
        self._wire_post_loop_needs(jobs, opts, windows_core_job_names)

        gitlab_ci.update(jobs)
        return gitlab_ci

    def get_gitlab_ci_from_tier_assignment(
        self,
        skip_hosts: list[str] = None,
        only_hosts: list[str] = None,
        actor: list[str] = None,
        large_tiers: list[str] = None,
        standalone_tiers: list[str] = None,
        ignore_deploy_order: bool = False,
        reverse_deploy_order: bool = False,
        docker_image_count: int = 1,
        standalone_deployment: bool = False,
        core_level: int = 0,
        nova_version: str = "PRODUCTION",
        windows_tier: str = None,
        clustered_tiers: list[str] = None,
        required_tiers: list[str] = None,
        dry_run: bool = False,
    ) -> dict[str, list[Any]]:

        if not standalone_deployment:
            tier_assignments = self.get_tier_assignments_providentia()
        else:
            tier_assignments = {"Tier0a": [{x: {"actor": "SA"}} for x in only_hosts]}
            standalone_tiers = ["TIER0"]
            large_tiers = ["TIER0"]

        gitlab_ci = self.generate_gitlab_ci(
            data=tier_assignments,
            skip_hosts=skip_hosts,
            only_hosts=only_hosts,
            actor=actor,
            large_tiers=large_tiers,
            standalone_tiers=standalone_tiers,
            ignore_deploy_order=ignore_deploy_order,
            reverse_deploy_order=reverse_deploy_order,
            docker_image_count=docker_image_count,
            standalone_deployment=standalone_deployment,
            core_level=core_level,
            nova_version=nova_version,
            windows_tier=windows_tier,
            clustered_tiers=clustered_tiers,
            required_tiers=required_tiers,
            dry_run=dry_run,
        )

        return gitlab_ci

    def get_pipeline_schedule(
        self, schedule_id: int = None, fetch_all: bool = False
    ) -> ProjectPipelineSchedule | list[ProjectPipelineSchedule]:
        pass

        the_project = self.get_project_by_namespace(self.config.PROJECT_NAMESPACE)

        if fetch_all:
            return the_project.pipelineschedules.list(get_all=True)
        else:
            return the_project.pipelineschedules.get(schedule_id)

    def get_pipeline_schedule_status(
        self, schedule_id: int = None, fetch_all: bool = False
    ) -> Tuple[list[str], list[str]]:
        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        header_list = [
            "ID",
            "Description",
            "Cron",
            "TZ",
            "Active",
            "Branch",
            "Owner",
            "Next Run",
            "Last run result",
            "Variables",
        ]
        entry_list = []
        all_schedule_objs = []
        if fetch_all:
            all_schedules = self.get_pipeline_schedule(fetch_all=fetch_all)
            all_ids = [x.id for x in all_schedules]

            for each in all_ids:
                all_schedule_objs.append(self.get_pipeline_schedule(schedule_id=each))
        else:
            all_schedule_objs.append(
                self.get_pipeline_schedule(schedule_id=schedule_id)
            )
        all_schedule_objs = [
            PipelineScheduleDetails.from_pipelineschedule_attributes(x.attributes)
            for x in all_schedule_objs
        ]
        entry_list.extend([x.get_entry_list() for x in all_schedule_objs])

        return header_list, entry_list
