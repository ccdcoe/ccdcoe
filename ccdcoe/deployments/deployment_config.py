import os
import shutil

from dotenv import load_dotenv

if not os.path.exists(os.path.expanduser("~/.ccdcoe")):
    os.mkdir(os.path.expanduser("~/.ccdcoe"))

user_wd = os.path.expanduser("~/.ccdcoe")

if not os.path.exists(os.path.join(user_wd, ".env")):
    shutil.copyfile(
        os.path.join(os.path.dirname(__file__), ".env_example"),
        os.path.join(user_wd, ".env"),
    )

load_dotenv(os.path.join(user_wd, ".env"))

config_file_location = os.path.join(user_wd, ".env")

from ccdcoe.generic.utils import getenv_bool, __MANDATORY_VALUE__, getenv_str


class Config(object):
    DEBUG: bool = getenv_bool("DEBUG", "False")

    TRIGGER_TOKEN: str = getenv_str(
        "TRIGGER_TOKEN", __MANDATORY_VALUE__, True, config_file_location
    )
    PAT_TOKEN: str = getenv_str(
        "PAT_TOKEN", __MANDATORY_VALUE__, True, config_file_location
    )
    PROVIDENTIA_TOKEN: str = getenv_str(
        "PROVIDENTIA_TOKEN", __MANDATORY_VALUE__, True, config_file_location
    )

    GITLAB_URL: str = getenv_str(
        "GITLAB_URL", __MANDATORY_VALUE__, True, config_file_location
    )
    PROJECT_ROOT: str = getenv_str(
        "PROJECT_ROOT", __MANDATORY_VALUE__, True, config_file_location
    )
    PROJECT_VERSION: str = getenv_str(
        "PROJECT_VERSION", __MANDATORY_VALUE__, True, config_file_location
    )
    PROJECT_NAMESPACE: str = getenv_str(
        "PROJECT_NAMESPACE", f"{PROJECT_ROOT}/{PROJECT_VERSION}"
    )
    NEXUS_HOST: str = getenv_str(
        "NEXUS_HOST", __MANDATORY_VALUE__, True, config_file_location
    )

    EXECUTOR_DOCKER_IMAGE: str = getenv_str(
        "EXECUTOR_DOCKER_IMAGE", f"{NEXUS_HOST}/{PROJECT_VERSION}-cicd-image:latest"
    )
    TAG_RUNNER_SLIM: str = getenv_str("TAG_RUNNER_SLIM", "docker-deployer-slim")
    TAG_RUNNER_FAT: str = getenv_str("TAG_RUNNER_FAT", "docker-deployer-fat")

    PROVIDENTIA_URL: str = getenv_str(
        "PROVIDENTIA_URL", __MANDATORY_VALUE__, True, config_file_location
    )
    PROVIDENTIA_VERSION: str = getenv_str("PROVIDENTIA_VERSION", "v3")

    DEPLOYMENT_RANGE_LOWER: int = int(getenv_str("DEPLOYMENT_RANGE_LOWER", "1"))
    DEPLOYMENT_RANGE_UPPER: int = int(getenv_str("DEPLOYMENT_RANGE_UPPER", "40"))
    DEPLOYMENT_SEQUENCE_STEP: int = int(getenv_str("DEPLOYMENT_SEQUENCE_STEP", "5"))
