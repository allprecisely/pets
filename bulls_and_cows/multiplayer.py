import asyncio
import os
import socket

PORT = os.getenv('MULTIPLAYER_PORT', 8765)
HOST = os.getenv('MULTIPLAYER_HOST', '')


async def client():
    with socket.socket(type=socket.SOCK_STREAM | socket.SOCK_NONBLOCK) as sock:
        await asyncio.sleep(2)
        loop = asyncio.get_event_loop()
        await loop.sock_connect(sock, ('localhost', 8765))
        # await loop.sock_sendall(sock, 'hello, world!'.encode('utf8'))
        # print(await loop.sock_recv(sock, 1024))
        await asyncio.sleep(2)
        # await loop.sock_sendall(sock, 'hello, world2!'.encode('utf8'))
        print(await loop.sock_recv(sock, 1024))


async def server():
    with socket.socket(type=socket.SOCK_STREAM | socket.SOCK_NONBLOCK) as sock:
        sock.bind((HOST, PORT))
        sock.listen(1)
        loop = asyncio.get_event_loop()
        conn, addr = await loop.sock_accept(sock)

        with conn:
            print(f'connected by: {addr}')
            # while True:
            await loop.sock_sendall(conn, 'answer'.encode('utf8'))
                # data = await loop.sock_recv(conn, 5)
                # print('data ', data.decode('utf8'))
                # if not data:
                #     print(123)
                #     await loop.sock_sendall(conn, 'answer'.encode('utf8'))
                #     break
            # await loop.sock_sendall(conn, 'answer'.encode('utf8'))


async def main():
    await asyncio.gather(
        asyncio.create_task(client()),
        asyncio.create_task(server()),
    )


if __name__ == '__main__':
    asyncio.run(main())
