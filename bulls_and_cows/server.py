import asyncio
from datetime import datetime
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
            print("Could not send message. Retry later...")

    async def handle_data(self, _id, data):
        if not isinstance(data, dict):
            print(f"Client sent {data}, returning upper str")
            return data.upper()


class BCServer(Server):
    def __init__(self):
        """
        БД
        # TODO: перенести в базу, чтобы при краше сервера все было ок
        users: {con_id: room_n}
        rooms: {
            room_n: {
                players: {name1: con_id1, name2: con_id2},
                # field: [{
                #     name1: [[guess1, bulls1, cows1], [guess2...]],
                #     name2: [...],
                # }...],
                field: {p1: [g1, b1, c], p2:...},
                created_at: timestamp,
            }
        }
        """
        self.bd = {
            "users": {},
            "rooms": {},
        }
        super().__init__()

    async def handle_data(self, con_id, data):
        if not data:
            name = self.bd["users"].get(con_id)
            if not name:
                return
            del self.bd["users"][con_id]
            for room_id, room in self.bd["rooms"].items():
                if con_id not in room["players"].values():
                    if len(room["players"]) == 1:
                        del self.bd["rooms"][room_id]
                    else:
                        room["players"][name] = ""
                    break
            return
        action = data["action"]
        value = data["value"]
        if action == "connect_to_room":
            """
            Ответы:
            0: ошибка
            1: ответ для создателя комнаты с номером комнаты
            2: ответ с именами
            """
            return {
                "action": action,
                "value": await self.connect_to_room(con_id, value),
            }
        elif action.startswith("send_"):
            _type = action[len("send_") :]
            response = await self.send_value(con_id, value, _type)
            if response:
                return {"action": action, "value": response}

    async def connect_to_room(self, con_id, config):
        name, room_id = config["name"], config["room_id"]
        if not room_id:
            last_room = max(map(int, self.bd["rooms"] or [0]))
            room = "0" * (4 - len(str(last_room))) + str(last_room + 1)
            self.bd["rooms"][room] = {
                "players": {name: con_id},
                "created_at": datetime.now(),
                "field": [{}],
            }
            self.bd["users"][con_id] = self.bd["rooms"][room]
            return 1, room
        room = self.bd["rooms"].get(room_id)
        if not room:
            return 0, "No room with such id"
        if len(room["players"]) == 1 and room["players"].get(name):
            return 0, "Player with such name is already in the room"
        elif len(room["players"]) == 2 and room["players"].get(name) == "":
            return 0, "The room is occupied by other players"

        opponent_name = ""
        for bd_name, bd_con_id in room["players"].items():
            if name != bd_name and bd_con_id:
                # TODO: как сделать гарантию доставки?
                await self.send_data(
                    bd_con_id,
                    {
                        "action": "connect_to_room",
                        "value": (2, name),
                    },
                )
                opponent_name = bd_name
        room["players"][name] = con_id
        self.bd["users"][con_id] = room
        return 2, opponent_name

    async def send_value(self, con_id, value, _type):
        room = self.bd["users"][con_id]
        response = None
        if _type == "guess" and room["field"] and len(room["field"][-1]) == 2:
            room["field"].append({})
        for bd_name, bd_con_id in room["players"].items():
            if con_id == bd_con_id:
                room["field"][-1].setdefault(bd_name, {})[_type] = value
            elif room["field"][-1].get(bd_name, {}).get(_type):
                # TODO: как сделать гарантию доставки?
                await self.send_data(
                    bd_con_id,
                    {
                        "action": f"send_{_type}",
                        "value": value,
                    },
                )
                response = room["field"][-1][bd_name][_type]
        return response


if __name__ == "__main__":
    BCServer()
