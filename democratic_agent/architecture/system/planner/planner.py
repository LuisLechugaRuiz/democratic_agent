from typing import Callable, List, Optional
from openai.types.chat import ChatCompletionMessageToolCall

from democratic_agent.architecture.helpers import Request, Step
from democratic_agent.architecture.system.planner.plan import Plan, PlanStatus
from democratic_agent.chat.chat import Chat
from democratic_agent.tools.tools_manager import ToolsManager
from democratic_agent.utils.helpers import colored


MAX_ITERATIONS = 10  # TODO: Move to config.


# TODO: Set MAX short term memory size and MAX conversation size!(Important to calculate number of tokens).
class Planner:
    """Planner module that will generate the steps to solve the problem."""

    def __init__(self, get_user_feedback: Callable, user_name: str):
        self.chat = Chat(
            module_name="planner",
            system_prompt_kwargs={"request": ""},
            user_name=user_name,
        )
        self.tool_manager = ToolsManager()
        self.planner_functions = [
            self.find_tools,
            self.execute_tools,
            self.communicate_with_user,
            self.set_task_completed,
        ]
        self.get_user_feedback = get_user_feedback
        self.new_plan = None

    def get_response(
        self, feedback: Optional[str]
    ) -> List[ChatCompletionMessageToolCall]:
        print(
            colored("\n--- Planner ---\n", "cyan")
        )  # TODO: Make this part of logger with different colors depending on the running module of chat..
        if feedback:
            planner_prompt_kwargs = {
                "feedback": feedback,
            }
            return self.chat.get_response(
                prompt_kwargs=planner_prompt_kwargs, functions=self.planner_functions
            )
        return self.chat.call(
            functions=self.planner_functions,
        )

    def plan(self, previous_step: Optional[Step] = None) -> Plan:
        # TODO Verify our memory and remove this comments:

        # 1. Based on Request search prepares queries for:
        # 1.  Relevant data: general queries for content related to the request
        # 2.  Past outcomes: previous similar requests.
        # 3.  User preferences.
        # 2. Summarize info preparing a "Context" that grounds the request on "data", "user preferences" and "previous experiences".
        # TODO: Add here step + context
        iterations = 0

        # TODO: Remove when we include here tool executor as the feedback will be already included.
        feedback = ""
        if previous_step:
            feedback = previous_step.get_feedback()

        # TODO: Send iterations to the prompt? This can be seen as a "frustration" metric that maybe helps the model to take more risks.
        while iterations < MAX_ITERATIONS:
            tools_call = self.get_response(feedback=feedback)
            feedback = None
            try:
                if tools_call is not None:
                    if isinstance(tools_call, str):
                        print(f"Tools call is a string: {tools_call}")
                        feedback = "Please call a function, don't send a string"  # TODO: Send the message to user and get feedback?
                    else:
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

    def update_request(self, request: Request):
        self.request = request
        self.chat.edit_system_message(system_prompt_kwargs={"request": request.request})

    # TODO: What if we use the tool here instead??
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
        # TODO: Find on database tools that could be used to solve the current step - ADD ME!! SEARCH FOR POTENTIAL TOOLS IN DATABASE. REGISTER THEM AT A REGISTER.
        available_tools = self.tool_manager.fetch_tools(descriptions)
        print(f"Available tools: {available_tools}\n")

        return f"Found available tools: {available_tools}"

    def communicate_with_user(self, message: str):
        """
        Communicate with the user.

        Args:
            message (str): The message to be sent to the user.

        Returns:
            callable: The tool that was created.
        """
        # Send message
        print(colored("System requires feedback: ", "red") + message)

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
