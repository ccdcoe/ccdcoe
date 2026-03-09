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
    "--reverse_deploy_order",
    help="Reverse the deployment order",
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
@click.option(
    "--standalone_deployment",
    help="Execute the deployment in standalone mode",
    default=False,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--core_level",
    help="Set this tier level (and all tiers below) as core tiers",
    default=0,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--nova_version",
    type=click.Choice(["PRODUCTION", "STAGING"], case_sensitive=False),
    default="PRODUCTION",
    show_default=True,
    help="Choose nova.core version",
)
@click.option(
    "--windows_tier",
    help="Set this tier level as windows tier",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--clustered_tiers",
    help="Comma separated list of job names whose hosts must all be placed in a single job (ignores DEPLOYMENT_SEQUENCE_STEP)",
    default=None,
    is_flag=False,
    flag_value="",
    show_default=True,
)
@click.option(
    "--required_tiers",
    help=(
        "Comma separated list of tier job names that must not fail. "
        "All other jobs will have allow_failure: true (warning only). "
        "Supports exact names ('tier1a') and parent-tier prefixes ('tier1' matches tier1a, tier1b, ...). "
        "If omitted, all tiers are treated as required (no allow_failure added)."
    ),
    default=None,
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
    reverse_deploy_order: bool = False,
    docker_image_count: int = 1,
    standalone_deployment: bool = False,
    core_level: int = 0,
    nova_version: str = "PRODUCTION",
    windows_tier: str = None,
    clustered_tiers: str = None,
    required_tiers: str = None,
):
    if ignore_deploy_order and reverse_deploy_order:
        deployment_handler.logger.error(
            "Cannot set both --ignore_deploy_order and --reverse_deploy_order at the same time"
        )
        return False

    if skip_hosts is not None:
        skip_hosts = skip_hosts.replace(" ", "").split(",")
    if only_hosts is not None:
        only_hosts = only_hosts.replace(" ", "").split(",")
    if actor is not None:
        actor = [a.strip().upper() for a in actor.split(",")]
    if large_tiers is not None:
        large_tiers = [l.strip().upper() for l in large_tiers.split(",")]
    if standalone_tiers is not None:
        standalone_tiers = [s.strip().upper() for s in standalone_tiers.split(",")]
    if clustered_tiers is not None and clustered_tiers != "":
        clustered_tiers = [t.strip() for t in clustered_tiers.split(",") if t.strip()]
    else:
        clustered_tiers = None

    if required_tiers is not None and required_tiers != "":
        required_tiers = [t.strip().lower() for t in required_tiers.split(",") if t.strip()]
        if not required_tiers:
            required_tiers = None
    else:
        required_tiers = None

    deployment_handler.logger.info(f"Fetching tier assignment...")
    gitlab_ci_data = deployment_handler.get_gitlab_ci_from_tier_assignment(
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
