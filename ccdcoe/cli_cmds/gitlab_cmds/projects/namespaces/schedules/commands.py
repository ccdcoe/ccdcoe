import logging

import click
import gitlab
from gitlab.v4.objects import ProjectPipelineSchedule
from tabulate import tabulate

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.gitlab.gitlab_handler import GitlabHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "schedule",
    no_args_is_help=True,
)
@click.pass_obj
def schedule_cmd(gitlab_handler: GitlabHandler):
    """
    Perform namespace related operations on gitlab repositories.

    NAMESPACE_ID is the full name (e.g. 'ls/ls26') or the ID of the namespace.
    """
    pass


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
    help="Show status of all available schedules pipelines.",
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline.",
)
@click.pass_obj
def status(
    gitlab_handler: GitlabHandler,
    all: bool,
    id: str = None,
):
    if all:
        header_list, entry_list = (
            gitlab_handler.pipeline_handler.get_pipeline_schedule_status(
                namespace_id=gitlab_handler.namespace_id, fetch_all=True
            )
        )
    else:
        header_list, entry_list = (
            gitlab_handler.pipeline_handler.get_pipeline_schedule_status(
                namespace_id=gitlab_handler.namespace_id, schedule_id=id
            )
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
    gitlab_handler: GitlabHandler,
    id: str = None,
):
    try:
        the_schedule: ProjectPipelineSchedule = (
            gitlab_handler.pipeline_handler.get_pipeline_schedule(
                namespace_id=gitlab_handler.namespace_id, schedule_id=id
            )
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
    gitlab_handler: GitlabHandler,
    id: str = None,
):
    try:
        the_schedule: ProjectPipelineSchedule = (
            gitlab_handler.pipeline_handler.get_pipeline_schedule(
                namespace_id=gitlab_handler.namespace_id, schedule_id=id
            )
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
