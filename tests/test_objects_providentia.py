import os

import pytest

from ccdcoe.objects.providentia import ProvidentiaHost, ProvidentiaHosts


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("PROJECT_VERSION", "test25")
    monkeypatch.setenv("DEPLOYMENT_RANGE_LOWER", "1")
    monkeypatch.setenv("DEPLOYMENT_RANGE_UPPER", "2")


def make_host(actor_id="bt", egress_networks=None, connection_network=None, sequence_total=None):
    return ProvidentiaHost(
        id="myhost",
        actor_id=actor_id,
        owner="owner",
        sequence_total=sequence_total,
        connection_network=connection_network or "con_net",
        egress_networks=egress_networks or ["net1_dmz"],
        tags=["custom_tier1"],
    )


class TestProvidentiaHostEgressNetworks:
    def test_field_stored(self):
        host = make_host(egress_networks=["net1_dmz", "other_net"])
        assert host.egress_networks == ["net1_dmz", "other_net"]

    def test_vm_hosts_pass_egress_networks(self):
        host = make_host(egress_networks=["net1_dmz"])
        for vm in host.vm_hosts:
            assert vm.egress_networks == ["net1_dmz"]

    def test_from_dict_includes_egress_networks(self):
        data = {
            "id": "myhost",
            "actor_id": "bt",
            "owner": "owner",
            "sequence_total": None,
            "connection_network": "con_net",
            "egress_networks": ["net1_dmz"],
            "tags": ["custom_tier1"],
        }
        host = ProvidentiaHost(**data)
        assert host.egress_networks == ["net1_dmz"]


class TestTeamVmVsphereName:
    def test_bt_single_uses_egress_network(self):
        host = make_host(actor_id="bt", connection_network="conn_net", egress_networks=["egress_net_1"])
        vm = host.vm_hosts[0]
        assert vm.vsphere_name == "test25_bt_t01_egress_net_1_myhost"

    def test_gt_single_uses_egress_network(self):
        host = make_host(actor_id="gt", egress_networks=["gt_net"])
        vm = host.vm_hosts[0]
        assert "gt_net" in vm.vsphere_name
        assert "con_net" not in vm.vsphere_name

    def test_bt_sequence_uses_egress_network(self):
        host = make_host(actor_id="bt", egress_networks=["net1_dmz"], sequence_total=3)
        vm = host.vm_hosts[0]
        names = vm.vsphere_name
        assert isinstance(names, list)
        assert len(names) == 3
        for name in names:
            assert "net1_dmz" in name
            assert "con_net" not in name

    def test_gt_sequence_uses_egress_network(self):
        host = make_host(actor_id="gt", egress_networks=["gt_net"], sequence_total=2)
        vm = host.vm_hosts[0]
        names = vm.vsphere_name
        assert isinstance(names, list)
        for name in names:
            assert "gt_net" in name

    def test_vsphere_name_format_bt(self):
        host = make_host(actor_id="bt", egress_networks=["net1_dmz"])
        vm = host.vm_hosts[0]  # team_number=1
        assert vm.vsphere_name == "test25_bt_t01_net1_dmz_myhost"

    def test_vsphere_name_format_gt(self):
        host = make_host(actor_id="gt", egress_networks=["gt_net"])
        vm = host.vm_hosts[0]  # team_number=1
        assert vm.vsphere_name == "test25_gt_t01_gt_net_myhost"


class TestProvidentiaHostsValidation:
    def test_validate_hosts_coerces_dicts(self):
        data = {
            "id": "myhost",
            "actor_id": "bt",
            "owner": "owner",
            "sequence_total": None,
            "connection_network": "con_net",
            "egress_networks": ["net1_dmz"],
            "tags": [],
        }
        hosts = ProvidentiaHosts(hosts=[data])
        assert len(hosts.hosts) == 1
        assert isinstance(hosts.hosts[0], ProvidentiaHost)
        assert hosts.hosts[0].egress_networks == ["net1_dmz"]
