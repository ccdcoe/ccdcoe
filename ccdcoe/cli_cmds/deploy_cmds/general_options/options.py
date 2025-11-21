import click

from ccdcoe.cli_cmds.cli_utils.mutex import Mutex

team_number_option = [
    click.option(
        "-t",
        "--team",
        show_default=True,
        default="28",
        help="The team number to deploy; this could be a comma separated (1,2) or hyphen separated (3-7) string "
        "or a combination of both. So entering '1,2' will deploy both team 1 and team 2; entering '3-7' will "
        "deploy teams 3 through 7 and entering 1,2,3-7,9 will deploy teams 1,2,3,4,5,6,7 and 9",
    )
]
branch_option = [
    click.option(
        "-b",
        "--branch",
        type=str,
        default="main",
        show_default=True,
        help="Limits the deployment status to this branch.",
    )
]
skip_vulns_option = [
    click.option(
        "-s",
        "--skip_vulns",
        type=bool,
        default=False,
        show_default=True,
        help="Should the vulnerability deployment be skipped.",
    )
]
snapshot_option = [
    click.option(
        "--snapshot",
        help="Snapshot systems after deployment",
        is_flag=True,
        default=True,
        show_default=True,
    ),
    click.option(
        "--snap_name",
        help="Name of the snapshot",
        type=str,
        default="CLEAN",
        show_default=True,
    ),
]
deploy_mode_option = [
    click.option(
        "--deploy",
        help="Set mode to deploy",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--undeploy",
        help="Set mode to undeploy",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--snap_deploy",
        help="Set mode to deploy-snap",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--clean_snap_deploy",
        help="Set mode to deploy-clean-snap",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "revert",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--revert",
        help="Set mode to revert",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "poweron",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--poweron",
        help="Set mode to poweron",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "shutdown",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--shutdown",
        help="Set mode to shutdown",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "clean_snap_deploy_shutdown",
        ],
    ),
    click.option(
        "--clean_snap_deploy_shutdown",
        help="Set mode to deploy-clean-snap-shutdown, i.e. clean snap and keep VM powered off after",
        is_flag=True,
        cls=Mutex,
        not_required_if=[
            "deploy",
            "undeploy",
            "snap_deploy",
            "clean_snap_deploy",
            "revert",
            "poweron",
            "shutdown",
        ],
    ),
]
skip_hosts_option = [
    click.option(
        "--skip_hosts",
        help="Comma separated list of hosts to skip",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]
only_hosts_option = [
    click.option(
        "--only_hosts",
        help="Comma separated list of hosts to deploy, everything else will be ignored",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]
actor_option = [
    click.option(
        "--actor",
        help="Comma separated list of actors to deploy, by default all actors are deployed",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]
large_tiers_option = [
    click.option(
        "--large_tiers",
        help="Comma separated list of tiers that need more resources",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]
standalone_tiers_option = [
    click.option(
        "--standalone_tiers",
        help="Comma separated list of tiers that have standalone VMs, i.e. no team number",
        default="",
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]
nova_option = [
    click.option(
        "-n",
        "--nova_version",
        type=click.Choice(["PRODUCTION", "STAGING"], case_sensitive=False),
        default="PRODUCTION",
        show_default=True,
        help="Choose nova.core version",
    )
]
docker_image_count_option = [
    click.option(
        "--docker_image_count",
        help="Number of available docker images",
        default=1,
        is_flag=False,
        flag_value="",
        show_default=True,
    )
]
