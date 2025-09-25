from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json

from ccdcoe.deployments.deployment_config import Config
from ccdcoe.deployments.generic.constants import gitlab_boolean, deploy_modes
from ccdcoe.deployments.objects.data_class_validations import Validations
from ccdcoe.generic.utils import str2bool

config = Config


# noinspection PyPep8Naming
@dataclass_json
@dataclass
class PipelineVars(Validations):
    GIT_CLEAN_FLAGS: str = "none"
    CICD_TEAM: str = "28"
    SKIP_VULNS: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER0: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER1: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER2: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER3: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER4: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER5: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER6: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER7: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER8: str = gitlab_boolean.DISABLED
    REDEPLOY_TIER9: str = gitlab_boolean.DISABLED
    SNAPSHOT: str = gitlab_boolean.ENABLED
    SNAPSHOT_NAME: str = "CLEAN"
    DEPLOY_MODE: str = deploy_modes.REDEPLOY
    DEPLOY_DESCRIPTION: str = "NONE"
    SKIP_HOSTS: str = ""
    ONLY_HOSTS: str = ""
    ACTOR: str = ""
    LARGE_TIERS: str = ""
    STANDALONE_TIERS: str = ""
    IGNORE_DEPLOY_ORDER: str = gitlab_boolean.DISABLED
    DOCKER_IMAGE_COUNT: int = 1
    NOVA_VERSION: str = "PRODUCTION"

    def as_dict(self) -> dict[str, Any]:
        # noinspection PyUnresolvedReferences
        return self.to_dict()

    def validate_CICD_TEAM(self, value: str | int, **_) -> str:
        def check_range(the_value: int) -> bool:
            if (
                config.DEPLOYMENT_RANGE_LOWER
                <= the_value
                <= config.DEPLOYMENT_RANGE_UPPER
            ):
                return True
            return False

        if isinstance(self.CICD_TEAM, int):
            try:
                if check_range(self.CICD_TEAM):
                    return str(value)
                else:
                    raise ValueError(
                        f"CICD_TEAM must be in the range "
                        f"[{config.DEPLOYMENT_RANGE_LOWER}, {config.DEPLOYMENT_RANGE_UPPER}]"
                    )
            except TypeError:
                raise ValueError(
                    "CICD_TEAM must be a string or an integer that can be converted to an string."
                )
        elif isinstance(self.CICD_TEAM, str):
            try:
                if check_range(int(self.CICD_TEAM)):
                    return value
                else:
                    raise ValueError(
                        f"CICD_TEAM must be in the range "
                        f"[{config.DEPLOYMENT_RANGE_LOWER}, {config.DEPLOYMENT_RANGE_UPPER}]"
                    )
            except ValueError:
                raise ValueError(
                    f"CICD_TEAM must be a string representation of an integer, "
                    f"and {value} could not be converted to an integer."
                )
            except TypeError:
                raise ValueError(
                    "CICD_TEAM must be a string representation of an integer."
                )
        else:
            return ValueError(
                f"CICD_TEAM must be a string representation of an integer or an integer that can be "
                f"converted to an string. NOT of type: {type(self.CICD_TEAM)}"
            )

    def validate_SNAPSHOT_NAME(self, value: str, **_) -> str:
        if isinstance(self.SNAPSHOT_NAME, str):
            return value
        else:
            return ValueError(
                f"SNAPSHOT_NAME must be a string. NOT of type: {type(value)}"
            )

    def validate_DEPLOY_MODE(self, value: str, **_) -> str:
        if isinstance(self.DEPLOY_MODE, str):
            return value
        else:
            return ValueError(
                f"DEPLOY_MODE must be a string. NOT of type: {type(value)}"
            )

    def validate_DEPLOY_DESCRIPTION(self, value: str, **_) -> str:
        if isinstance(self.DEPLOY_DESCRIPTION, str):
            return value
        else:
            return ValueError(
                f"DEPLOY_DESCRIPTION must be a string. NOT of type: {type(value)}"
            )

    def validate_SKIP_HOSTS(self, value: str, **_) -> str:
        if isinstance(self.SKIP_HOSTS, str):
            return value
        else:
            return ValueError(
                f"SKIP_HOSTS must be a string. NOT of type: {type(value)}"
            )

    def validate_ONLY_HOSTS(self, value: str, **_) -> str:
        if isinstance(self.ONLY_HOSTS, str):
            return value
        else:
            return ValueError(
                f"ONLY_HOSTS must be a string. NOT of type: {type(value)}"
            )

    def validate_ACTOR(self, value: str, **_) -> str:
        if isinstance(self.ACTOR, str):
            return value
        else:
            return ValueError(f"ACTOR must be a string. NOT of type: {type(value)}")

    def validate_LARGE_TIERS(self, value: str, **_) -> str:
        if isinstance(self.LARGE_TIERS, str):
            return value
        else:
            return ValueError(
                f"LARGE_TIERS must be a string. NOT of type: {type(value)}"
            )

    def validate_STANDALONE_TIERS(self, value: str, **_) -> str:
        if isinstance(self.STANDALONE_TIERS, str):
            return value
        else:
            return ValueError(
                f"STANDALONE_TIERS must be a string. NOT of type: {type(value)}"
            )

    def validate_DOCKER_IMAGE_COUNT(self, value: int, **_) -> int:
        if isinstance(self.DOCKER_IMAGE_COUNT, int):
            return value
        else:
            return ValueError(
                f"DOCKER_IMAGE_COUNT must be an integer. NOT of type: {type(value)}"
            )

    def validate_NOVA_VERSION(self, value: str, **_) -> str:
        if isinstance(self.NOVA_VERSION, str):
            return value
        else:
            return ValueError(
                f"NOVA_VERSION must be a string. NOT of type: {type(value)}"
            )

    @staticmethod
    def check_boolean_string_fields(value: str, field_name: str):
        if isinstance(value, str):
            try:
                check = str2bool(value)
                if check:
                    return gitlab_boolean.ENABLED
                else:
                    return gitlab_boolean.DISABLED
            except ValueError as e:
                raise
        elif isinstance(value, bool):
            if value:
                return gitlab_boolean.ENABLED
            else:
                return gitlab_boolean.DISABLED
        else:
            raise ValueError(
                f"{field_name} must be a string representation of an boolean. NOT of type: {type(value)}"
            )

    def validate_SNAPSHOT(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "SNAPSHOT")

    def validate_SKIP_VULNS(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "SKIP_VULNS")

    def validate_REDEPLOY_TIER0(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER0")

    def validate_REDEPLOY_TIER1(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER1")

    def validate_REDEPLOY_TIER2(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER2")

    def validate_REDEPLOY_TIER3(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER3")

    def validate_REDEPLOY_TIER4(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER4")

    def validate_REDEPLOY_TIER5(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER5")

    def validate_REDEPLOY_TIER6(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER6")

    def validate_REDEPLOY_TIER7(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER7")

    def validate_REDEPLOY_TIER8(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER8")

    def validate_REDEPLOY_TIER9(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "REDEPLOY_TIER9")

    def validate_IGNORE_DEPLOY_ORDER(self, value: str, **_) -> str:
        return self.check_boolean_string_fields(value, "IGNORE_DEPLOY_ORDER")
