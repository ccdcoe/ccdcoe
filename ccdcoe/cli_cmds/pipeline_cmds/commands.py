import click
import yaml

from ccdcoe.cli_cmds.cli_utils.mutex import Mutex
from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.deployments.deployment_config import Config
from ccdcoe.deployments.deployment_handler import DeploymentHandler
from ccdcoe.dumpers.indent_dumper import IndentDumper

config = Config


@click.group(
    "pipeline",
    no_args_is_help=True,
    help="Perform pipeline related operations.",
)
@click.pass_context
def pipeline_cmd(ctx):
    ctx.obj = DeploymentHandler()


@pipeline_cmd.command(
    help="Perform config actions.",
    no_args_is_help=True,
)
@click.option(
    "--out",
    help="Save the deployment config (in .gitlab-ci.yml format)",
    default="./.gitlab-ci.yml",
    is_flag=False,
    flag_value="./.gitlab-ci.yml",
    show_default=True,
    cls=Mutex,
    not_required_if=["show"],
)
@click.option(
    "--show",
    is_flag=True,
    help="Show the generated config",
    cls=Mutex,
    not_required_if=["out"],
)
@click.option(
    "--skip_hosts",
    help="Comma separated list of hosts to skip",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--only_hosts",
    help="Comma separated list of hosts to deploy, everything else will get ignored",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--actor",
    help="Comma separated list of actors to deploy, by default all actors are deployed",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--large_tiers",
    help="Comma separated list of tiers that need more resources",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--standalone_tiers",
    help="Comma separated list of tiers that have standalone VMs, i.e. no team number",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--ignore_deploy_order",
    help="Ignore the deployment order and perform the action in parallel",
    default=False,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--docker_image_count",
    help="Number of available docker images",
    default=1,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.pass_obj
def config(
    deployment_handler: DeploymentHandler,
    show: str,
    out: str = "./.gitlab-ci.yml",
    skip_hosts: str = None,
    only_hosts: str = None,
    actor: str = None,
    large_tiers: str = None,
    standalone_tiers: str = None,
    ignore_deploy_order: bool = False,
    docker_image_count: int = 1,
):
    if skip_hosts is not None:
        skip_hosts = skip_hosts.replace(" ", "").split(",")
    if only_hosts is not None:
        only_hosts = only_hosts.replace(" ", "").split(",")
    if actor is not None:
        actor = actor.replace(" ", "").split(",")
    if large_tiers is not None:
        large_tiers = large_tiers.replace(" ", "").split(",")
    if standalone_tiers is not None:
        standalone_tiers = standalone_tiers.replace(" ", "").split(",")

    deployment_handler.logger.info(f"Fetching tier assignment...")
    gitlab_ci_data = deployment_handler.get_gitlab_ci_from_tier_assignment(
        skip_hosts=skip_hosts,
        only_hosts=only_hosts,
        actor=actor,
        large_tiers=large_tiers,
        standalone_tiers=standalone_tiers,
        ignore_deploy_order=ignore_deploy_order,
        docker_image_count=docker_image_count,
    )
    if show:
        ConsoleOutput.print(gitlab_ci_data)

    with open(out, "w") as f:
        yaml.dump(
            gitlab_ci_data,
            f,
            Dumper=IndentDumper,
            default_flow_style=False,
            explicit_start=True,
        )
    deployment_handler.logger.info(f"Saved file to: {out}")
