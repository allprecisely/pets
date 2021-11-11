import os
import socket
import time

PORT = int(os.getenv("MULTIPLAYER_PORT", 8765))
HOST = os.getenv("MULTIPLAYER_HOST", "")


def get_socket():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


class Client:
    def __init__(self, ip_address):
        self.sock = socket.socket()
        self.ip_address = ip_address
        self.error_text = (
            "Соединение не установлено, " "т.к. порт не существует или проблема с сетью"
        )
        self.connected = False
        self.connect_text = "Ожидание подключения к серверу..."
        self.data = None
        self.try_another_server = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self, timeout=5):
        start_connection = time.time()
        port = PORT
        while time.time() - start_connection < timeout:
            try:
                self.sock.connect((self.ip_address, port))
                self.connected = True
                return
            except:
                port += 1
                time.sleep(1)
        self.try_another_server = True

    def get_data(self):
        try:
            response = self.sock.recv(1024)
            self.data = response.decode("utf8")
        except:
            self.connected = False

    def send_data(self, data):
        try:
            self.sock.send(data.encode("utf8"))
        except:
            self.connected = False

    def close(self):
        if not self.sock._closed:
            self.sock.close()


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
        self.sock.listen(1)
        self.conn = None
        self.error_text = "Время ожидания истекло"
        self.connect_text = (
            f"Ожидание подключения второго игрока по ip {self.ip_address}"
        )
        self.connected = False
        self.data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        self.conn, addr = self.sock.accept()
        self.connected = True
        print(f"connected by: {addr}")

    def get_data(self):
        response = self.conn.recv(1024)
        self.data = response.decode("utf8")

    def send_data(self, data):
        self.conn.send(data.encode("utf8"))

    def close(self):
        if self.conn and not self.conn._closed:
            self.conn.close()
        if not self.sock._closed:
            self.sock.close()
