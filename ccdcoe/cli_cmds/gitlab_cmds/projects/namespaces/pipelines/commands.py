import logging

import click
import gitlab
from tabulate import tabulate

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.cli_cmds.cli_utils.utils import add_options
from ccdcoe.cli_cmds.deploy_cmds.general_options.options import branch_option
from ccdcoe.gitlab.gitlab_handler import GitlabHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "pipeline",
    no_args_is_help=True,
    invoke_without_command=True,
)
@click.pass_obj
def pipeline_cmd(
    gitlab_handler: GitlabHandler,
):
    """
    Perform namespace related operations on gitlab repositories.

    NAMESPACE_ID is the full name (e.g. 'ls/ls26') or the ID of the namespace.
    """
    pass


@pipeline_cmd.command(
    "status",
    no_args_is_help=True,
)
@add_options(branch_option)
@click.option(
    "-a",
    "--all",
    is_flag=True,
    default=False,
    show_default=True,
    help="Show status of all available pipelines ran without the last 4 hours.",
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def status_cmd(
    gitlab_handler: GitlabHandler,
    branch: str,
    all: bool,
    id: str = None,
):
    if gitlab_handler.namespace_id is not None:
        if all:
            header_list, entry_list = (
                gitlab_handler.pipeline_handler.get_pipeline_status(
                    gitlab_handler.namespace_id, reference=branch, fetch_all=True
                )
            )
        else:
            header_list, entry_list = (
                gitlab_handler.pipeline_handler.get_pipeline_status(
                    gitlab_handler.namespace_id, reference=branch, pipeline_id=id
                )
            )

        ConsoleOutput.print(
            tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
        )


@pipeline_cmd.command(
    help="Cancel pipeline.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def cancel(
    gitlab_handler: GitlabHandler,
    id: str,
):
    try:
        the_pipeline = gitlab_handler.pipeline_handler.get_pipeline_by_id(
            namespace_id=gitlab_handler.namespace_id, pipeline_id=id
        )
        the_pipeline.cancel()
        ConsoleOutput.print(f"Pipeline: {the_pipeline.get_id()} cancelled!")
    except gitlab.exceptions.GitlabPipelineCancelError as e:
        ConsoleOutput.print(f"Could not cancel pipeline: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(f"Not authorized to cancel pipeline: {e.error_message}")


@pipeline_cmd.command(
    help="Delete pipeline.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def delete(
    gitlab_handler: GitlabHandler,
    id: str,
):
    try:
        the_pipeline = gitlab_handler.pipeline_handler.get_pipeline_by_id(
            namespace_id=gitlab_handler.namespace_id, pipeline_id=id
        )
        the_pipeline.delete()
        ConsoleOutput.print(f"Pipeline: {the_pipeline.get_id()} deleted!")
    except gitlab.exceptions.GitlabDeleteError as e:
        ConsoleOutput.print(f"Could not delete pipeline: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(f"Not authorized to delete pipeline: {e.error_message}")


@pipeline_cmd.command(
    help="Retry pipeline.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def retry(
    gitlab_handler: GitlabHandler,
    id: str,
):
    try:
        the_pipeline = gitlab_handler.pipeline_handler.get_pipeline_by_id(
            namespace_id=gitlab_handler.namespace_id, pipeline_id=id
        )
        the_pipeline.retry()
        ConsoleOutput.print(
            ConsoleOutput.print(f"Pipeline: {the_pipeline.get_id()} started (retried)!")
        )
    except gitlab.exceptions.GitlabPipelineRetryError as e:
        ConsoleOutput.print(f"Could not retry pipeline: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(f"Not authorized to retry pipeline: {e.error_message}")
