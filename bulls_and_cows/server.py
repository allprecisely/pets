import asyncio
import pickle
import socket


def get_addr():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("10.255.255.255", 1))
        return sock.getsockname()[0]


class Server:
    def __init__(self, host=None, port=None):
        self.host = host or get_addr()
        self.port = port or 8765
        self.connections = {}
        asyncio.run(self.start_server())

    async def start_server(self):
        server = await asyncio.start_server(self.handle_request, self.host, self.port)
        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        print(f"Serving on {addrs}")

        async with server:
            await server.serve_forever()

    async def handle_request(self, reader, writer):
        con_id = writer.get_extra_info("peername")
        print(f"Started listen {con_id}")
        self.connections[con_id] = reader, writer
        while True:
            data = await reader.read(1024)
            if not data:
                await self.handle_data(con_id, None)
                print(f"Client {con_id} closed connection")
                del self.connections[con_id]
                writer.close()
                break
            response = await self.handle_data(con_id, pickle.loads(data))
            if response:
                writer.write(pickle.dumps(response))
                await writer.drain()

    async def send_data(self, whom, data):
        writer = self.connections[whom][1]
        try:
            writer.write(pickle.dumps(data))
            await writer.drain()
        except BrokenPipeError:
            print('Could not send message. Retry later...')

    async def handle_data(self, _id, data):
        return "answer"


class BCServer(Server):
    def __init__(self):
        """
        Ответы:
        0: ошибка
        1: ответ нужен, все в порядке
        2: ответ не нужен, все ок
        БД
        users: {name: con_id}
        rooms: {n: {name1: connected?, name2: connected?}}
        """
        self.bd = {"users": {}, "rooms": {}}
        super().__init__()

    async def handle_data(self, con_id, data):
        if not data:
            for key, value in self.bd["users"].items():
                if value == con_id:
                    del self.bd["users"][key]
                    return
        action = data["action"]
        value = data["value"]
        if action == "connect_to_room":
            return {
                "action": "connect_to_room",
                "value": await self.connect_to_room(con_id, value),
            }

    async def connect_to_room(self, con_id, config):
        last_con_id = self.bd["users"].get(config["name"])
        if last_con_id and last_con_id != con_id:
            return 0, "User with such name already exists. Choose other."
        self.bd["users"][config["name"]] = con_id
        if not config["room_id"]:
            last_room = str(len(self.bd["rooms"]))
            room = "0" * max(4 - len(last_room), 0) + last_room
            self.bd["rooms"][room] = {config["name"]: True}
            return 1, room
        room = self.bd["rooms"].get(config["room_id"])
        if not room:
            return 0, "No room with such id"
        if len(room) < 2 or not room.get(config["name"], True):
            for user, connected in room.items():
                if user != config["name"] and connected:
                    await self.send_data(self.bd["users"][user], (2, "OK"))
            room[config["name"]] = True
            return 2, "OK"
        return 0, "The room is occupied by other players"


if __name__ == "__main__":
    BCServer()
