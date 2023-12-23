from typing import Callable, List, Optional
from openai.types.chat import ChatCompletionMessageToolCall

from democratic_agent.architecture.helpers import Request, Step
from democratic_agent.architecture.system.planner.plan import Plan, PlanStatus
from democratic_agent.chat.chat import Chat
from democratic_agent.tools.tools_manager import ToolsManager
from democratic_agent.utils.helpers import colored


MAX_ITERATIONS = 10  # TODO: Move to config.


# TODO: Decide if we should split plan and execution or use execute tools to send the full execution from here.
# Will require higher memory but will avoid sending info between different modules.
class Planner:
    """Planner module that will generate the steps to solve the problem."""

    def __init__(self, request: Request, get_user_feedback: Callable):
        self.chat = Chat(
            "planner",
            system_prompt_kwargs={"request": request.request},
            containers=[],
        )
        self.tool_manager = ToolsManager()
        self.planner_functions = [
            self.find_tools,
            self.execute_tools,
            self.search_info_on_database,
            self.communicate_with_user,
            self.set_task_completed,
        ]
        self.get_user_feedback = get_user_feedback
        self.request = request
        self.new_plan = None

    def get_response(
        self, feedback: Optional[str]
    ) -> List[ChatCompletionMessageToolCall]:
        print(
            colored("\n--- Planner ---\n", "cyan")
        )  # TODO: Make this part of logger with different colors depending on the running module of chat..
        planner_prompt_kwargs = {
            "feedback": feedback,
        }
        return self.chat.get_response(
            prompt_kwargs=planner_prompt_kwargs, functions=self.planner_functions
        )

    def plan(self, previous_step: Optional[Step] = None) -> Plan:
        # TODO:
        # 1. Based on Request search prepares queries for:
        # 1.  Relevant data: general queries for content related to the request
        # 2.  Past outcomes: previous similar requests.
        # 3.  User preferences.
        # 2. Summarize info preparing a "Context" that grounds the request on "data", "user preferences" and "previous experiences".
        # TODO: Add here step + context
        iterations = 0

        feedback = ""
        if previous_step:
            feedback = previous_step.get_feedback()

        # TODO: Send iterations to the prompt? This can be seen as a "frustration" metric that maybe helps the model to take more risks.
        while iterations < MAX_ITERATIONS:
            tools_call = self.get_response(feedback=feedback)
            feedback = None
            try:
                if tools_call is not None:
                    # The feedback is included inside of execute_tools!
                    self.tool_manager.execute_tools(
                        chat=self.chat,
                        tools_call=tools_call,
                        functions=self.planner_functions,
                    )

                    # Check if we have plan or task is completed.
                    if self.new_plan:
                        return self.new_plan
            except Exception as e:
                print(f"Error executing tools: {e}")
            iterations += 1
        print(
            colored(
                "Max iterations reached... returning empty plan.",
                "red",
            )
        )
        return Plan(
            summary="Max iterations reached... returning empty plan.",
            status=PlanStatus.FAILURE,
        )

    def execute_tools(self, step_description: str, tools: List[str]):
        """
        Initiates a request for another module to use the specified tools to accomplish the step, as defined by the step description.
        Remember to add all the details needed to execute the tools at the step_description.

        Args:
            step_description (str): The description of the step that should be accomplished next.
            tools (List[str]): The name of the tools that should be used to accomplish the step.

        Returns:
            str: The description of the step that should be accomplished next.
            str: The name of the tool that will be executed.
        """
        try:
            # Verify tools exist
            for tool_name in tools:
                self.tool_manager.get_tool(tool_name)
        except Exception:
            return f"Tool: {tool_name} doesn't exists. Please choose a tool that is available."

        self.save_plan(
            summary=step_description, status=PlanStatus.IN_PROGRESS, tools=tools
        )

        return f"Executing tool: {tool_name} to accomplish step: {step_description}"

    def find_tools(self, potential_approach: str, descriptions: List[str]):
        """
        Description of hypothetical tools that could be used to solve the current step.

        Args:
            potential_approach (str): The potential approach that could be used to solve the current step.
            descriptions (List[str]): The descriptions of the tools that could be used.

        Returns:
            callable: The tool that was created.
        """
        # TODO: Find on database tools that could be used to solve the current step.
        available_tools = self.tool_manager.fetch_tools(descriptions)
        print(f"Available tools: {available_tools}\n")

        return f"Found available tools: {available_tools}"

    def search_info_on_database(self, info: str):
        """
        Search for information on the database.

        Args:
            info (str): The information to be searched on the database.

        Returns:
            str: The information that was searched on the database.
        """
        # TODO: Search on database.

        info = input(
            f"Fake searching for {info} on database, please add the info manually: "
        )
        return info

    def communicate_with_user(self, message: str):
        """
        Communicate with the user.

        Args:
            message (str): The message to be sent to the user.

        Returns:
            callable: The tool that was created.
        """
        # Send message
        print(
            colored("System requires feedback", "red")
            + f"Sending message: {message} to user. Waiting for answer."
        )

        self.request.update_feedback(feedback=message)
        response = self.get_user_feedback(self.request)
        return f"User response: {response}"

    def save_plan(self, summary: str, status: PlanStatus, tools: List[str] = []):
        """
        Save a plan.
        """
        self.new_plan = Plan(summary=summary, status=status, tools=tools)

    def set_task_completed(self, summary: str):
        """
        Set the task as completed.

        Args:
            summary (str): The summary of the task.

        Returns:
            str: The summary of the task.
        """
        self.save_plan(summary=summary, status=PlanStatus.SUCCESS)

        return summary
