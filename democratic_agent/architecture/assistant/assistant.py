import json
import logging
from typing import Dict
from time import sleep
from queue import Queue

from democratic_agent.architecture.helpers.tmp_ips import (
    DEF_ASSISTANT_IP,
    DEF_PUB_PORT,
    DEF_SUB_PORT,
    DEF_REGISTRATION_PORT,
)  # TODO: REMOVE AND GET THIS DYNAMICALLY
from democratic_agent.architecture.helpers.topics import (
    DEF_ASSISTANT_MESSAGE,
    DEF_USER_MESSAGE,
)
from democratic_agent.architecture.helpers.request import Request, RequestStatus
from democratic_agent.architecture.user.user_message import UserMessage
from democratic_agent.chat.chat import Chat
from democratic_agent.tools.tools_manager import ToolsManager
from democratic_agent.utils.helpers import colored
from democratic_agent.utils.communication_protocols import (
    Proxy,
    Publisher,
    Subscriber,
    Server,
    ActionClient,
)

LOG = logging.getLogger(__name__)


# TODO: Centralize conversation! All users should be able to see the conversation.
class Assistant:
    """Your classical chatbot! But it can send requests to the system"""

    def __init__(self, assistant_ip: str, registration_port: int):
        self.requests: Dict[str, Request] = {}
        # Ideally requests should be stored on a real-time database?
        self.chat = Chat("user", system_prompt_kwargs={"requests": self.get_requests()})

        self.users: Dict[str, str] = {}
        self.user_messages: Queue[UserMessage] = Queue()

        # Communication - Assistant on any computer, USER and SYSTEM on the same computer!!
        self.proxy = Proxy(xsub_port=DEF_SUB_PORT, xpub_port=DEF_PUB_PORT)

        self.assistant_message_publisher = Publisher(
            address=f"tcp://{assistant_ip}:{DEF_SUB_PORT}",
            topic=DEF_ASSISTANT_MESSAGE,
        )  # TODO: Should we add port here?
        self.users_message_subscriber = Subscriber(
            address=f"tcp://{assistant_ip}:{DEF_PUB_PORT}",
            topic=DEF_USER_MESSAGE,
            callback=self.user_message_callback,
        )

        # Server to handle user registration
        self.registration_server = Server(
            f"tcp://{assistant_ip}:{registration_port}", self.handle_registration
        )

        # Action client for each user system.
        self.system_action_clients: Dict[str, ActionClient] = {}

        self.assistant_functions = [
            self.communicate_with_users,
            self.send_request,
            self.search_user_info,
            self.store_user_info,
            self.wait_for_user,
        ]
        self.tools_manager = ToolsManager()

    def handle_registration(self, message):
        """Register user creating a new action client connected to user's system"""

        user_info = json.loads(message)
        self.system_action_clients[user_info["user_name"]] = ActionClient(
            server_address=f"tcp://{user_info['system_ip']}:{user_info['system_port']}",
            callback=self.update_request,
            action_class=Request,
        )
        print(f"Registered user: {user_info['user_name']}")
        return "Registered Successfully"

    def get_requests(self):
        request_str = "\n".join([str(value) for value in self.requests.values()])
        # self.requests = {}  # Resetting requests TODO: Decide when to reset requests.
        return request_str

    def broadcast_message(self, message: str):
        self.assistant_message_publisher.publish(message)

    def user_message_callback(self, user_message: str):
        # Save user message in a queue.
        message = UserMessage.from_json(user_message)
        print(f"User {message.user_name} message: {message.message}")
        self.user_messages.put(message)

        # Broadcast to all users
        self.broadcast_message(user_message)

    def update_system(self):
        self.chat.edit_system_message(
            system_prompt_kwargs={"requests": self.get_requests()}
        )

    def send_request(self, user_name: str, request: str):
        """
        Send a request to the system, make a very explicit request.

        Args:
            request (str): The request the system needs to solve.

        Returns:
            None
        """

        new_request = Request(request=request)
        self.system_action_clients[user_name].send_goal(new_request)
        self.update_request(new_request)
        print(colored(f"Request: {request}", "yellow"))
        return "Request sent."

    # NOT USED FOR NOW TO HAVE A GROUP COMMUNICATION - FOR NOW JUST BROADCASTING
    # def send_message_to_user(self, user_name: str, message: str):
    #     self.users[user_name].send_message(message)

    def communicate_with_users(self, message: str):
        """
        Communicate with the users.

        Args:
            message (str): The message to be sent.

        Returns:
            str
        """
        print(f'{colored("Assistant:", "red")} {message}')
        assistant_message = UserMessage(user_name="Aware", message=message)
        self.broadcast_message(assistant_message.to_json())
        return "Message sent."

    def search_user_info(self, user_name: str, query: str):
        """
        Search the query on user's semantic database.

        Args:
            user_name (str): The user name to be searched.
            query (str): The search query.

        Returns:
            str
        """

        # TODO: Search on database!!
        # self.database.search_user_info(user_name, query)
        data = input(
            f"Query: {query}, please add the info for testing until the database is implemented: "
        )
        return f"\nSearch returned: {data}"

    def store_user_info(self, user_name: str, info: str):
        """
        Store the info on user's semantic database.

        Args:
            user_name (str): The user name.
            info (str): The info to be stored.

        Returns:
            str
        """
        # self.database.store_user_info(user_name, info)
        print(f"Storing {user_name}'s info: {info}")
        return "Info stored."

    def wait_for_user(self):
        """
        Wait for user's input, use this function to stop execution until a new message is received.

        Args:
            None
        """
        print("Waiting for user's input...")
        self.running = False
        return "Waiting for user's input..."

    def update_request(self, request: Request):
        self.requests[request.get_id()] = request
        feedback = request.get_feedback()
        if request.get_status() == RequestStatus.WAITING_USER_FEEDBACK:
            # Ask for feedback
            print(
                f'{colored("Assistant request:", "red")} {request.request} requires feedback: {feedback}'
            )
            self.chat.conversation.add_assistant_message(
                f"Request: {request.request} requires feedback: {feedback}"
            )
            self.communicate_with_users(
                f"Request: {request.request} requires feedback: {feedback}"
            )

            # Wait for feedback TODO: FIX ME.
            self.wait_user_message()

            # Send feedback
            user_message = self.user_messages.get()
            self.chat.conversation.add_user_message(
                message=user_message.message, user_name=user_message.user_name
            )
            self.user_messages.task_done()
            request.update_status(
                status=RequestStatus.IN_PROGRESS, feedback=user_message.message
            )
            self.send_request(request)
        self.update_system()

    def run(self):
        while True:
            while self.user_messages.empty():
                sleep(0.1)

            while not self.user_messages.empty():
                # Add user message to the chat
                user_message = self.user_messages.get()
                self.chat.conversation.add_user_message(
                    message=user_message.message, user_name=user_message.user_name
                )
                self.user_messages.task_done()

            self.running = True
            while self.running:
                tools_call = self.chat.call(functions=self.assistant_functions)
                if tools_call is None or not tools_call:
                    self.running = False
                    print("Stopping assistant due to None call.")
                elif isinstance(tools_call, str):
                    self.communicate_with_users(tools_call)
                    self.running = False
                else:
                    self.tools_manager.execute_tools(
                        chat=self.chat,
                        tools_call=tools_call,
                        functions=self.assistant_functions,
                    )

    def wait_user_message(self):
        while self.user_messages == []:
            sleep(0.1)


def main():
    assistant = Assistant(
        assistant_ip=DEF_ASSISTANT_IP,
        registration_port=DEF_REGISTRATION_PORT,
    )
    assistant.run()


if __name__ == "__main__":
    main()
