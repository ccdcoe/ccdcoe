import inspect
import logging

from gitlab import Gitlab
from gitlab.v4.objects import Project

from ccdcoe.deployments.deployment_config import Config
from ccdcoe.loggers.console_logger import ConsoleLogger

logging.setLoggerClass(ConsoleLogger)


class GitlabBase(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__repr__())

        self.config = Config

    def get_gitlab_obj(self) -> Gitlab:
        return Gitlab(url=self.config.GITLAB_URL, private_token=self.config.PAT_TOKEN)

    def get_project_by_namespace(
        self, namespace: str, lazy: bool = True, **kwargs
    ) -> Project:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        with self.get_gitlab_obj() as gl:
            project = gl.projects.get(namespace, lazy=lazy, **kwargs)

        return project
