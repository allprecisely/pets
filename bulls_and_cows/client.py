"""
Сюда бы хорошо прикрутить брокера
"""
import pickle
import socket
import threading
import time


class Client:
    def __init__(self, host, port, handle_func=None):
        self.host = host
        self.port = port
        self.sock = None
        self.handle_func = handle_func or self.handle_data
        self.connect()

    def connect(self):
        self.close()
        self.sock = socket.socket()
        tries = 5
        while tries:
            try:
                self.sock.connect((self.host, self.port))
                threading.Thread(target=self.get_data, daemon=True).start()
                return
            except ConnectionRefusedError:
                time.sleep(2)
                tries -= 1
            except OSError:
                print('No internet connection')
                break
        print('Could not connect to server. Abort.')
        self.close()
        self.sock = None

    def get_data(self):
        while True:
            data = self.sock.recv(1024)
            if not data:
                print('Server closed connection. Reconnecting...')
                self.connect()
                return
            response = self.handle_func(pickle.loads(data))
            if response:
                self.send_data(response)

    def send_data(self, data):
        try:
            self.sock.send(pickle.dumps(data))
        except BrokenPipeError:
            print('Could not send message. Retry later...')

    def handle_data(self, data):
        pass

    def close(self):
        if self.sock and not self.sock._closed:
            self.sock.close()


class BCClient(Client):
    def __init__(self, handle_func):
        self.responses = []
        super().__init__('192.168.0.16', 8765, handle_func)

    def connect_to_room(self, name, room_id=None):
        self.send_data({
            'action': 'connect_to_room',
            'value': {'name': name, 'room_id': room_id},
        })


if __name__ == '__main__':
    client = Client('192.168.0.16', 8765)
    inp = input('Input what to send: ')
    while inp != 'q':
        client.send_data(inp)
        inp = input('Input what to send: ')
    client.close()
