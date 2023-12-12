from typing import Callable
from queue import Queue

from democratic_agent.architecture.helpers import Request, RequestStatus, Step
from democratic_agent.architecture.system.planner import Planner, PlanStatus
from democratic_agent.architecture.system.tool_creator import ToolCreator
from democratic_agent.architecture.system.tool_executor import (
    ToolExecutor,
)
from democratic_agent.tools.tools_manager import ToolManager
from democratic_agent.utils.process import Process


class System:
    """Router for the system, completing the request from the user."""

    def __init__(self):
        self.tool_creator = ToolCreator()  # TODO: Next version.

        self.tool_manager = ToolManager()
        self.requests: Queue[Request] = Queue()

    def add_request(self, request: Request):
        self.requests.put(request)

    # Implement here FuncSearch -> https://github.com/google-deepmind/funsearch adapted to our case -> Evaluator is a LLM evaluating criterias depending on the feedback received from using the tool.
    def create_tool(self, tool_name: str, tool_description: str, step: str):
        # Test the tool - decide how to create the tests to verify the tool.
        # self.tool_creator.create_test

        new_function = self.tool_creator.call(tool_name, tool_description)
        self.tool_manager.save_tool(new_function, tool_name)

        approved = True  # It will be False, but setting to True as test is not implemented yet.
        while not approved:
            pass
            # self.tool_manager.test_tool(tool_name)

    def run(self):
        while not self.requests.empty():
            request = self.requests.get()
            request.update_status(
                RequestStatus.IN_PROGRESS, feedback="Starting to plan."
            )

            # Start other modules with empty conversation and add request to system message.
            planner = Planner(request)
            tool_executor = ToolExecutor(request)

            step = None
            finished = False
            while not finished:  # TODO: Add max number of iterations.
                plan = planner.plan(previous_step=step)
                status = plan.get_status()
                if status == PlanStatus.FAILURE:
                    # We need to notify to user OR create our own tool (On next version!!).
                    request.update_status(
                        status=RequestStatus.FAILURE,
                        feedback="Couldn't find a tool to execute.",
                    )
                    self.update_request(request)
                    finished = True
                elif status == PlanStatus.SUCCESS:
                    request.update_status(
                        status=RequestStatus.SUCCESS, feedback=plan.summary
                    )
                    self.update_request(request)
                    finished = True
                else:
                    request.update_status(
                        status=RequestStatus.IN_PROGRESS, feedback=plan.summary
                    )
                    step = Step(step=plan.step, tools=plan.selected_tools)
                    functions = []
                    for tool in step.tools:
                        functions.append(self.tool_manager.get_tool(tool.name))

                    # Update the tools based on the execution and the feedback.
                    step.tools = tool_executor.call(functions, step=step.step)
        return self.requests

    def store_update_request_command(self, update_request: Callable):
        self.update_request = update_request


def main():
    system = System()
    system_process = Process(
        input_port=8888,
        output_port=8887,
        run_command=system.run,
        receive_message=system.add_request,
    )
    system.store_update_request_command(system_process.send_message)
    system_process.run()

    # TODO: Create proper tests to benchmark every part of the system.
    # def tests():
    # system = System()
    # test_0 = "Find who is the currenlty the richest person in the world, today is (2023-12-14)."  # Send date as part of the prompt?
    # test_1 = "Get Tesla historical stocks from 2023-01-01 to 2023-12-14."
    # test_2 = "Tell me the PIB of Spain in 2023."
    # tests = [test_0, test_1, test_2]
    # for test in tests:
    #    print(f"--- Test: {test} ---")
    # feedback = system.process_request(test) -> Will be used after adding reasoner!
    #    feedback = system.execute_tools(test)
    #    print(feedback)
    # pass


if __name__ == "__main__":
    main()
