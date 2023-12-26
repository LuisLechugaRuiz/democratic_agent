import uuid
import zmq
import threading
from typing import Callable, Dict

from democratic_agent.utils.communication_protocols.actions.goal_handle import (
    GoalHandle,
    GoalHandleStatus,
)
from democratic_agent.utils.communication_protocols.actions.action import Action


class ActionClient:
    def __init__(self, server_address: str, callback: Callable, action_class: Action):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.connect(server_address)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.active_goals: Dict[str, GoalHandle] = {}
        self.action_class = action_class
        self.callback = callback

        # Start feedback thread
        thread = threading.Thread(target=self.listen_for_feedback)
        thread.start()

    def send_goal(self, action):
        goal_id = str(uuid.uuid4())
        goal_handle = GoalHandle(goal_id, action)
        self.active_goals[goal_id] = goal_handle

        # Send the goal
        self.socket.send_string(goal_handle.to_json())

        return goal_handle

    def listen_for_feedback(self):
        while True:
            socks = dict(self.poller.poll(timeout=1000))  # Timeout in milliseconds
            if socks.get(self.socket) == zmq.POLLIN:
                message = self.socket.recv_string()
                update = GoalHandle.from_json(message, self.action_class)
                if update.goal_id in self.active_goals:
                    self.callback(update.action)
                    if update.status in [
                        GoalHandleStatus.COMPLETED,
                        GoalHandleStatus.ABORTED,
                    ]:
                        del self.active_goals[update.goal_id]

    def close(self):
        # Close sockets and context
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
