import logging
from importlib.metadata import version
from logging.config import dictConfig

import click

from ccdcoe.cli_cmds.deploy_cmds import commands as deploy_commands
from ccdcoe.cli_cmds.pipeline_cmds import commands as pipeline_commands
from ccdcoe.cli_cmds.providentia_cmds import commands as providentia_commands
from ccdcoe.loggers.console_logger import ConsoleLogger

__version__ = VERSION = version("ccdcoe")


@click.group(no_args_is_help=True)
@click.version_option(version=VERSION)
@click.option(
    "-vv",
    "--verbose",
    help="Enable verbose (DEBUG) logging",
    show_default=True,
    default=False,
    flag_value=True,
)
@click.option(
    "--log_level",
    show_default=True,
    default="INFO",
    help="DEBUG, INFO (default), WARNING, ERROR, CRITICAL",
)
@click.pass_context
def main(ctx, log_level, verbose):
    if ctx.invoked_subcommand is None:
        click.echo(main.get_help(ctx))

    logDict = {
        "version": 1,
        "formatters": {"simpleFormatter": {"format": "%(asctime)s %(message)s"}},
        "handlers": {
            "consoleHandler": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "simpleFormatter",
            }
        },
        "root": {
            "level": getattr(logging, log_level if not verbose else "DEBUG"),
            "handlers": ["consoleHandler"],
        },
    }

    dictConfig(logDict)

    logging.setLoggerClass(ConsoleLogger)

    logger = logging.getLogger(__name__)

    logger.debug("DEBUG Logging configured.....")

main.add_command(deploy_commands.deploy_cmd)
main.add_command(providentia_commands.providentia_cmd)
main.add_command(pipeline_commands.pipeline_cmd)
