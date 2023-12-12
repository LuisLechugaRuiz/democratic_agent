from typing import List, Optional

from democratic_agent.architecture.system.planner.plan import Plan, PlanStatus
from democratic_agent.architecture.helpers.step import Step
from democratic_agent.chat.chat import Chat
from democratic_agent.tools.tools_manager import ToolManager
from democratic_agent.utils.helpers import colored


MAX_ITERATIONS = 3  # TODO: Move to config.


class Planner:
    """Planner module that will generate the steps to solve the problem."""

    def __init__(self, request: str):
        self.chat = Chat(
            "planner",
            system_prompt_kwargs={"request": request},
            containers=[Plan],
        )
        self.tool_manager = ToolManager()

    def call(self, step: Optional[Step], available_tools: List[str]) -> Plan:
        print(
            colored("\n--- Planner ---\n", "cyan")
        )  # TODO: Make this part of logger with different colors depending on the running module of chat..f
        feedback = ""
        if step:
            feedback = step.get_feedback()
        planner_prompt_kwargs = {
            "feedback": feedback,
            "available_tools": available_tools,
        }
        response = self.chat.get_response(planner_prompt_kwargs)
        plan = response[0]
        print(plan)
        return plan

    def plan(self, previous_step: Optional[Step] = None) -> Plan:
        # TODO:
        # 1. Based on Request search prepares queries for:
        # 1.  Relevant data: general queries for content related to the request
        # 2.  Past outcomes: previous similar requests.
        # 3.  User preferences.
        # 2. Summarize info preparing a "Context" that grounds the request on "data", "user preferences" and "previous experiences".
        # TODO: Add here step + context

        available_tools = ["Please search for potential tools first."]
        iterations = 0
        # TODO: Send iterations to the prompt? This can be seen as a "frustration" metric that maybe helps the model to take more risks.
        while iterations < MAX_ITERATIONS:
            plan = self.call(step=previous_step, available_tools=available_tools)

            if plan.task_completed:
                plan.update_status(PlanStatus.SUCCESS)
                return plan

            if plan.selected_tools:
                plan.update_status(PlanStatus.IN_PROGRESS)
                return plan

            available_tools = self.tool_manager.fetch_tools(plan.potential_tools)
            print(f"Available tools: {available_tools}")
            iterations += 1

        print(
            colored(
                "Max iterations reached... returning empty plan.",
                "red",
            )
        )
        plan.update_status(PlanStatus.FAILURE)
        return plan
