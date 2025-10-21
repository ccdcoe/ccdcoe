from io import StringIO

import pytest
import yaml
from gitlab.v4.objects import ProjectCiLint

from ccdcoe.dumpers.indent_dumper import IndentDumper
from tests.helpers.skip_if import not_reachable

reachable = pytest.mark.skipif(
    not_reachable("GITLAB_URL"), reason="Skipping; cannot reach gitlab instance"
)


@reachable
class TestValidateGitlabCi:
    def test_gitlab_ci(
        self,
    ):
        from ccdcoe.deployments.deployment_handler import DeploymentHandler

        dh = DeploymentHandler()

        gitlab_ci = dh.get_gitlab_ci_from_tier_assignment()

        sio = StringIO()

        yaml.dump(
            gitlab_ci,
            sio,
            Dumper=IndentDumper,
            default_flow_style=False,
            explicit_start=True,
        )

        sio.seek(0)

        project = dh.get_project_by_namespace(namespace=dh.config.PROJECT_NAMESPACE)
        lint_result = project.ci_lint.create({"content": sio.read()})

        assert isinstance(lint_result, ProjectCiLint)
        assert lint_result.valid
