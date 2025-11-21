import logging

from ccdcoe.gitlab.gitlab_pipeline.gitlab_pipeline import GitlabPipeline
from ccdcoe.gitlab.gitlab_project.gitlab_project import GitlabProject
from ccdcoe.gitlab.gitlab_user.gitlab_user import GitlabUser


class GitlabHandler(object):
    def __init__(self, namespace_id: int | str = None):
        self.logger = logging.getLogger(__name__)

        self.namespace_id = namespace_id

        self.user_handler = GitlabUser()
        self.project_handler = GitlabProject()
        self.pipeline_handler = GitlabPipeline()

    def __repr__(self):
        return "<GitlabHandler>"
