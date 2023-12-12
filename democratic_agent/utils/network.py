import pickle
import socket
import select
import threading
from typing import Callable, Optional


class NetworkProtocol:
    def __init__(self, port: int, url: str = "localhost"):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((url, port))
        self.sock.listen(5)
        self.url = url

    def receive(self) -> str:
        client_socket, _ = self.sock.accept()
        data = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            data += chunk
        request = pickle.loads(data)
        return request

    def send(self, request: str, port: int):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.url, port))
        data = pickle.dumps(request)
        client_socket.sendall(data)

    def available(self) -> bool:
        """
        Checks if any data is available to be received.
        Returns True if data is available, False otherwise.class MessageListenerThread(threading.Thread):
        """
        ready_to_read, _, _ = select.select([self.sock], [], [], 0)
        return len(ready_to_read) > 0

    def stop(self):
        self.sock.close()


class MessageListenerThread(threading.Thread):
    def __init__(
        self,
        network_protocol: NetworkProtocol,
        received_callback: Optional[Callable] = None,
    ):
        super().__init__()
        self.network_protocol = network_protocol
        self.running = True
        self.received_callback = received_callback

    def run(self):
        while self.running:
            rlist, _, _ = select.select([self.network_protocol.sock], [], [], 1)
            if self.network_protocol.sock in rlist:
                message = self.network_protocol.receive()
                if self.received_callback:
                    self.received_callback(message)

    def stop(self):
        self.running = False
