import logging

import click
import gitlab.exceptions
from tabulate import tabulate

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.cli_cmds.cli_utils.utils import add_options
from ccdcoe.deployments.deployment_handler import DeploymentHandler
from ccdcoe.deployments.parsers.team_numbers import parse_team_number
from ccdcoe.loggers.console_logger import ConsoleLogger
from ccdcoe.cli_cmds.deploy_cmds.general_options.options import (
    team_number_option,
    branch_option,
)

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "pipeline",
    no_args_is_help=True,
    help="Perform actions on the deployment pipelines. Actions like requesting the status, cancelling pipelines \n"
    "or deleting pipelines.",
)
@click.pass_context
def pipeline_cmd(ctx):
    ctx.obj = DeploymentHandler()


@pipeline_cmd.command(
    help="Show status of deployments.",
    no_args_is_help=True,
)
@add_options(team_number_option)
@add_options(branch_option)
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
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def status(
    deployment_handler: DeploymentHandler,
    branch: str,
    team: str,
    all: bool,
    id: str = None,
):

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
        if id is None:
            deployment_handler.logger.info(f"Getting status team range: {team}...")
            header_list, entry_list = deployment_handler.get_deployment_status(
                reference=branch, team_number=parse_team_number(team)
            )
            ConsoleOutput.print(
                tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
            )
        else:
            deployment_handler.logger.info(f"Getting status pipeline id: {id}...")
            header_list, entry_list = deployment_handler.get_deployment_status(
                reference=branch, pipeline_id=id
            )
            ConsoleOutput.print(
                tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
            )


@pipeline_cmd.command(
    help="Cancel deployment pipeline.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def cancel(
    deployment_handler: DeploymentHandler,
    id: str,
):
    try:
        the_pipeline = deployment_handler.get_pipeline_by_id(id)
        the_pipeline.cancel()
        ConsoleOutput.print(f"Pipeline: {the_pipeline.get_id()} cancelled!")
    except gitlab.exceptions.GitlabPipelineCancelError as e:
        ConsoleOutput.print(f"Could not cancel pipeline: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(f"Not authorized to cancel pipeline: {e.error_message}")


@pipeline_cmd.command(
    help="Delete deployment pipeline.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def delete(
    deployment_handler: DeploymentHandler,
    id: str,
):
    try:
        the_pipeline = deployment_handler.get_pipeline_by_id(id)
        the_pipeline.delete()
        ConsoleOutput.print(f"Pipeline: {the_pipeline.get_id()} deleted!")
    except gitlab.exceptions.GitlabDeleteError as e:
        ConsoleOutput.print(f"Could not delete pipeline: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(f"Not authorized to delete pipeline: {e.error_message}")


@pipeline_cmd.command(
    help="Retry deployment pipeline.",
    no_args_is_help=True,
)
@click.option(
    "-i",
    "--id",
    help="The ID number of the pipeline you wish to see the status of.",
)
@click.pass_obj
def retry(
    deployment_handler: DeploymentHandler,
    id: str,
):
    try:
        the_pipeline = deployment_handler.get_pipeline_by_id(id)
        the_pipeline.retry()
        ConsoleOutput.print(
            ConsoleOutput.print(f"Pipeline: {the_pipeline.get_id()} started (retried)!")
        )
    except gitlab.exceptions.GitlabPipelineRetryError as e:
        ConsoleOutput.print(f"Could not retry pipeline: {e.error_message}")
    except gitlab.exceptions.GitlabAuthenticationError as e:
        ConsoleOutput.print(f"Not authorized to retry pipeline: {e.error_message}")
