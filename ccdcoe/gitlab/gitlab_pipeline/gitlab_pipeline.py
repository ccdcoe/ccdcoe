import datetime
import inspect
from typing import Tuple

import gitlab
from gitlab.v4.objects import ProjectPipelineSchedule, ProjectPipeline

from ccdcoe.deployments.deployment_handler import PipelineFilter
from ccdcoe.deployments.objects.pipeline_details import (
    PipelineScheduleDetails,
    PipelineDetails,
)
from ccdcoe.gitlab.gitlab_base import GitlabBase


class GitlabPipeline(GitlabBase):
    def __init__(self):
        super().__init__()

    def get_pipeline_by_id(
        self,
        namespace_id: int | str,
        pipeline_id: int | str,
    ) -> ProjectPipeline | None:  # pragma: no cover

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        try:
            the_project = self.get_project_by_namespace(namespace_id)

            pipeline = the_project.pipelines.get(pipeline_id)

            self.logger.debug(f"Fetched pipeline with id {pipeline_id}: {pipeline}")
            return pipeline

        except gitlab.exceptions.GitlabGetError as e:
            self.logger.error(
                f"Pipeline with id {pipeline_id} could not be fetched -> {e}"
            )
            return None

    def get_last_deployment_pipeline(
        self,
        namespace_id: int | str,
        reference: str = "main",
        update_delta_in_hours: int = 4,
        return_pipeline_details: bool = True,
    ) -> ProjectPipeline | list[PipelineDetails] | None:  # pragma: no cover
        """
        in order to limit the amount of records coming back; a time cap is used; so this command only fetches the
        results from pipelines that are updated the last 4 hours (default; can be controlled via the \
        'update_delta_in_hours' variable). If that yields more then 1 result; it will return the last entry.
        """
        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        date_time = datetime.datetime.now()
        date_time_delta = datetime.timedelta(hours=update_delta_in_hours)

        iso_formatted_delta = (date_time - date_time_delta).isoformat()

        the_project = self.get_project_by_namespace(namespace_id)

        pipelines = the_project.pipelines.list(
            ref=reference,
            get_all=True,
            updated_after=iso_formatted_delta,
        )

        pf = PipelineFilter(pipelines=pipelines)

        if len(pipelines) == 0:
            return None

        if return_pipeline_details:
            return pf.pipelines_return_details()
        else:
            return pipelines[0]

    def get_pipeline_status(
        self,
        namespace_id: int | str,
        reference: str = "main",
        fetch_all: bool = False,
        pipeline_id: int | str = None,
    ) -> Tuple[list[str], list[str]]:  # pragma: no cover

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        header_list = ["ID", "Name", "Status", "Branch", "Updated", "Url"]
        entry_list = []
        if fetch_all:
            details_obj = self.get_last_deployment_pipeline(
                namespace_id=namespace_id,
                reference=reference,
                return_pipeline_details=True,
            )
            if details_obj is not None:
                entry_list.extend([x.get_entry_list() for x in details_obj])
        else:
            pipeline_obj = self.get_pipeline_by_id(
                namespace_id=namespace_id, pipeline_id=pipeline_id
            )
            if pipeline_obj is not None:
                details_obj = PipelineDetails(
                    pipeline_obj.id,
                    pipeline_obj.name,
                    pipeline_obj.ref,
                    pipeline_obj.status,
                    pipeline_obj.web_url,
                    pipeline_obj.updated_at,
                )
                entry_list.extend([details_obj.get_entry_list()])

        return header_list, entry_list

    def get_pipeline_schedule(
        self, namespace_id: str | int, schedule_id: int = None, fetch_all: bool = False
    ) -> ProjectPipelineSchedule | list[ProjectPipelineSchedule]:
        pass

        the_project = self.get_project_by_namespace(namespace_id)

        if fetch_all:
            return the_project.pipelineschedules.list(get_all=True)
        else:
            return the_project.pipelineschedules.get(schedule_id)

    def get_pipeline_schedule_status(
        self, namespace_id: int | str, schedule_id: int = None, fetch_all: bool = False
    ) -> Tuple[list[str], list[str]]:

        self.logger.debug(
            f"Method '{inspect.currentframe().f_code.co_name}' called with arguments: {locals()}"
        )

        header_list = [
            "ID",
            "Description",
            "Cron",
            "TZ",
            "Active",
            "Branch",
            "Owner",
            "Next Run",
            "Last run result",
            "Variables"
        ]
        entry_list = []
        all_schedule_objs = []
        if fetch_all:
            all_schedules = self.get_pipeline_schedule(
                namespace_id=namespace_id, fetch_all=fetch_all
            )
            all_ids = [x.id for x in all_schedules]

            for each in all_ids:
                all_schedule_objs.append(
                    self.get_pipeline_schedule(
                        namespace_id=namespace_id, schedule_id=each
                    )
                )
        else:
            all_schedule_objs.append(
                self.get_pipeline_schedule(
                    namespace_id=namespace_id, schedule_id=schedule_id
                )
            )
        all_schedule_objs = [
            PipelineScheduleDetails.from_pipelineschedule_attributes(x.attributes)
            for x in all_schedule_objs
        ]
        entry_list.extend([x.get_entry_list() for x in all_schedule_objs])

        return header_list, entry_list
