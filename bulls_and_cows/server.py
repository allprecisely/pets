import asyncio
import socket


def get_addr():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(('10.255.255.255', 1))
        return sock.getsockname()[0]


class Server:
    def __init__(self, host=None, port=None):
        self.host = host or get_addr()
        self.port = port or 8765
        asyncio.run(self.start_server())

    async def start_server(self):
        server = await asyncio.start_server(
            self.handle_new_data, self.host, self.port
        )
        addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Serving on {addrs}')

        async with server:
            await server.serve_forever()

    async def handle_new_data(self):
        pass
