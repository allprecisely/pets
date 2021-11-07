import asyncio
import os
import socket

PORT = os.getenv('MULTIPLAYER_PORT', 8765)
HOST = os.getenv('MULTIPLAYER_HOST', '')


class Client:
    def __init__(self, port):
        self.socket = socket.socket()
        self.port = port

    def get_connection(self):
        self.socket.connect(('localhost', self.port))

    def get_data(self):
        response = self.socket.recv(1024)
        data = response.decode('utf8').split('\n')
        dct = {'op_guess': data[0], 'you_bulls': data[1], 'you_cows': data[2]}
        return dct

    def send_data(self, guess='', bulls='', cows=''):
        self.socket.sendall(f'{guess}\n{bulls}\n{cows}'.encode('utf8'))

    def close(self):
        if not self.socket._closed:
            self.socket.close()


class Server:
    def __init__(self):
        self.socket = socket.socket(type=socket.SOCK_STREAM | socket.SOCK_NONBLOCK)
        host = HOST
        while True:
            try:
                self.socket.bind((host, PORT))
                break
            except:
                host += 1
                print(f'new host: {host}')
        self.socket.listen(1)
        self.loop = asyncio.get_event_loop()
        self.conn = None

    async def get_connection(self):
        self.conn, addr = await self.loop.sock_accept(self.socket)
        print(f'connected by: {addr}')

    async def get_data(self):
        response = await self.loop.sock_recv(self.conn, 1024)
        print(response)
        data = response.decode('utf8').split('\n')
        print(data)
        dct = {'op_guess': data[0], 'you_bulls': data[1], 'you_cows': data[2]}
        return dct

    async def send_data(self, guess='', bulls='', cows=''):
        await self.loop.sock_sendall(self.conn, f'{guess}\n{bulls}\n{cows}'.encode('utf8'))

    def close(self):
        print(123)
        if self.conn and not self.conn._closed:
            self.conn.close()
        if not self.socket._closed:
            self.socket.close()


# async def server():
#     with socket.socket(type=socket.SOCK_STREAM | socket.SOCK_NONBLOCK) as sock:
#         sock.bind((HOST, PORT))
#         sock.listen(1)
#         loop = asyncio.get_event_loop()
#         conn, addr = await loop.sock_accept(sock)
#
#         with conn:
#             print(f'connected by: {addr}')
#             # while True:
#             await loop.sock_sendall(conn, 'answer'.encode('utf8'))
#                 # data = await loop.sock_recv(conn, 5)
#                 # print('data ', data.decode('utf8'))
#                 # if not data:
#                 #     print(123)
#                 #     await loop.sock_sendall(conn, 'answer'.encode('utf8'))
#                 #     break
#             # await loop.sock_sendall(conn, 'answer'.encode('utf8'))
#
#
# async def main():
#     await asyncio.gather(
#         asyncio.create_task(client()),
#         asyncio.create_task(server()),
#     )

#
# if __name__ == '__main__':
#     asyncio.run(main())
