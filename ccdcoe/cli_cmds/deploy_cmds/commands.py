import logging
from typing import List

import click
from tabulate import tabulate

from ccdcoe.cli_cmds.cli_utils.mutex import Mutex
from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.cli_cmds.cli_utils.utils import add_options
from ccdcoe.deployments.deployment_handler import DeploymentHandler
from ccdcoe.deployments.generic.constants import deploy_modes
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


def parse_team_number(team_number: str) -> List[int]:
    """
    Method for parsing the team number into a list of integers.
    Parsed list is made unique to avoid double entries.
    """
    team_number_list = team_number.split(",")

    parsed_team_numbers = []

    for each in team_number_list:
        if "-" in each:
            splitted = each.split("-")
            try:
                try:
                    for i in range(int(splitted[0]), int(splitted[1]) + 1):
                        parsed_team_numbers.append(i)
                except ValueError:
                    logger.warning(f"Invalid team number entry '{each}'")
            except IndexError:
                logger.warning(f"Invalid range entry for team number'{each}'")
        else:
            try:
                parsed_team_numbers.append(int(each))
            except ValueError:
                logger.warning(
                    f"Invalid team number entry '{each}'; could not convert to int"
                )

    return list(set(parsed_team_numbers))


_team_number_option = [
    click.option(
        "-t",
        "--team",
        show_default=True,
        default="28",
        help="The team number to deploy; this could be a comma separated (1,2) or hyphen separated (3-7) string "
        "or a combination of both. So entering '1,2' will deploy both team 1 and team 2; entering '3-7' will "
        "deploy teams 3 through 7 and entering 1,2,3-7,9 will deploy teams 1,2,3,4,5,6,7 and 9",
    )
]

_branch_option = [
    click.option(
        "-b",
        "--branch",
        type=str,
        default="main",
        show_default=True,
        help="Limits the deployment status to this branch.",
    )
]

_skip_vulns_option = [
    click.option(
        "-s",
        "--skip_vulns",
        type=bool,
        default=False,
        show_default=True,
        help="Should the vulnerability deployment be skipped.",
    )
]

_snapshot_option = [
    click.option(
        "--snapshot",
        help="Snapshot systems after deployment",
        is_flag=True,
        default=True,
        show_default=True,
    ),
    click.option(
        "--snap_name",
        help="Name of the snapshot",
        type=str,
        default="CLEAN",
        show_default=True,
    ),
]

_deploy_mode_option = [
    click.option(
        "--deploy",
        help="Set mode to deploy",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--undeploy",
        help="Set mode to undeploy",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--snap_deploy",
        help="Set mode to deploy-snap",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--clean_snap_deploy",
        help="Set mode to deploy-clean-snap",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--revert",
        help="Set mode to revert",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--poweron",
        help="Set mode to poweron",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--shutdown",
        help="Set mode to shutdown",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--clean_snap_deploy_shutdown",
        help="Set mode to deploy-clean-snap-shutdown, i.e. clean snap and keep VM powered off after",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
        ],
    ),
]

_skip_hosts_option = [
    click.option(
        "--skip_hosts",
        help="Comma separated list of hosts to skip",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]

_only_hosts_option = [
    click.option(
        "--only_hosts",
        help="Comma separated list of hosts to deploy, everything else will be ignored",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]

_actor_option = [
    click.option(
        "--actor",
        help="Comma separated list of actors to deploy, by default all actors are deployed",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]

_large_tiers_option = [
    click.option(
        "--large_tiers",
        help="Comma separated list of tiers that need more resources",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]

_standalone_tiers_option = [
    click.option(
        "--standalone_tiers",
        help="Comma separated list of tiers that have standalone VMs, i.e. no team number",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]

_nova_option = [
    click.option(
        "-n",
        "--nova_version",
        type=click.Choice(["PRODUCTION", "STAGING"], case_sensitive=False),
        default="PRODUCTION",
        show_default=True,
        help="Choose nova.core version",
    )
]
_docker_image_count_option = [
    click.option(
        "--docker_image_count",
        help="Number of available docker images",
        default=1,
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]


@click.group(
    "deploy",
    no_args_is_help=True,
    help="Perform deployment related operations.\n\nFor all commands executed here a 'redeploy' is assumed "
    "(unless specific deployment options are given or otherwise specified),"
    "\nmeaning that if a tier is already deployed, it will be undeployed first before it's deployed again!",
)
@click.pass_context
def deploy_cmd(ctx):
    ctx.obj = DeploymentHandler()


@deploy_cmd.command(
    help="Perform a full redeployment."
    "\n\nA full redeployment in this context reveres to a redeployment of all tiers.",
    no_args_is_help=True,
)
@add_options(_branch_option)
@add_options(_team_number_option)
@add_options(_skip_vulns_option)
@add_options(_snapshot_option)
@add_options(_deploy_mode_option)
@add_options(_skip_hosts_option)
@add_options(_only_hosts_option)
@add_options(_actor_option)
@add_options(_large_tiers_option)
@add_options(_standalone_tiers_option)
@add_options(_nova_option)
@add_options(_docker_image_count_option)
@click.pass_obj
def full(
    deployment_handler: DeploymentHandler,
    branch: str,
    team: str,
    skip_vulns: bool = False,
    deploy: bool = False,
    undeploy: bool = False,
    snap_deploy: bool = False,
    clean_snap_deploy: bool = False,
    clean_snap_deploy_shutdown: bool = False,
    revert: bool = False,
    poweron: bool = False,
    shutdown: bool = False,
    snapshot: bool = True,
    snap_name: str = "CLEAN",
    skip_hosts: str = "",
    only_hosts: str = "",
    actor: str = "",
    large_tiers: str = "",
    standalone_tiers: str = "",
    nova_version: str = "PRODUCTION",
    docker_image_count: int = 1,
):

    all_tier_data = deployment_handler.get_tier(retrieve_all=True, show_bear_level=True)

    last_tier = list(all_tier_data.keys())[-1]

    if deploy:
        deployment_mode = deploy_modes.DEPLOY
    elif undeploy:
        deployment_mode = deploy_modes.UNDEPLOY
    elif snap_deploy:
        deployment_mode = deploy_modes.DEPLOY_SNAP
    elif clean_snap_deploy:
        deployment_mode = deploy_modes.DEPLOY_CLEAN_SNAP
    elif clean_snap_deploy_shutdown:
        deployment_mode = deploy_modes.DEPLOY_CLEAN_SNAP_SHUTDOWN
    elif revert:
        deployment_mode = deploy_modes.REVERT
    elif poweron:
        deployment_mode = deploy_modes.POWERON
    elif shutdown:
        deployment_mode = deploy_modes.SHUTDOWN
    else:
        deployment_mode = deploy_modes.REDEPLOY

    for the_team in parse_team_number(team):
        deployment_handler.logger.info(f"Initiated deployment for team: {the_team}...")
        ret_data = deployment_handler.deploy_team(
            reference=branch,
            team_number=team,
            tier_level=last_tier,
            deploy_full_tier=True,
            deploy_mode=deployment_mode,
            skip_vulns=skip_vulns,
            snapshot=snapshot,
            snap_name=snap_name,
            skip_hosts=skip_hosts,
            only_hosts=only_hosts,
            actor=actor,
            large_tiers=large_tiers,
            standalone_tiers=standalone_tiers,
            nova_version=nova_version,
            docker_image_count=docker_image_count,
        )
        deployment_handler.logger.info(f"Full deployment for team: {the_team} started!")
        ConsoleOutput.print(ret_data)


@deploy_cmd.command(
    help="Perform a tiered deployment.\n\nA tiered deployment is a deployment that can be capped to a certain tier "
    "(given the output of --show_levels) level. You have the possibility to deploy up to and including the given "
    "tier (using --level); or limit the deployment to a certain tier (using --limit).",
    no_args_is_help=True,
)
@add_options(_branch_option)
@add_options(_team_number_option)
@add_options(_skip_vulns_option)
@add_options(_snapshot_option)
@add_options(_deploy_mode_option)
@add_options(_skip_hosts_option)
@add_options(_only_hosts_option)
@add_options(_actor_option)
@add_options(_large_tiers_option)
@add_options(_standalone_tiers_option)
@add_options(_nova_option)
@add_options(_docker_image_count_option)
@click.option("--show_levels", help="Show available tiers", is_flag=True)
@click.option("--assignments", help="Show tier assignments", is_flag=True)
@click.option(
    "--level",
    type=int,
    show_default=True,
    help="Deploy this tier level (and all lower tiers!), could be used in combination with --start_tier to control on "
    "which Tier to start",
    cls=Mutex,
    not_required_if=["limit"],
)
@click.option(
    "--limit",
    type=int,
    show_default=True,
    help="Deploy only this tier level",
    cls=Mutex,
    not_required_if=["level"],
)
@click.option(
    "--start_tier",
    type=int,
    show_default=True,
    default=0,
    help="Deploy only from this tier onwards (can be used in combination with --level switch)",
)
@click.pass_obj
def tier(
    deployment_handler: DeploymentHandler,
    branch: str,
    team: str,
    snap_name: str,
    show_levels: bool,
    assignments: bool,
    level: int = None,
    limit: int = None,
    start_tier: int = 0,
    deploy: bool = False,
    undeploy: bool = False,
    snap_deploy: bool = False,
    clean_snap_deploy: bool = False,
    clean_snap_deploy_shutdown: bool = False,
    revert: bool = False,
    poweron: bool = False,
    shutdown: bool = False,
    skip_vulns: bool = False,
    snapshot: bool = False,
    skip_hosts: str = "",
    only_hosts: str = "",
    actor: str = "",
    large_tiers: str = "",
    standalone_tiers: str = "",
    nova_version: str = "PRODUCTION",
    docker_image_count: int = 1,
):
    if show_levels:
        deployment_handler.logger.debug(f"Fetching tiers available for deployment")
        ConsoleOutput.print(
            deployment_handler.get_tier(retrieve_all=True, show_bear_level=True)
        )
    elif assignments:
        deployment_handler.logger.debug(f"Fetching tier assignments for hosts")
        ConsoleOutput.print(deployment_handler.get_tier_assignments_providentia())
    else:
        if deploy:
            deployment_mode = deploy_modes.DEPLOY
        elif undeploy:
            deployment_mode = deploy_modes.UNDEPLOY
        elif snap_deploy:
            deployment_mode = deploy_modes.DEPLOY_SNAP
        elif clean_snap_deploy:
            deployment_mode = deploy_modes.DEPLOY_CLEAN_SNAP
        elif clean_snap_deploy_shutdown:
            deployment_mode = deploy_modes.DEPLOY_CLEAN_SNAP_SHUTDOWN
        elif revert:
            deployment_mode = deploy_modes.REVERT
        elif poweron:
            deployment_mode = deploy_modes.POWERON
        elif shutdown:
            deployment_mode = deploy_modes.SHUTDOWN
        else:
            deployment_mode = deploy_modes.REDEPLOY

        if level is not None:
            for the_team in parse_team_number(team):
                deployment_handler.logger.info(
                    f"Initiating deployment for tier number: {level} team: {the_team}..."
                )
                ret_data = deployment_handler.deploy_team(
                    reference=branch,
                    team_number=the_team,
                    tier_level=level,
                    start_tier_level=start_tier,
                    deploy_full_tier=True,
                    deploy_mode=deployment_mode,
                    skip_vulns=skip_vulns,
                    snapshot=snapshot,
                    snap_name=snap_name,
                    skip_hosts=skip_hosts,
                    only_hosts=only_hosts,
                    actor=actor,
                    large_tiers=large_tiers,
                    standalone_tiers=standalone_tiers,
                    nova_version=nova_version,
                    docker_image_count=docker_image_count,
                )
                deployment_handler.logger.info(
                    f"Tier deployment for tier number: {level} team: {the_team} started!"
                )
                ConsoleOutput.print(ret_data)
        elif limit is not None:
            for the_team in parse_team_number(team):
                deployment_handler.logger.info(
                    f"Initiating deployment limited to tier number: {limit} team: {the_team}..."
                )
                ret_data = deployment_handler.deploy_team(
                    reference=branch,
                    team_number=the_team,
                    tier_level=limit,
                    deploy_mode=deployment_mode,
                    skip_vulns=skip_vulns,
                    snapshot=snapshot,
                    snap_name=snap_name,
                    skip_hosts=skip_hosts,
                    only_hosts=only_hosts,
                    actor=actor,
                    large_tiers=large_tiers,
                    standalone_tiers=standalone_tiers,
                    nova_version=nova_version,
                    docker_image_count=docker_image_count,
                )
                deployment_handler.logger.info(
                    f"Tier deployment limited to tier number: {limit} team: {the_team} started!"
                )
                ConsoleOutput.print(ret_data)


@deploy_cmd.command(
    help="Show status of deployments.",
    no_args_is_help=True,
)
@add_options(_team_number_option)
@add_options(_branch_option)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show status of all available deployments pipelines. If this flag is set; the 'team' variable is ignored "
    "and all teams (controlled by the range between the DEPLOYMENT_RANGE_LOWER and the DEPLOYMENT_RANGE_UPPER "
    "variables) are queried.",
)
@click.pass_obj
def status(deployment_handler: DeploymentHandler, branch: str, team: str, all: bool):

    deployment_handler.logger.info(f"Looking for deployments on branch: {branch}...")

    if all:
        deployment_handler.logger.info("Getting status from all teams...")
        header_list, entry_list = deployment_handler.get_deployment_status(
            reference=branch, team_number=parse_team_number(team), fetch_all=True
        )
        ConsoleOutput.print(
            tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
        )
    else:
        deployment_handler.logger.info(f"Getting status team range: {team}...")
        header_list, entry_list = deployment_handler.get_deployment_status(
            reference=branch, team_number=parse_team_number(team)
        )
        ConsoleOutput.print(
            tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
        )
