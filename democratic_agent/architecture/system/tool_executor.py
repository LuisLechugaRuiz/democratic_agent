import inspect
from logging import getLogger
from typing import Callable, List
import json

from democratic_agent.chat.chat import Chat
from democratic_agent.architecture.helpers.tool import Tool
from democratic_agent.utils.helpers import colored

# TODO: Create our own logger.
LOG = getLogger(__name__)


class ToolExecutor:
    def __init__(self, request: str):
        self.chat = Chat("executor", system_prompt_kwargs={"request": request})

    def call(self, functions: List[Callable], step: str) -> List[Tool]:
        print(colored("\n--- Executor ---\n", "green"))
        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

        tools_call = self.chat.get_response(
            prompt_kwargs={"step": step},
            functions=functions,
        )

        tools_result: List[Tool] = []
        for tool_call in tools_call:
            try:
                function_name = tool_call.function.name
                function = functions_dict[function_name]
            except KeyError:
                raise Exception("Function name doesn't exist...")

            signature = inspect.signature(function)
            args = [param.name for param in signature.parameters.values()]

            arguments = json.loads(tool_call.function.arguments)
            call_arguments_dict = {}
            for arg in args:
                arg_value = arguments.get(arg, None)
                if not arg_value:
                    raise Exception(
                        f"Function {function_name} requires argument {arg} but it is not provided."
                    )
                call_arguments_dict[arg] = arg_value
            try:
                response = function(**call_arguments_dict)
                args_string = ", ".join(
                    [f"{key}={value!r}" for key, value in call_arguments_dict.items()]
                )
                print(f"{function.__name__}({args_string}): {response}")
            except Exception as e:
                raise Exception(
                    f"Error while executing function {function_name} with arguments {call_arguments_dict}. Error: {e}"
                )
            self.chat.add_tool_feedback(id=tool_call.id, message=response)
            tools_result.append(Tool(name=function_name, feedback=response))
        return tools_result
