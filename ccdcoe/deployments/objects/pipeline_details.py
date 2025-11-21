from dataclasses import dataclass
from typing import List, Any

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


@dataclass_json
@dataclass
class PipelineScheduleDetails:
    id: int
    description: str
    cron: str
    cron_timezone: str
    active: bool
    ref: str
    owner: dict[str, str]
    next_run_at: str
    last_pipeline: dict[str, Any]
    variables: list[dict[str, Any]]

    @classmethod
    def from_pipelineschedule_attributes(
        cls, pipeline_schedule_attributes: dict[str, Any]
    ) -> "PipelineScheduleDetails":
        pop_list = ["project_id", "created_at", "updated_at"]
        for each in pop_list:
            pipeline_schedule_attributes.pop(each)

        return PipelineScheduleDetails(**pipeline_schedule_attributes)

    def get_entry_list(self) -> list[str]:
        return [
            self.id,
            self.description,
            self.cron,
            self.cron_timezone,
            self.active,
            self.ref,
            self.owner["name"],
            self.next_run_at,
            colorize_status(self.last_pipeline["status"]),
        ]
