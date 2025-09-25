import collections

gitlab_boolean = collections.namedtuple("boolean", ["ENABLED", "DISABLED"])(
    "true", "false"
)

deploy_modes = collections.namedtuple(
    "deploy_modes",
    [
        "DEPLOY",
        "UNDEPLOY",
        "REDEPLOY",
        "DEPLOY_SNAP",
        "DEPLOY_CLEAN_SNAP",
        "DEPLOY_CLEAN_SNAP_SHUTDOWN",
        "REVERT",
        "POWERON",
        "SHUTDOWN",
    ],
)(
    "deploy",
    "undeploy",
    "redeploy",
    "deploy-snap",
    "deploy-clean-snap",
    "deploy-clean-snap-shutdown",
    "revert",
    "poweron",
    "shutdown",
)
