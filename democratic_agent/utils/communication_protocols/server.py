import zmq
import threading


class Server:
    def __init__(self, address, callback):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(address)
        self.callback = callback
        self.listener_thread = threading.Thread(target=self.listen, daemon=True)
        self.listener_thread.start()

    def listen(self):
        while True:
            message = self.socket.recv_string()
            response = self.callback(message)
            self.socket.send_string(response)

    def close(self):
        self.socket.close()
        self.context.term()
