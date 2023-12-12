from logging import getLogger

from democratic_agent.chat.chat import Chat
from democratic_agent.utils.helpers import colored

# TODO: Create our own logger.
LOG = getLogger(__name__)


class ToolCreator:
    def __init__(self):
        self.regex_pattern = r"```python\n(.*?)```"  # TODO: Make this configurable? we can even code on other programming languages...

    def call(self, tool_name: str, tool_description: str):
        creator_prompt_kwargs = {"name": tool_name, "instruction": tool_description}
        function = Chat("tool_creator").get_response(
            prompt_kwargs=creator_prompt_kwargs,
            filter_pattern=self.regex_pattern,
            multiple_responses=False,
        )
        print(colored("--- ToolCreator ---", "yellow"))  # TODO: Custom log per class.
        print(function)
        return function
