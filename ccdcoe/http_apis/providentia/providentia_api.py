from typing import Any

from requests import Response

from ccdcoe.http_apis.base_class.api_base_class import ApiBaseClass


class ProvidentiaApi(ApiBaseClass):
    def __init__(
        self,
        baseurl: str,
        api_path: str = "v3",
        proxies: dict = None,
        user_agent: str = "CCDCOE",
        api_key: str = "",
        **kwargs,
    ):
        super().__init__(
            baseurl=baseurl,
            api_path=api_path,
            proxies=proxies,
            user_agent=user_agent,
            **kwargs,
        )

        self.set_header_field("Authorization", f"Bearer {api_key}")

    def environments(
        self, **kwargs
    ) -> dict[str, list[dict[str, str]]] | Response | Any:
        resource = ""
        return self.call(self.methods.GET, resource, **kwargs)

    def environment(self, environment: str, **kwargs) -> dict | Response | Any:
        resource = f"{environment}"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_hosts(self, environment: str, **kwargs) -> dict | Response | Any:
        resource = f"{environment}/hosts"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_hosts_id(
        self, environment: str, host_id: str, **kwargs
    ) -> dict | Response | Any:
        resource = f"{environment}/hosts/{host_id}"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_inventory(
        self, environment: str, **kwargs
    ) -> dict | Response | Any:
        resource = f"{environment}/inventory"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_networks(self, environment: str, **kwargs) -> dict | Response | Any:
        resource = f"{environment}/networks"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_tags(self, environment: str, **kwargs) -> dict | Response | Any:
        resource = f"{environment}/tags"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_actors(self, environment: str, **kwargs) -> dict | Response | Any:
        resource = f"{environment}/actors"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_services(self, environment: str, **kwargs) -> dict | Response | Any:
        resource = f"{environment}/services"
        return self.call(self.methods.GET, resource, **kwargs)

    def environment_services_id(
        self, environment: str, service_id: str, **kwargs
    ) -> dict | Response | Any:
        resource = f"{environment}/services/{service_id}"
        return self.call(self.methods.GET, resource, **kwargs)
