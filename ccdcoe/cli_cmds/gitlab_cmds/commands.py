import logging

import click

from ccdcoe.gitlab.gitlab_handler import GitlabHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "gitlab",
    no_args_is_help=True,
    help="Perform gitlab related operations.",
)
@click.pass_context
def gitlab_cmd(ctx):
    ctx.obj = GitlabHandler()
