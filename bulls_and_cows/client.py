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
        self.server_connected = None
        self.thread = None

    def connect(self):
        self.server_connected = None
        self.close()
        self.sock = socket.socket()
        tries = 0
        while tries < 5:
            try:
                self.sock.connect((self.host, self.port))
                self.server_connected = True
                self.thread = threading.Thread(target=self.get_data, daemon=True)
                self.thread.start()
                return
            except ConnectionRefusedError:
                tries += 1
                print(f"Could not connect to server {tries} times.")
                time.sleep(1)
            except OSError:
                print("No internet connection")
                break
        print("Abort. Number of tries exceeded")
        self.close()
        self.sock = None
        self.server_connected = False

    def get_data(self):
        self.sock.settimeout(5)
        while True:
            while True:
                try:
                    data = self.sock.recv(1024)
                    break
                except socket.timeout:
                    print("check if socket is alive")
                except OSError:
                    print("socket is dead")
                    return
                except AttributeError:
                    print("problems with server")
            if data:
                data = pickle.loads(data)
            response = self.handle_func(data)
            if response:
                self.send_data(response)

    def send_data(self, data):
        try:
            self.sock.send(pickle.dumps(data))
        except BrokenPipeError:
            print("Could not send message. Retry later...")

    def handle_data(self, data):
        print(f"Received from server: {data}")

    def close(self):
        if self.sock and not self.sock._closed:
            print("Client has closed connection.")
            self.sock.close()


class BCClient(Client):
    def __init__(self, handle_func):
        super().__init__("192.168.0.16", 8765, handle_func)

    def connect_to_room(self, name, room_id=None):
        self.send_data(
            {
                "action": "connect_to_room",
                "value": {"name": name, "room_id": room_id},
            }
        )

    def send_guess(self, guess):
        self.send_data({"action": "send_guess", "value": guess})


if __name__ == "__main__":
    client = Client("192.168.0.16", 8765)
    try:
        inp = input("Input what to send: ")
        while inp != "q":
            client.send_data(inp)
            inp = input("Input what to send: ")
    except KeyboardInterrupt:
        print("\n\nGame was closed")
        client.close()
