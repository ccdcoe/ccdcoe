import requests
from sqlalchemy.exc import ProgrammingError

from ccdcoe.deployments.deployment_config import Config


def not_reachable(config_attr: str = None, url: str = None) -> bool | None:
    if config_attr is None and url is None:
        raise ProgrammingError("You must provide either a config_attr or a url")

    config = Config
    try:
        with requests.Session() as session:
            r = session.get(
                getattr(config, config_attr.upper()) if config_attr is not None else url
            )
            if r.status_code != 200:
                return True
    except Exception:
        return True
