import logging
import re

import click
from tabulate import tabulate

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.gitlab.gitlab_handler import GitlabHandler
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)

logger = logging.getLogger(__name__)


@click.group(
    "namespace",
    no_args_is_help=True,
    invoke_without_command=True,
)
@click.option(
    "-l",
    "--list",
    is_flag=True,
    default=False,
    show_default=True,
    help="List the namespaces.",
)
@click.option(
    "-f",
    "--filter",
    help="Filter the returned namespaces based on a given regex.",
)
@click.argument("namespace_id", required=False)
@click.pass_context
def namespace_cmd(
    ctx,
    list: bool = False,
    filter: str = None,
    namespace_id: str = None,
):
    """
    Perform namespace related operations on gitlab repositories.

    NAMESPACE_ID is the full name (e.g. 'ls/ls26') or the ID of the namespace.
    """

    ctx.obj = GitlabHandler(namespace_id=namespace_id)
    if not ctx.invoked_subcommand:
        if list:
            namespace_list = ctx.obj.project_handler.get_project_list()

            header_list = ["ID", "Namespace"]
            entry_list = []
            for namespace in namespace_list:
                entry_list.append([namespace.id, namespace.name])

            ConsoleOutput.print(
                tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
            )
        elif filter is not None:
            try:
                filter_match = re.compile(f"{filter}")
            except re.error:
                ConsoleOutput.print("Bad regex given!")
                return

            namespace_list = ctx.obj.project_handler.get_project_list()
            header_list = ["ID", "Namespace"]
            entry_list = []

            for namespace in namespace_list:
                if filter_match.match(namespace.name):
                    entry_list.append([namespace.id, namespace.name])

            ConsoleOutput.print(
                tabulate(entry_list, headers=header_list, tablefmt="fancy_grid")
            )
        else:
            click.echo(namespace_cmd.get_help(ctx))
