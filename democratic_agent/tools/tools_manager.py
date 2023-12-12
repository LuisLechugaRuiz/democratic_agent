import importlib
from logging import getLogger
from pathlib import Path
import os
from typing import Callable, List

# TODO: Create our own logger.
LOG = getLogger(__name__)


# TODO: Move tools to a inner folder.
class ToolManager:
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
