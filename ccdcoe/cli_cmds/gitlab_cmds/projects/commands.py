import logging

import click

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.gitlab.gitlab_handler import GitlabHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "project",
    no_args_is_help=True,
    invoke_without_command=True,
    help="Gitlab projects.",
)
@click.option(
    "-l",
    "--list",
    is_flag=True,
    default=True,
    show_default=True,
    help="List the projects of the current user.",
)
@click.pass_context
def project_cmd(ctx, list: bool = False):
    ctx.obj = GitlabHandler()
    if not ctx.invoked_subcommand:
        if list:
            the_groups = ctx.obj.project_handler.get_groups_list()
            ConsoleOutput.print(the_groups)
