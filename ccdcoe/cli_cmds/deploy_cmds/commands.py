import logging

import click

from ccdcoe.cli_cmds.cli_utils.mutex import Mutex
from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.cli_cmds.cli_utils.utils import add_options
from ccdcoe.cli_cmds.deploy_cmds.general_options.options import (
    team_number_option,
    branch_option,
    skip_vulns_option,
    snapshot_option,
    deploy_mode_option,
    skip_hosts_option,
    only_hosts_option,
    actor_option,
    large_tiers_option,
    standalone_tiers_option,
    nova_option,
    docker_image_count_option,
)
from ccdcoe.deployments.deployment_handler import DeploymentHandler
from ccdcoe.deployments.generic.constants import deploy_modes
from ccdcoe.deployments.parsers.team_numbers import parse_team_number
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


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
@add_options(branch_option)
@add_options(team_number_option)
@add_options(skip_vulns_option)
@add_options(snapshot_option)
@add_options(deploy_mode_option)
@add_options(skip_hosts_option)
@add_options(only_hosts_option)
@add_options(actor_option)
@add_options(large_tiers_option)
@add_options(standalone_tiers_option)
@add_options(nova_option)
@add_options(docker_image_count_option)
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
@add_options(branch_option)
@add_options(team_number_option)
@add_options(skip_vulns_option)
@add_options(snapshot_option)
@add_options(deploy_mode_option)
@add_options(skip_hosts_option)
@add_options(only_hosts_option)
@add_options(actor_option)
@add_options(large_tiers_option)
@add_options(standalone_tiers_option)
@add_options(nova_option)
@add_options(docker_image_count_option)
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
    help="Perform a standalone deployment.\n\nA standalone deployment is a deployment that does not take into account "
    "any tiers; but simply deploys the selected hosts in a single parallel stage.",
    no_args_is_help=True,
)
@add_options(branch_option)
@add_options(skip_vulns_option)
@add_options(snapshot_option)
@add_options(deploy_mode_option)
@add_options(only_hosts_option)
@click.pass_obj
def standalone(
    deployment_handler: DeploymentHandler,
    branch: str,
    snap_name: str,
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
    only_hosts: str = "",
):
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

    deployment_handler.logger.info(
        f"Initiating standalone deployment for hosts: {only_hosts}..."
    )
    ret_data = deployment_handler.deploy_standalone(
        reference=branch,
        deploy_mode=deployment_mode,
        skip_vulns=skip_vulns,
        snapshot=snapshot,
        snap_name=snap_name,
        only_hosts=only_hosts,
    )
    deployment_handler.logger.info(
        f"Standalone deployment for hosts: {only_hosts} started!"
    )
    ConsoleOutput.print(ret_data)
