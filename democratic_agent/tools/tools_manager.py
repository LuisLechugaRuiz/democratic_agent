import json
import importlib
import inspect
from logging import getLogger
from pathlib import Path
import os
from typing import Callable, List
from openai.types.chat import ChatCompletionMessageToolCall

from democratic_agent.architecture.helpers.tool import Tool
from democratic_agent.chat.chat import Chat

# TODO: Create our own logger.
LOG = getLogger(__name__)


# TODO: Move tools to a inner folder.
class ToolsManager:
    def __init__(self):
        self.module_path = "democratic_agent.tools.tools"
        self.tools_folder = Path(__file__).parent / "tools"
        self.default_tools = []
        # Here we should retrieve the embedded tools, create it based on the folder or retrieve from db? - we need a SSoT.
        # Ideally the data retrieved after executing tool should be send online to our database (after filtering), for future fine-tuning, so we can improve the models and provide them back to the community.

    def fetch_tools(self, potential_tools: List[str]) -> List[Callable]:
        """TODO: Fetch from database the tools that are similar to the step."""

        tools = self.default_tools.copy()

        # Dummy for now, but should search for the tool by similarity step - tools description.
        retrieved_tools = [
            "send_whatsapp_message"
        ]  # TODO: REMOVE ME!! Only for testing for now.
        tools.extend(retrieved_tools)
        return tools

    # TODO: Log here that the function already exists. Should not append as affordance should verify this.
    def save_tool(self, function, name):
        path = os.path.join(self.tools_folder / f"{name}.py")
        with open(path, "w") as f:
            f.write(function)
            self.default_tools.append(
                name
            )  # TODO: REMOVE ME!! This is only to test newly created tools until we implement the DB.

    def get_tool(self, name: str) -> Callable:
        # Dynamically import the module
        module = importlib.import_module(f"{self.module_path}.{name}")

        # Retrieve the function with the same name as the module
        tool_function = getattr(module, name, None)

        if tool_function is None:
            raise AttributeError(f"No function named '{name}' found in module '{name}'")

        return tool_function

    def execute_tools(
        self,
        chat: Chat,
        tools_call: List[ChatCompletionMessageToolCall],
        functions: List[Callable],
    ) -> List[Tool]:
        functions_dict = {}
        for function in functions:
            functions_dict[function.__name__] = function

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
            chat.add_tool_feedback(id=tool_call.id, message=response)
            tools_result.append(Tool(name=function_name, feedback=response))
        return tools_result
