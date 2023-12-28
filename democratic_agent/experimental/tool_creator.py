from logging import getLogger

from democratic_agent.chat.chat import Chat
from democratic_agent.utils.helpers import colored

# TODO: Create our own logger.
LOG = getLogger(__name__)


# TODO: ADAPT TO NEW ARCHITECTURE
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

    def create_tool(self, name: str, description: str):
        """
        Creates a new tool, make it general to be usable with different arguments. i.e: search_on_google instead of search_for_specific_info
        Use this only in case no other function can satisfy the request.

        Args:
            name (str): The name of the tool, should match the expected function name. i.e: search_on_google
            description (str): A description used to create the tool, should include all the details.

        Returns:
            callable: The tool that was created.
        """
        return name, description
        # Implement here FuncSearch -> https://github.com/google-deepmind/funsearch adapted to our case -> Evaluator is a LLM evaluating criterias depending on the feedback received from using the tool.
        new_function = self.tool_creator.call(tool_name, tool_description)
        self.tools_manager.save_tool(new_function, tool_name)

        approved = True  # It will be False, but setting to True as test is not implemented yet.
        while not approved:
            pass
            # self.tool_manager.test_tool(tool_name)
