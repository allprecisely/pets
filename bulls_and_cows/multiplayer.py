import asyncio
import os
import socket
import time

PORT = int(os.getenv("MULTIPLAYER_PORT", 8765))
HOST = os.getenv("MULTIPLAYER_HOST", "")


class Client:
    def __init__(self, port):
        self.sock = socket.socket()
        self.port = port
        self.error_text = (
            "Соединение не установлено, " "т.к. порт не существует или проблема с сетью"
        )
        self.connected = False
        self.connect_text = 'Ожидание подключения к серверу...'
        self.try_another_server = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self, timeout=5):
        start_connection = time.time()
        while time.time() - start_connection < timeout:
            try:
                self.sock.connect(("localhost", self.port))
                self.connected = True
                return
            except:
                time.sleep(1)
        self.try_another_server = True

    def get_data(self):
        response = self.sock.recv(1024)
        data = response.decode("utf8").split("\n")
        dct = {"op_guess": data[0], "you_bulls": data[1], "you_cows": data[2]}
        return dct

    def send_data(self, guess="", bulls="", cows=""):
        self.sock.sendall(f"{guess}\n{bulls}\n{cows}".encode("utf8"))

    def close(self):
        if not self.sock._closed:
            self.sock.close()


class Server:
    def __init__(self):
        self.sock = socket.socket()
        self.port = PORT
        while True:
            try:
                self.sock.bind((HOST, self.port))
                break
            except:
                self.port += 1
                print(f"new port: {self.port}")
        self.sock.listen(1)
        self.connected = False
        self.conn = None
        self.error_text = "Время ожидания истекло"
        self.connect_text = f'Ожидание подключения второго игрока на порту {self.port}'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        self.conn, addr = self.sock.accept()
        self.connected = True
        print(f"connected by: {addr}")

    def get_data(self):
        response = self.sock.recv(1024)
        data = response.decode("utf8").split("\n")
        dct = {"op_guess": data[0], "you_bulls": data[1], "you_cows": data[2]}
        return dct

    def send_data(self, guess="", bulls="", cows=""):
        self.sock.send(f"{guess}\n{bulls}\n{cows}".encode("utf8"))

    def close(self):
        if self.conn and not self.conn._closed:
            self.conn.close()
        if not self.sock._closed:
            self.sock.close()
