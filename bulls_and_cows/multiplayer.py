import logging
import os
import pathlib
import socket
import threading
import time

logger = logging.getLogger(__name__)
PORT = int(os.getenv("MULTIPLAYER_PORT", 8765))
HOST = os.getenv("MULTIPLAYER_HOST", "")


def get_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


class Client:
    def __init__(self, ip_address):
        self.sock = socket.socket()
        self.port = PORT
        local_game = pathlib.Path('current_port.txt')
        if local_game.exists():
            self.port = local_game.read_text()
        self.ip_address = ip_address
        self.error_text = (
            "Connection refused as host doesn't exist"
            " or there are problems with connection"
        )
        self.sent = self.received = False
        self.connected = False
        self.connect_text = "Waiting for connection..."
        self.data = None
        self.try_another_server = False
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self, timeout=5):
        self.closed = False
        start_connection = time.time()
        while time.time() - start_connection < timeout:
            try:
                self.sock.connect((self.ip_address, int(self.port)))
                logger.info('connected to %s:%s', self.ip_address, self.port)
                self.connected = True
                return
            except:
                self.port += 1
                time.sleep(1)
        self.try_another_server = True

    def get_data(self):
        self.received = False
        try:
            response = self.sock.recv(1024)
            self.data = response.decode("utf8")
            self.received = True
        except:
            self.connected = False

    def send_data(self, data):
        self.sent = False
        try:
            self.sock.send(data.encode("utf8"))
            self.sent = True
        except:
            self.connected = False

    def close(self):
        if not self.sock._closed:
            self.sock.close()
        self.closed = True


class Server:
    def __init__(self):
        self.ip_address = get_socket()
        self.sock = socket.socket()
        self.port = PORT
        while True:
            try:
                self.sock.bind((self.ip_address, self.port))
                break
            except:
                self.port += 1
                print(f"new port: {self.port}")
        local_game = pathlib.Path('current_port.txt')
        if local_game.exists():
            local_game.write_text(str(self.port))
        self.sock.listen(1)
        self.conn = None
        self.error_text = "The time of connection has reached out"
        self.connect_text = (
            f"Waiting other player via ip {self.ip_address}"
        )
        self.connected = False
        self.data = None
        self.closed = False
        self.sent = self.received = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        self.closed = False
        try:
            self.conn, addr = self.sock.accept()
            self.connected = True
            logger.info("connected by: %s", addr)
        except ConnectionAbortedError:
            logger.info('User has stopped to wait')

    def get_data(self):
        self.received = False
        try:
            response = self.conn.recv(1024)
            self.data = response.decode("utf8")
            self.received = True
        except:
            self.connected = False

    def send_data(self, data):
        self.sent = False
        try:
            self.conn.send(data.encode("utf8"))
            self.sent = True
        except:
            self.connected = False

    def close(self):
        if self.conn and not self.conn._closed:
            self.conn.close()
        if not self.sock._closed:
            self.sock.close()
        self.connected = False
        self.closed = True
