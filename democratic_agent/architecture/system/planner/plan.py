from enum import Enum
from pydantic import Field
from typing import List

from democratic_agent.chat.parser.loggable_base_model import LoggableBaseModel


class PlanStatus(Enum):
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


class Plan(LoggableBaseModel):
    summary: str = Field(description="The step that should be accomplish next or the final result of the plan.")
    status: PlanStatus = Field(description="Tool status", default=PlanStatus.IN_PROGRESS)
    tools: List[str] = Field(description="The name of the tools that should be used to accomplish the step.", default=[])

    def get_status(self):
        return self.status

    def update_status(self, status: PlanStatus):
        self.status = status
