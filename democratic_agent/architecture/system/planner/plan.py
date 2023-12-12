from enum import Enum
from pydantic import Field, PrivateAttr
from typing import List

from democratic_agent.chat.parser.loggable_base_model import LoggableBaseModel


class PlanStatus(Enum):
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


class Plan(LoggableBaseModel):
    summary: str = Field(description="Summary of the request's current status.")
    task_completed: bool = Field(
        description="Should be False if there is a need to execute any tool. Set to True only if the task is already complete with no further action required."
    )
    step: str = Field(description="Next step to solve the problem")
    potential_tools: List[str] = Field(
        description="Descriptions of potential tools to be used for database searches in the current step."
    )
    selected_tools: List[str] = Field(
        description="Specific tools chosen from the database search results to complete the current step."
    )
    _status: PlanStatus = PrivateAttr(default=PlanStatus.IN_PROGRESS)

    def get_status(self):
        return self._status

    def update_status(self, status: PlanStatus):
        self._status = status
