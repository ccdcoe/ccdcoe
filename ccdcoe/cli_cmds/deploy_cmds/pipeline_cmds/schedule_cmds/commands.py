import logging

import click
import gitlab
from gitlab.v4.objects import ProjectPipelineSchedule
from tabulate import tabulate

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.deployments.deployment_handler import DeploymentHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "schedule",
    no_args_is_help=True,
    help="Perform actions on the deployment schedules / scheduled pipelines.",
)
@click.pass_context
def schedule_cmd(ctx):
    ctx.obj = DeploymentHandler()


@schedule_cmd.command(
    help="Show status of pipeline schedules.",
    no_args_is_help=True,
)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show status of all available scheduled pipelines",
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline.",
)
@click.pass_obj
def status(
    deployment_handler: DeploymentHandler,
    all: bool,
    id: str = None,
):

    if all:
        deployment_handler.logger.info("Getting status from all schedules...")
        header_list, entry_list = deployment_handler.get_pipeline_schedule_status(
            fetch_all=True
        )
    else:
        deployment_handler.logger.info(f"Getting status from schedules: {id}...")
        header_list, entry_list = deployment_handler.get_pipeline_schedule_status(
            schedule_id=id
        )
    ConsoleOutput.print(
        tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
    )


@schedule_cmd.command(
    help="Trigger a pipeline schedule for immediate execution.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline.",
)
@click.pass_obj
def trigger(
    deployment_handler: DeploymentHandler,
    id: str = None,
):
    try:
        the_schedule: ProjectPipelineSchedule = (
            deployment_handler.get_pipeline_schedule(schedule_id=id)
        )
        the_schedule.play()
        ConsoleOutput.print(f"Schedule started!")
    except gitlab.exceptions.GitlabPipelinePlayError as e:
        ConsoleOutput.print(f"Could not start pipeline schedule: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(
            f"Not authorized to start pipeline schedule: {e.error_message}"
        )


@schedule_cmd.command(
    help="Transfer a pipeline schedule ownership; this command will let you take ownership of a pipeline schedule.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline.",
)
@click.pass_obj
def transfer(
    deployment_handler: DeploymentHandler,
    id: str = None,
):
    try:
        the_schedule: ProjectPipelineSchedule = (
            deployment_handler.get_pipeline_schedule(schedule_id=id)
        )
        the_schedule.take_ownership()
        ConsoleOutput.print(f"Schedule transferred!")
    except gitlab.exceptions.GitlabOwnershipError as e:
        ConsoleOutput.print(
            f"Could not take ownership on pipeline schedule: {e.error_message}"
        )
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(
            f"Not authorized to take ownership on pipeline schedule: {e.error_message}"
        )
