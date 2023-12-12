import logging
from typing import Callable, Dict, Optional, Tuple
from pydantic import BaseModel, Field

from democratic_agent.architecture.helpers.request import Request
from democratic_agent.chat.chat import Chat
from democratic_agent.utils.helpers import colored
from democratic_agent.utils.process import Process

LOG = logging.getLogger(__name__)


class Response(BaseModel):
    """Response from chatbot"""

    response: str = Field(description="Response to the user")
    request: Optional[str] = Field(
        description="Optionally a well-formed string with a detailed request that includes: The primary goal or objective, the requirements necessary for task completion and any constraints such as time, budget, or resources."
    )
    search: Optional[str] = Field(
        description="Optionally a search query to retrieve information from a database that contains user info and the result of previous requests."
    )


class User:
    """Your classical chatbot! But it can send requests to the system"""

    def __init__(self):
        # TODO: Fetch User database or start questionnaire if he is not in the database.
        user_name = "Luis"  # Temporal until we can gather info from database.
        self.chat = Chat(
            "user", system_prompt_kwargs={"user_name": user_name}, containers=[Response]
        )
        self.requests: Dict[str, Request] = {}

    # Is this the right way? I need to initialize user before initializing process to send it as callable.
    def store_request_command(self, send_request: Callable):
        self.send_request = (
            send_request  # Callable method to communicate using network protocol
        )

    def run(self) -> Tuple[str, Optional[str]]:
        print("\n")
        prompt = input(colored("User: ", "blue"))
        # TODO: Algorithm to get relevant requests (based on IN_PROGRESS or WAITING_FEEDBACK)
        # TODO: Add here the status based on request status.
        user_prompt_kwargs = {"prompt": prompt}

        response = self.chat.get_response(prompt_kwargs=user_prompt_kwargs)[
            0
        ]  # Only one response
        print(colored(f"Assistant: {response.response}", "red"))
        request = response.request  # Getting only first
        if request:
            new_request = Request(request=request)
            self.send_request(new_request)
            self.update_request(new_request)
            print(colored(f"Request: {request}", "yellow"))
        search = response.search
        if search:
            # TODO: Temporal until we can gather info from database.
            fake_data = input(
                f"Search: {search}, please add the info for testing until the database is implemented: "
            )
            self.chat.conversation.messages[
                -1
            ] += f"\nSearch returned: {fake_data}"  # TODO: Implement this properly!!

    def update_request(self, request: Request):
        self.requests[request._id] = request


def main():
    user = User()
    user_process = Process(
        input_port=8887,
        output_port=8888,
        run_command=user.run,
        receive_message=user.update_request,
    )
    user.store_request_command(user_process.send_message)
    user_process.run()


if __name__ == "__main__":
    main()
