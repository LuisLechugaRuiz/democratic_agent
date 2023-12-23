import inspect
from logging import getLogger
from typing import Callable, List
import json

from democratic_agent.chat.chat import Chat
from democratic_agent.architecture.helpers.tool import Tool
from democratic_agent.tools.tools_manager import ToolsManager
from democratic_agent.utils.helpers import colored

# TODO: Create our own logger.
LOG = getLogger(__name__)

DEF_MAX_ITERATIONS = 3


class ToolExecutor:
    def __init__(self, request: str):
        self.chat = Chat("executor", system_prompt_kwargs={"request": request})
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
