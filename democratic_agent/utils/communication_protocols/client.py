import zmq


class Client:
    def __init__(self, address):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(address)

    def send(self, message):
        self.socket.send_string(message)
        return self.socket.recv_string()

    def close(self):
        self.socket.close()
        self.context.term()
