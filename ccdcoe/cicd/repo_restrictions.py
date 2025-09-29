from typing import Tuple


class RepoRestrictions(object):

    def __init__(self, repo_name: str):
        self.repo_name = repo_name

        self.name, self.segment, self.indicator, self.domain, self.tld = (
            self.parse_repo_name()
        )

    def parse_repo_name(self) -> Tuple[str, str, str, str, str]:
        return self.repo_name.split(".")

    def check_execution_needed(self, check_dict: dict[str, bool]) -> bool:
        if self.segment in check_dict:
            return check_dict[self.segment]
        return True
