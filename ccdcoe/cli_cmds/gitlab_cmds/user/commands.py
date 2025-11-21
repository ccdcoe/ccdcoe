import json
import logging

import click

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.gitlab.gitlab_handler import GitlabHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "user",
    no_args_is_help=True,
    invoke_without_command=True,
    help="Gitlab user management.",
)
@click.option(
    "-s",
    "--show",
    is_flag=True,
    default=True,
    show_default=True,
    help="Show the details of the current user.",
)
@click.pass_context
def user_cmd(
    ctx,
    show: bool = False,
):
    ctx.obj = GitlabHandler()
    if not ctx.invoked_subcommand:
        if show:
            the_user = ctx.obj.user_handler.get_current_gitlab_user()
            ConsoleOutput.print(json.loads(the_user.to_json()))
