from typing import Callable

from democratic_agent.utils.network import NetworkProtocol, MessageListenerThread


class Process:
    def __init__(
        self,
        input_port: int,
        output_port: int,
        run_command: Callable,
        receive_message: Callable,
    ):
        # TODO: Move to cfg
        self.input_port = input_port  # 8887
        self.output_port = output_port  # 8888

        self.network_protocol = NetworkProtocol(
            port=self.input_port
        )  # using localhost, improve this when moving to production.
        self.listener_thread = MessageListenerThread(
            self.network_protocol, receive_message
        )
        self.run_command = run_command

    def run(self):
        self.running = True

        self.listener_thread.start()

        try:
            while self.running:  # Add here Ctrl/c stop
                self.run_command()
        except KeyboardInterrupt:
            print("Stopping process...")
            self.network_protocol.stop()
            exit(0)

    def send_message(self, message):
        self.network_protocol.send(message, self.output_port)

    def stop(self):
        self.running = False
