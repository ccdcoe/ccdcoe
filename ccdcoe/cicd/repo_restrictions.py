from typing import Tuple


class RepoRestrictions(object):

    def __init__(self, repo_name: str):
        self.repo_name = repo_name

        self.name, self.segment, self.indicator, self.domain, self.tld = (
            self.parse_repo_name()
        )

    def parse_repo_name(self) -> Tuple[str, str, str, str, str]:
        parts = self.repo_name.split(".")
        
        if len(parts) == 5:
            return tuple(parts)
        elif len(parts) == 6:
            # Combine parts 2 and 3 into a single segment
            segment = f"{parts[1]}.{parts[2]}"
            return (parts[0], segment, parts[3], parts[4], parts[5])
        else:
            raise ValueError(
                f"Invalid repo name format: {self.repo_name}. "
                f"Expected 5 or 6 dot-separated parts, got {len(parts)}"
            )

    def check_execution_needed(self, check_dict: dict[str, bool]) -> bool:
        if self.segment in check_dict:
            return check_dict[self.segment]
        return True
