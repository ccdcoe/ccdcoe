from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json

from ccdcoe.deployments.generic.constants import gitlab_boolean


@dataclass_json
@dataclass
class Tiers:
    def as_dict(self) -> dict[str, Any]:
        # noinspection PyUnresolvedReferences
        return self.to_dict(self)

    def show_bear_level(self):
        the_dict = self.as_dict()
        ret_dict = {}
        for key, value in the_dict.items():
            ret_dict[key.replace("REDEPLOY_", "")] = value
        return ret_dict


@dataclass_json
@dataclass
class Tier0(Tiers):
    REDEPLOY_TIER0: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier1(Tiers):
    REDEPLOY_TIER1: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier2(Tiers):
    REDEPLOY_TIER2: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier3(Tiers):
    REDEPLOY_TIER3: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier4(Tiers):
    REDEPLOY_TIER4: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier5(Tiers):
    REDEPLOY_TIER5: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier6(Tiers):
    REDEPLOY_TIER6: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier7(Tiers):
    REDEPLOY_TIER7: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier8(Tiers):
    REDEPLOY_TIER8: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class Tier9(Tiers):
    REDEPLOY_TIER9: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier1(Tier0):
    REDEPLOY_TIER1: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier2(FullTier1):
    REDEPLOY_TIER2: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier3(FullTier2):
    REDEPLOY_TIER3: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier4(FullTier3):
    REDEPLOY_TIER4: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier5(FullTier4):
    REDEPLOY_TIER5: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier6(FullTier5):
    REDEPLOY_TIER6: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier7(FullTier6):
    REDEPLOY_TIER7: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier8(FullTier7):
    REDEPLOY_TIER8: str = gitlab_boolean.ENABLED


@dataclass_json
@dataclass
class FullTier9(FullTier8):
    REDEPLOY_TIER9: str = gitlab_boolean.ENABLED
