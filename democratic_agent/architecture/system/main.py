from democratic_agent.architecture.system.system import System
from democratic_agent.utils.network import NetworkProtocol, MessageListenerThread


class SystemComm:
    def __init__(self):
        # TODO: Move to cfg
        self.user_port = 8887
        self.system_port = 8888

        self.network_protocol = NetworkProtocol(
            port=self.system_port
        )  # using localhost, improve this when moving to production.
        self.system = System(send_feedback)

    def print_received_message(self, message):
        print(f"\nReceived message from executive_director: {message}\n")

    def run(self):
        self.running = True
        listener_thread = MessageListenerThread(
            self.network_protocol, self.print_received_message
        )
        listener_thread.start()

        while self.running:  # Add here Ctrl/c stop
            self.system.process_request()
        self.network_protocol.stop()

    def send_feedback(self, request: str):
        self.network_protocol.send(request, self.system_port)
        print()

    def stop(self):
        self.running = False


def main():
    user = UserComm()
    user.run()


if __name__ == "__main__":
    main()
