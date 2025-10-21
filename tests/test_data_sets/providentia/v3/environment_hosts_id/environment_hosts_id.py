import json
import os
import pytest

__LOCATION__ = os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def v3_environment_hosts_id_endpoint():
    with open(os.path.join(__LOCATION__, "test_data.json"), "r") as f:
        data = json.loads(f.read())

    yield data
