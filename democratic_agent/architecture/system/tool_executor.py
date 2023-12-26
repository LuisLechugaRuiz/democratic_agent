from logging import getLogger
from typing import Callable, List

from democratic_agent.architecture.helpers.request import Request
from democratic_agent.chat.chat import Chat
from democratic_agent.architecture.helpers.tool import Tool
from democratic_agent.tools.tools_manager import ToolsManager
from democratic_agent.utils.helpers import colored

# TODO: Create our own logger.
LOG = getLogger(__name__)

DEF_MAX_ITERATIONS = 3


# TODO: Merge tool executor with planner, as it now can handle his memory we just give him the new tool.
class ToolExecutor:
    def __init__(self, user_name: str):
        self.chat = Chat(
            "executor",
            system_prompt_kwargs={"request": ""},
            user_name=user_name,
            register_database=False,
        )
        self.tools_manager = ToolsManager()

    def call(self, functions: List[Callable], step: str) -> List[Tool]:
        print(colored("\n--- Executor ---\n", "green"))

        tools_call = self.chat.get_response(
            prompt_kwargs={"step": step},
            functions=functions,
        )
        if isinstance(tools_call, str):
            return Tool(name="None", feedback=tools_call)

        tools_result = self.tools_manager.execute_tools(
            chat=self.chat, tools_call=tools_call, functions=functions
        )
        return tools_result

    def update_request(self, request: Request):
        self.chat.edit_system_message(system_prompt_kwargs={"request": request.request})
