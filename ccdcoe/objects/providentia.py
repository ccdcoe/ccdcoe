import hashlib
import re
from dataclasses import dataclass
from typing import Tuple

from dataclasses_json import dataclass_json

from ccdcoe.deployments.objects.data_class_validations import Validations
from ccdcoe.generic.utils import getenv_str


@dataclass_json
@dataclass
class TeamVm:
    team_number: int
    actor_id: str
    id: str
    sequence_total: int | None
    connection_network: str
    tags: list[str]
    owner: str

    def __repr__(self):
        return f"<<{self.__class__.__name__}({self.id}_t{self.team_number:02})>>"

    @property
    def vsphere_name(self) -> list[str] | str:
        if self.actor_id == "gt":
            if self.sequence_total is None:
                return (
                    f"{getenv_str('PROJECT_VERSION')}_gt_{self.id}"
                    f"_t{self.team_number:02}"
                )
            else:
                vm_list = []
                for i in range(self.sequence_total):
                    vm_list.append(
                        f"{getenv_str('PROJECT_VERSION')}_gt_{self.id}_{i+1:02}"
                        f"_t{self.team_number:02}"
                    )
                return vm_list
        else:
            if self.sequence_total is None:
                return (
                    f"{getenv_str('PROJECT_VERSION')}_bt_t{self.team_number:02}"
                    f"_{self.connection_network}_{self.id}"
                )
            else:
                vm_list = []
                for i in range(self.sequence_total):
                    vm_list.append(
                        f"{getenv_str('PROJECT_VERSION')}_bt_t{self.team_number:02}"
                        f"_{self.connection_network}_{self.id}_{i+1:02}"
                    )
                return vm_list

    @property
    def vm_hash(self) -> dict[str, str] | str:
        if isinstance(self.vsphere_name, str):
            return self.get_hash(self.vsphere_name.encode())
        else:
            ret_dict = {}
            for each in self.vsphere_name:
                ret_dict[each] = self.get_hash(each.encode())
            return ret_dict

    @property
    def tier(self):
        top_tier_level, sub_level = self.tier_levels()
        return top_tier_level

    @property
    def full_tier(self):
        top_tier_level, sub_level = self.tier_levels()
        return sub_level

    def tier_levels(self) -> Tuple[str, str]:
        tier_regex = re.compile(r"custom_tier.*")
        tag_list = sorted(list(filter(tier_regex.match, self.tags)), reverse=True)
        if len(tag_list) == 0:
            top_tier_level, sub_level = "", ""
        else:
            tier_level = tag_list[0].replace("custom_", "").title()
            if len(tier_level) > 6:
                # tier with sub-level do some additional work....
                top_tier_level = tier_level[-2]
                sub_level = tier_level[-2:].upper()
            else:
                top_tier_level = tier_level[-1]
                sub_level = tier_level[-1]

        return top_tier_level, sub_level

    @staticmethod
    def get_hash(hash_input: bytes) -> str:
        # noinspection InsecureHash
        return hashlib.md5(hash_input).hexdigest()[:6]


@dataclass_json
@dataclass
class ProvidentiaHost:
    id: str
    actor_id: str
    owner: str
    sequence_total: int | None
    connection_network: str
    tags: list[str]

    def __repr__(self):
        return f"<<{self.__class__.__name__}({self.id})>>"

    @property
    def vm_hosts(self) -> list[TeamVm]:
        vm_host_list = []
        for i in range(
            int(getenv_str("DEPLOYMENT_RANGE_LOWER", "1")),
            int(getenv_str("DEPLOYMENT_RANGE_UPPER", "40")) + 1,
        ):
            vm_host_list.append(
                TeamVm(
                    team_number=i,
                    actor_id=self.actor_id,
                    id=self.id,
                    sequence_total=self.sequence_total,
                    connection_network=self.connection_network,
                    tags=self.tags,
                    owner=self.owner,
                )
            )
        return vm_host_list

    @property
    def tiers(self) -> list[str]:
        return list(set([x.tier for x in self.vm_hosts]))

    @property
    def full_tiers(self) -> list[str]:
        return list(set([x.full_tier for x in self.vm_hosts]))

    def vm_hosts_per_team(self, team_number: int) -> TeamVm | None:
        return [x for x in self.vm_hosts if x.team_number == team_number][0]


@dataclass_json
@dataclass
class ProvidentiaHosts(Validations):
    hosts: list[ProvidentiaHost]

    @property
    def vms_per_team(self) -> dict[int, list[TeamVm]]:
        vms_per_team = {}
        for i in range(
            int(getenv_str("DEPLOYMENT_RANGE_LOWER", "1")),
            int(getenv_str("DEPLOYMENT_RANGE_UPPER", "40")) + 1,
        ):
            vms_per_team[i] = [
                x.vm_hosts_per_team(i)
                for x in self.hosts
                if x.vm_hosts_per_team(i) is not None
            ]

        return vms_per_team

    @property
    def teams(self) -> list[str]:
        return [str(x) for x in list(self.vms_per_team.keys())]

    @property
    def tiers(self) -> list[str]:
        all_tiers = []
        for each in self.hosts:
            all_tiers.extend(each.tiers)

        return sorted(list(set([str(x) for x in all_tiers])))

    @property
    def full_tiers(self) -> list[str]:
        all_tiers = []
        for each in self.hosts:
            all_tiers.extend(each.full_tiers)

        return sorted(list(set([str(x) for x in all_tiers])))

    @property
    def sub_tiers_per_tier(self) -> dict[str, list[str]]:
        ret_dict = {}
        full_tiers = self.full_tiers
        for each in self.tiers:
            ret_dict[each] = [x for x in full_tiers if x.startswith(each)]

        return ret_dict

    def hosts_per_team_and_sub_tier(self, team: int, sub_tier: str) -> list[TeamVm]:
        return sorted(
            [x for x in self.vms_per_team[team] if x.full_tier == sub_tier.upper()],
            key=lambda x: x.id,
        )

    def host_count_per_team_and_sub_tier(self, team: int, sub_tier: str) -> int:
        hosts = self.hosts_per_team_and_sub_tier(team, sub_tier)
        count = 0
        for host in hosts:
            if host.sequence_total is None:
                count += 1
            else:
                count += int(host.sequence_total)
        return count

    def validate_hosts(self, value, field) -> list[ProvidentiaHost]:
        all_hosts = []
        for each in self.hosts:
            if not isinstance(each, ProvidentiaHost):
                if isinstance(each, dict):
                    all_hosts.append(ProvidentiaHost(**each))

            if isinstance(each, ProvidentiaHost):
                all_hosts.append(each)

        return sorted(all_hosts, key=lambda x: x.id)
