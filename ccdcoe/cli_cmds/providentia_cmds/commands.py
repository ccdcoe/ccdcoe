import click

from ccdcoe.cli_cmds.cli_utils.output import ConsoleOutput
from ccdcoe.deployments.deployment_config import Config
from ccdcoe.http_apis.providentia.providentia_api import ProvidentiaApi

config = Config


@click.group(
    "providentia",
    no_args_is_help=True,
    help="Perform providentia related operations.",
)
@click.pass_context
def providentia_cmd(ctx):
    ctx.obj = ProvidentiaApi(
        baseurl=config.PROVIDENTIA_URL,
        api_path=config.PROVIDENTIA_VERSION,
        api_key=config.PROVIDENTIA_TOKEN,
    )


@providentia_cmd.command(
    # help="Hosts related queries via the providentia API.",
    no_args_is_help=True,
)
@click.argument("host_id", required=False)
@click.option(
    "-l",
    "--list",
    is_flag=True,
    help="List all hosts in current inventory",
)
@click.pass_obj
def hosts(providentia_api: ProvidentiaApi, list: bool, host_id: str):
    """
    Hosts related queries via the providentia API.\n\n
    HOST_ID: id of the host you wish to get details from.
    """
    if list:
        ret_data = providentia_api.environment_hosts(config.PROJECT_VERSION)
        if "result" in ret_data:
            ConsoleOutput.print(ret_data["result"])
        else:
            ConsoleOutput.print(ret_data)
    else:
        ret_data = providentia_api.environment_hosts_id(config.PROJECT_VERSION, host_id)
        if "result" in ret_data:
            if "instances" in ret_data["result"]:
                all_instances = ret_data["result"].pop("instances")
                ret_data["result"]["instances"] = len(all_instances)

        ConsoleOutput.print(ret_data["result"])
