from ccdcoe.cli_cmds.objects.namespaces import GitlabNamespace
from ccdcoe.gitlab.gitlab_base import GitlabBase


class GitlabProject(GitlabBase):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"<<{__class__.__name__}>>"

    def get_groups_list(self):
        gl = self.get_gitlab_obj()
        groups = gl.groups.list(get_all=True)
        top_level_projects = [x for x in groups if "/" not in x.attributes["full_path"]]
        return sorted([x.name for x in top_level_projects])

    def get_project_list(self) -> list[GitlabNamespace]:
        gl = self.get_gitlab_obj()
        projects = gl.projects.list(get_all=True)
        return sorted(
            [
                GitlabNamespace(**{"id": x.id, "name": x.path_with_namespace})
                for x in projects
            ],
            key=lambda x: x.name,
        )
