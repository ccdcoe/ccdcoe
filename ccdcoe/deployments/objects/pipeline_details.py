from dataclasses import dataclass
from typing import List

from colors import colors
from dataclasses_json import dataclass_json

status_color_map = {
    "queued": "magenta",
    "running": "blue",
    "cancelled": "yellow",
    "error": "red",
    "failed": "red",
    "success": "green",
}


def colorize_status(status: str) -> str:
    if status in status_color_map:
        return colors.color(status, fg=status_color_map[status])
    else:
        return status


@dataclass_json
@dataclass
class PipelineDetails:
    id: int
    name: str
    ref: str
    status: str
    web_url: str
    updated_at: str

    def get_entry_list(self) -> List[str | int]:
        return [
            self.id,
            self.name,
            colorize_status(self.status),
            self.ref,
            self.updated_at,
            self.web_url,
        ]
