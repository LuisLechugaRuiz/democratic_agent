import json
import zmq
import threading
from typing import Callable, Dict
from queue import Queue

from democratic_agent.utils.communication_protocols.actions.goal_handle import (
    GoalHandle,
    GoalHandleStatus,
)
from democratic_agent.utils.communication_protocols.actions.action import Action


class ServerGoalHandle(GoalHandle):
    def __init__(
        self, goal_id, action: Action, status: GoalHandleStatus, send_feedback: Callable
    ):
        super().__init__(goal_id, action, status)
        self._send_feedback = send_feedback

    @staticmethod
    def from_json(json_str, action_class: Action, send_feedback: Callable):
        data = json.loads(json_str)
        action = action_class.from_json(data["action"])
        return ServerGoalHandle(
            data["goal_id"], action, GoalHandleStatus[data["status"]], send_feedback
        )

    def send_feedback(
        self,
    ):
        self._send_feedback(self)


class ActionServer:
    def __init__(
        self,
        server_address: str,
        callback: Callable,
        update_callback: Callable,
        action_class: Action,
    ):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.bind(server_address)

        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

        self.active_goals: Dict[str, GoalHandle] = {}
        self.action_class = action_class
        self.callback = callback
        self.update_callback = update_callback

        # Use a queue to store incoming goals
        self.goal_queue: Queue[GoalHandle] = Queue()

        # Start a thread to listen for goals
        self.goal_listener_thread = threading.Thread(
            target=self.listen_for_goals, daemon=True
        )
        self.goal_listener_thread.start()

        # Start a worker thread to process goals
        self.worker_thread = threading.Thread(target=self.process_goals, daemon=True)
        self.worker_thread.start()

    def listen_for_goals(self):
        while True:
            socks = dict(self.poller.poll())  # No timeout
            if socks.get(self.socket) == zmq.POLLIN:
                message = self.socket.recv_string()
                if message.startswith("update "):
                    # Extract the goal ID and update data
                    _, goal_handle_message = message.split(" ", 1)
                    goal_handle = ServerGoalHandle.from_json(
                        goal_handle_message, self.action_class, self.publish_feedback
                    )
                    # Check if this goal ID exists in active goals
                    if goal_handle.goal_id in self.active_goals:
                        self.update_goal(goal_handle)
                else:
                    # Handle new goal
                    goal_handle = ServerGoalHandle.from_json(
                        message, self.action_class, self.publish_feedback
                    )
                    self.goal_queue.put(goal_handle)
                    self.active_goals[goal_handle.goal_id] = goal_handle

    def process_goals(self):
        while True:
            goal_handle = self.goal_queue.get()
            self.callback(goal_handle)
            self.goal_queue.task_done()

            # Ensure that the goal is marked as completed
            if goal_handle.status not in [
                GoalHandleStatus.COMPLETED,
                GoalHandleStatus.ABORTED,
            ]:
                goal_handle.status = GoalHandleStatus.COMPLETED
            self.publish_feedback(goal_handle)

    def update_goal(self, updated_goal_handle: ServerGoalHandle):
        self.active_goals[updated_goal_handle.goal_id] = updated_goal_handle
        # Trigger the update callback
        if self.update_callback:
            self.update_callback(updated_goal_handle)

    def publish_feedback(self, update: ServerGoalHandle):
        self.socket.send_string(update.to_json())

    def close(self):
        self.socket.close()
        self.context.term()

    def __del__(self):
        self.close()
