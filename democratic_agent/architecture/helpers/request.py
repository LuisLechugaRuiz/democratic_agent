from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, PrivateAttr
import uuid


class RequestStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"
    WAITING_FEEDBACK = "waiting_feedback"
    # CANCELED = "canceled"

    def __init__(self, status: str):
        self.status = status


class Request(BaseModel):
    request: str = Field(
        description="Request that includes: 1) The primary goal or 'Objective', 2) The 'Requirements' necessary for task completion, and 3) Any 'Constraints' such as time, budget, or resources. Please structure your request in a single sentence using semicolons to separate these three components."
    )
    _status: RequestStatus = PrivateAttr(default=RequestStatus.NOT_STARTED)
    _feedback: Optional[str] = PrivateAttr(default=None)
    _id: int = PrivateAttr(default=uuid.uuid4().int)

    def update_status(self, status: RequestStatus, feedback: Optional[str] = None):
        self._status = status
        if feedback:
            self._feedback = feedback

    def __repr__(self):
        repr = f"Objective: {self.objective}, requirements: {self.requirements}, constraints: {self.constraints}, status: {self._status}"
        if self._feedback:
            repr += f", feedback: {self._feedback}"
        return repr
