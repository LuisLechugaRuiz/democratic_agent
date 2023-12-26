import argparse
from collections import OrderedDict
import json
from time import sleep

from democratic_agent.architecture.helpers import Request, RequestStatus, Step
from democratic_agent.architecture.system.planner import Planner, PlanStatus

# from democratic_agent.architecture.system.tool_creator import ToolCreator
from democratic_agent.architecture.system.tool_executor import (
    ToolExecutor,
)
from democratic_agent.tools.tools_manager import ToolsManager
from democratic_agent.utils.helpers import colored, get_local_ip
from democratic_agent.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_CLIENT_PORT,
    DEF_SYSTEM_PORT,
)
from democratic_agent.architecture.helpers.topics import DEF_REGISTRATION_SERVER
from democratic_agent.utils.communication_protocols import Client
from democratic_agent.utils.communication_protocols.actions.action_server import (
    ActionServer,
    ServerGoalHandle,
)


class System:
    """Router for the system, completing the request from the user."""

    def __init__(
        self,
        user_name: str,
        assistant_ip: str,
        system_port: int,
    ):
        self.system_ip = get_local_ip()

        # self.tool_creator = ToolCreator()  # TODO: Next version.
        self.user_name = user_name
        self.tools_manager = ToolsManager()
        self.requests: OrderedDict[str, Request] = OrderedDict()

        self.planner = Planner(
            get_user_feedback=self.get_user_feedback,
            user_name=user_name,
        )
        self.tool_executor = ToolExecutor(
            user_name=user_name,
        )
        # Communication - TODO: Centralize comms at assistant.
        self.system_action_server = ActionServer(
            server_address=f"tcp://{self.system_ip}:{system_port}",
            callback=self.execute_request,
            action_class=Request,
        )
        self.register_with_assistant(assistant_ip, system_port)

    def add_request(self, request: Request):
        # In case request already exists just update it.
        self.requests[request.get_id()] = request

    # Implement here FuncSearch -> https://github.com/google-deepmind/funsearch adapted to our case -> Evaluator is a LLM evaluating criterias depending on the feedback received from using the tool.
    def create_tool(self, tool_name: str, tool_description: str, step: str):
        # Test the tool - decide how to create the tests to verify the tool.
        # self.tool_creator.create_test

        new_function = self.tool_creator.call(tool_name, tool_description)
        self.tools_manager.save_tool(new_function, tool_name)

        approved = True  # It will be False, but setting to True as test is not implemented yet.
        while not approved:
            pass
            # self.tool_manager.test_tool(tool_name)

    def execute_request(self, server_goal_handle: ServerGoalHandle):
        self.current_goal_handle = server_goal_handle
        request: Request = server_goal_handle.action
        print(colored("\n--- Request ---\n", "yellow"))
        print(request)
        self.update_request(
            request,
            status=RequestStatus.IN_PROGRESS,
            feedback="Starting to plan.",
        )
        self.tool_executor.update_request(request)
        self.planner.update_request(request)

        step = None
        finished = False
        while not finished:  # TODO: Add max number of iterations.
            plan = self.planner.plan(previous_step=step)
            status = plan.get_status()
            if status == PlanStatus.FAILURE:
                # We need to notify to user OR create our own tool (On next version!!).
                self.update_request(
                    request,
                    status=RequestStatus.FAILURE,
                    feedback="Couldn't find a suitable tool for the request.",
                )
                finished = True
            elif status == PlanStatus.SUCCESS:
                self.update_request(
                    request, status=RequestStatus.SUCCESS, feedback=plan.summary
                )
                finished = True
            else:
                self.update_request(
                    request, status=RequestStatus.IN_PROGRESS, feedback=plan.summary
                )
                step = Step(step=plan.summary, tools=plan.tools)
                functions = []
                for tool in step.tools:
                    functions.append(self.tools_manager.get_tool(tool.name))

                # Update the tools based on the execution and the feedback.
                step.tools = self.tool_executor.call(functions, step=step.step)

    # TODO: FIX ME! NOT WORKING PROPERLY THE RECEPTION.
    def get_user_feedback(self, request: Request):
        # Update request status
        request.update_status(status=RequestStatus.WAITING_USER_FEEDBACK)
        self.requests[request.get_id()] = request

        # Send feedback to user
        self.current_goal_handle.action = request
        self.current_goal_handle.send_feedback()

        # Wait for feedback
        while (
            self.requests[request.get_id()].get_status()
            == RequestStatus.WAITING_USER_FEEDBACK
        ):
            sleep(1)
        # Update request
        request = self.requests[request.get_id()]
        return request.get_feedback()

    def update_request(self, request: Request, status: RequestStatus, feedback: str):
        request.update_status(status=status, feedback=feedback)
        self.requests[request.get_id()] = request
        self.current_goal_handle.action = request

        if status == RequestStatus.SUCCESS:
            self.current_goal_handle.set_completed()
        elif status == RequestStatus.FAILURE:
            self.current_goal_handle.set_aborted()
        self.current_goal_handle.send_feedback()

    # TODO: receive ack.
    def register_with_assistant(
        self,
        assistant_ip: str,
        system_port: int,
    ):
        print("REGISTERING WITH ASSISTANT")
        client = Client(f"tcp://{assistant_ip}:{DEF_CLIENT_PORT}")
        # TODO: Create class
        user_info = {
            "user_name": self.user_name,
            "system_ip": self.system_ip,
            "system_request_port": system_port,
        }
        client.send(
            topic=DEF_REGISTRATION_SERVER, message=json.dumps(user_info)
        )  # Send registration info to Assistant
        client.close()


def main():
    # TODO: Get USER FROM CONFIG!
    parser = argparse.ArgumentParser(description="User configuration script.")
    parser.add_argument("-n", "--name", default="Luis", help="User name")
    parser.add_argument(
        "-a",
        "--assistant_ip",
        type=str,
        default=DEF_ASSISTANT_IP,
        help="Assistant IP",
    )
    parser.add_argument(
        "-s", "--system_port", type=int, default=DEF_SYSTEM_PORT, help="System port"
    )
    args = parser.parse_args()

    # When user starts initialize his system.
    system = System(
        user_name=args.name,
        assistant_ip=args.assistant_ip,
        system_port=args.system_port,
    )
    while True:
        sleep(0.1)


if __name__ == "__main__":
    main()
