import datetime
import inspect
import logging
import random
import re
from collections import defaultdict
from typing import Any, List, Tuple

import gitlab
from gitlab import Gitlab
from gitlab.v4.objects import Project, ProjectPipeline
from tqdm import tqdm

from ccdcoe.deployments.deployment_config import Config
from ccdcoe.deployments.generic.constants import deploy_modes, gitlab_boolean
from ccdcoe.deployments.objects.pipeline_details import PipelineDetails
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


class DeploymentHandler(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.config = Config

        self.providentia = ProvidentiaApi(
            baseurl=self.config.PROVIDENTIA_URL,
            api_path=self.config.PROVIDENTIA_VERSION,
            api_key=self.config.PROVIDENTIA_TOKEN,
        )

        self.beg_regex = re.compile(r"beg")
        self.baf_regex = re.compile(r"baf")

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
    ) -> ProjectPipeline:

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
            ret_dict = {}
            for key, val in __UNIQUE_TIERS__.items():
                if show_bear_level:
                    ret_dict.update({key: val().show_bear_level()})
                else:
                    ret_dict.update({key: val().as_dict()})
            return ret_dict
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
        docker_image_count: int = 1,
        nova_version: str = "PRODUCTION",
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
                for tl in range(0, 10):  # fix this
                    setattr(the_tier, f"REDEPLOY_TIER{tl}", gitlab_boolean.DISABLED)
                for i, tier in enumerate(tiers):
                    top_level_tier = re.sub(r"[a-zA-Z]$", "", tier)
                    for host in tier_assignments[tier]:
                        if host in only_hosts_list:
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
            tier_data["DOCKER_IMAGE_COUNT"] = docker_image_count
            tier_data["NOVA_VERSION"] = nova_version

            if only_hosts:
                description = (
                    f"LIMITED to hosts: {only_hosts}, skip_vulns: {skip_vulns}"
                )
            else:
                if deploy_full_tier:
                    if start_tier_level == 0:
                        description = f"FULL up to Tier {tier_level}, skip_vulns: {skip_vulns}, skip_hosts: {skip_hosts}"
                    else:
                        description = f"FULL from Tier {start_tier_level} to {tier_level}, skip_vulns: {skip_vulns}, skip_hosts: {skip_hosts}"
                else:
                    description = f"LIMITED to Tier {tier_level}, skip_vulns: {skip_vulns}, skip_hosts: {skip_hosts}"

            if actor:
                description += f", actor: {actor}"

            if len(description) >= 255:
                description = (
                    description[:220] + "-TRUNCATED"
                )  # accounting for 'redeploy Team xx as well'

            tier_data["DEPLOY_DESCRIPTION"] = description

            project_pipeline = self.custom_deployment(
                reference=reference, variables=tier_data
            )
            if project_pipeline is not None:
                return (
                    f"Project pipeline for team {team_number}({description}) deployed -> "
                    f"pipeline id {project_pipeline.id} status: {project_pipeline.status} ref: {project_pipeline.ref}"
                )
        except Exception as e:
            self.logger.error(f"Uncaught exception -> {e}")

    def get_last_deployment_pipeline(
        self,
        reference: str = "main",
        team_number: int = 28,
        update_delta_in_hours: int = 4,
        return_pipeline_details: bool = True,
    ) -> ProjectPipeline | PipelineDetails | None:
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
            get_all=False,
            updated_after=iso_formatted_delta,
        )

        if len(pipelines) == 0:
            return None

        if return_pipeline_details:
            project_pipeline = pipelines[0]
            project_pipeline_details = PipelineDetails(
                project_pipeline.id,
                project_pipeline.name,
                project_pipeline.ref,
                project_pipeline.status,
                project_pipeline.web_url,
                project_pipeline.updated_at,
            )
            return project_pipeline_details
        else:
            return pipelines[0]

    def get_deployment_status(
        self,
        reference: str = "main",
        team_number: int | List[int] = 28,
        fetch_all: bool = False,
    ) -> Tuple[List[str], List[str]]:

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
                    entry_list.append(details_obj.get_entry_list())
        else:
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
                        entry_list.append(details_obj.get_entry_list())
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
                        entry_list.append(details_obj.get_entry_list())

        return header_list, entry_list

    def get_hosts_per_network_providentia(self):

        self.logger.info(f"Fetching all networks...")
        all_networks = self.providentia.environment_networks(
            self.config.PROJECT_VERSION
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
            self.config.PROJECT_VERSION
        )

        all_hosts = [x for x in host_inventory["result"] if x["actor_id"] != "gt"]

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
            self.config.PROJECT_VERSION
        )

        ret_dict = defaultdict(list)

        for host in tqdm(the_inventory["result"], desc="Processing tier assignments"):
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
                if len(tier_level) > 6:
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

    def generate_gitlab_ci(
        self,
        data: dict[str, List[str]],
        skip_hosts: List[str] = None,
        only_hosts: List[str] = None,
        actor: List[str] = None,
        large_tiers: List[str] = None,
        standalone_tiers: List[str] = None,
        ignore_deploy_order: bool = False,
        docker_image_count: int = 1,
    ) -> dict[str, list]:
        if any(skip_hosts) and any(only_hosts):
            self.logger.warning(
                f"Warning: Both --skip_hosts and --only_hosts provided; --only_hosts takes precedence"
            )
            skip_hosts = []  # only_hosts takes precedence
        if skip_hosts is None:
            skip_hosts = []

        if only_hosts is None:
            only_hosts = []

        if actor is None:
            actor = []

        if large_tiers is None:
            large_tiers = []

        if standalone_tiers is None:
            standalone_tiers = []

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        tiers = list(data.keys())
        top_level_tiers = list(set(re.sub(r"[a-zA-Z]$", "", tier) for tier in tiers))

        # Sort numerically based on the number in "TierX"
        top_level_tiers.sort(key=lambda x: int(re.search(r"\d+", x).group()))

        # Prepare GitLab CI/CD pipeline structure
        gitlab_ci = {"stages": top_level_tiers}

        jobs = {}

        for i, tier in enumerate(tiers):
            mode = getenv_str("DEPLOY_MODE", deploy_modes.REDEPLOY)
            # nova_version = getenv_str("NOVA_VERSION", "PRODUCTION")
            job_name = f"{tier.lower()}"
            top_level_tier = re.sub(r"[a-zA-Z]$", "", tier)

            deploy_rule = [
                {
                    "if": f'$REDEPLOY_{top_level_tier.upper()} == "true"',
                    "when": "on_success",
                }
            ]
            host_list = []
            for host in data[tier]:
                host, host_actor = list(host.items())[0]
                host = host.strip()
                host_actor = host_actor["actor"].strip()

                if host_actor.upper() not in actor and any(actor):
                    continue
                if (any(only_hosts) and host in only_hosts) or (
                    not any(only_hosts) and host not in skip_hosts
                ):
                    # Skip team suffix for standalone tiers
                    add_team_suffix = top_level_tier.upper() not in standalone_tiers

                    team_nr = getenv_str("CICD_TEAM", "28")
                    if int(team_nr) < 10:
                        team_nr = f"0{team_nr}"

                    if "||" in host:
                        hostname, count_str = host.split("||")
                        count = int(count_str)

                        all_hosts = [f"hostname_{i:02}" for i in range(1, count + 1)]

                        grouped = [
                            all_hosts[i : i + self.config.DEPLOYMENT_SEQUENCE_STEP]
                            for i in range(
                                0, len(all_hosts), self.config.DEPLOYMENT_SEQUENCE_STEP
                            )
                        ]

                        for group in grouped:
                            numbers = [int(x.split("_")[-1]) for x in group]

                            tens_groups = defaultdict(list)
                            for n in numbers:
                                tens_groups[n // 10].append(n)

                            group_patterns = []
                            for tens, nums in sorted(tens_groups.items()):
                                nums.sort()
                                if len(nums) == 1:
                                    group_patterns.append(f"{nums[0]:02}")
                                else:
                                    start, end = nums[0], nums[-1]
                                    if start // 10 == end // 10:
                                        group_patterns.append(
                                            f"0[{start % 10}-{end % 10}]"
                                            if start < 10
                                            else f"{start//10}[{start%10}-{end%10}]"
                                        )
                                    else:
                                        group_patterns.append(
                                            "|".join(f"{n:02}" for n in nums)
                                        )

                            if len(group_patterns) == 1:
                                pattern = group_patterns[0]
                            else:
                                pattern = "(" + "|".join(group_patterns) + ")"

                            entry = f"{hostname}_{pattern}"
                            if add_team_suffix:

                                entry += f"_t{team_nr}"
                            host_list.append(entry)
                    else:
                        entry = host
                        if add_team_suffix:
                            entry += f"_t{team_nr}"
                        host_list.append(entry)

            if top_level_tier.upper() in large_tiers:
                job_tag = self.config.TAG_RUNNER_FAT

            else:
                job_tag = self.config.TAG_RUNNER_SLIM

            if docker_image_count > 1:
                random_image_number = random.randint(1, docker_image_count)
                docker_image = f"{self.config.NEXUS_HOST}/{self.config.PROJECT_VERSION}-cicd-image-{random_image_number}:latest"
            else:
                docker_image = self.config.EXECUTOR_DOCKER_IMAGE

            jobs[job_name] = {
                "stage": top_level_tier,
                "image": docker_image,
                "tags": [job_tag],
                "before_script": [
                    "sudo bash /app/move_needed_files.sh",
                    'echo "$VAULT_PASS" >> /app/.vault_pass',
                ],
                "rules": deploy_rule,
                "script": [
                    f'echo "Deploying $HOST..."',
                    f"bash /app/deploy.sh $HOST $SKIP_VULNS $DEPLOY_MODE $SNAPSHOT_NAME",
                ],
                "parallel": {"matrix": [{"HOST": host_list}]},
                "dependencies": [],  # no artifacts needed....
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

            if ignore_deploy_order:
                continue
            else:
                if i > 0:
                    my_job_index = list(jobs.keys()).index(job_name)
                    # if top_level_tier.upper() not in exclude_tier_list:
                    jobs[job_name]["needs"] = [
                        {
                            "job": (
                                "dummy_job"
                                if my_job_index == 0
                                else list(jobs.keys())[my_job_index - 1]
                            ),
                            "optional": True,
                        }
                    ]

        # Merge jobs into GitLab CI structure
        gitlab_ci.update(jobs)

        return gitlab_ci

    def get_gitlab_ci_from_tier_assignment(
        self,
        skip_hosts: List[str] = None,
        only_hosts: List[str] = None,
        actor: List[str] = None,
        large_tiers: List[str] = None,
        standalone_tiers: List[str] = None,
        ignore_deploy_order: bool = False,
        docker_image_count: int = 1,
    ) -> dict[str, List[Any]]:

        tier_assignments = self.get_tier_assignments_providentia()

        large_tiers = [elem.upper() for elem in large_tiers]
        standalone_tiers = [elem.upper() for elem in standalone_tiers]

        gitlab_ci = self.generate_gitlab_ci(
            data=tier_assignments,
            skip_hosts=skip_hosts,
            only_hosts=only_hosts,
            actor=actor,
            large_tiers=large_tiers,
            standalone_tiers=standalone_tiers,
            ignore_deploy_order=ignore_deploy_order,
            docker_image_count=docker_image_count,
        )

        return gitlab_ci
