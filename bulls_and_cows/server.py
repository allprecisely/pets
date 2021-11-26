import asyncio
from datetime import datetime
import pickle
import socket
import sqlite3


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
        con_id = str(writer.get_extra_info("peername"))
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
        self.con = sqlite3.connect("server.db")
        try:
            self.cur = self.con.cursor()
            self.create_tables()
            super().__init__()
        finally:
            self.con.close()

    def create_tables(self):
        self.cur.execute(
            """
                CREATE TABLE IF NOT EXISTS rooms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player1_name TEXT NOT NULL,
                    player2_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
        )
        self.cur.execute(
            """
                CREATE TABLE IF NOT EXISTS fields (
                    room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
                    turn INTEGER NOT NULL,
                    player_name TEXT NOT NULL,
                    guess TEXT,
                    bulls TEXT,
                    cows TEXT,
                    PRIMARY KEY (room_id, turn, player_name)
                )
            """
        )
        self.cur.execute(
            """
                CREATE TABLE IF NOT EXISTS users (
                    con_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    room_id INTEGER REFERENCES rooms(id)
                )
            """
        )
        self.con.commit()

    async def handle_data(self, con_id, data):
        if not data:
            # TODO: хорошо бы сообщать пользователю, если противник ливнул
            # TODO (sqlite): переделать на USING, когда его введут
            self.cur.execute(
                """
                    DELETE FROM rooms WHERE player2_name IS NULL
                        AND id = (SELECT room_id FROM users WHERE con_id = ?)
                """,
                (con_id,),
            )
            # TODO: в случае отключения сервера юзер не удалится, если выйти
            self.cur.execute("DELETE FROM users WHERE con_id = ?", (con_id,))
            self.con.commit()
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
        elif action == "send_value":
            response = await self.send_value(con_id, value)
            if response:
                return {"action": action, "value": response}

    async def connect_to_room(self, con_id, config):
        name, room_id = config["name"], config["room_id"]

        if not room_id:
            # TODO (sqlite): use RETURNING id after sqlite=3.35
            self.cur.execute("INSERT INTO rooms (player1_name) values (?)", (name,))
            room_id = self.cur.execute(
                "SELECT id FROM rooms WHERE player1_name = ? ORDER BY id DESC", (name,)
            ).fetchone()[0]
            print(con_id, name, room_id)
            self.cur.execute(
                "INSERT INTO users (con_id, name, room_id) values (?, ?, ?)",
                (con_id, name, room_id),
            )
            self.con.commit()
            return 1, room_id

        players = self.cur.execute(
            """
                SELECT con_id, player1_name, player2_name FROM users JOIN rooms
                    ON room_id = id WHERE room_id = ?
            """,
            (room_id,),
        ).fetchall()
        if not players:
            return 0, "No room with such id"
        if len(players) == 2:
            return 0, "The room is occupied by other players"
        if name not in players[0][1:] and None not in players[0][1:]:
            return 0, "Player with such name is already in the room"

        response = self.con.execute(
            f"""
                SELECT turn, player_name, guess, bulls, cows FROM fields 
                    WHERE room_id = ? ORDER BY turn
            """,
            (room_id,),
        ).fetchall()
        self.cur.execute(
            "INSERT INTO users (con_id, name, room_id) values (?, ?, ?)",
            (con_id, name, room_id),
        )
        opponent_name = None
        for i, player_name in enumerate(players[0][1:]):
            if player_name is None:
                self.cur.execute(
                    f"UPDATE rooms SET player{i + 1}_name = ? WHERE id = ?",
                    (name, room_id),
                )
            elif player_name != name:
                # TODO: как сделать гарантию доставки?
                await self.send_data(
                    players[0][0],
                    {"action": "connect_to_room", "value": (2, name, response)},
                )
                opponent_name = player_name
        assert opponent_name
        self.con.commit()
        return 2, opponent_name, response

    async def send_value(self, con_id, value):
        fetched_data = self.con.execute(
            """
                SELECT con_id, name, room_id FROM users 
                    WHERE room_id = (SELECT room_id FROM users WHERE con_id = ?)
            """,
            (con_id,),
        ).fetchall()
        room_id = self_name = op_name = op_con_id = None
        for db_con_id, name, room_id in fetched_data:
            if db_con_id != con_id:
                op_name = name
                op_con_id = db_con_id
            else:
                self_name = name
        assert room_id and self_name and op_name and op_con_id
        if value["type"] == "guess":
            self.con.execute(
                f"""
                    INSERT INTO fields (room_id, turn, player_name, guess) 
                        VALUES (?, ?, ?, ?) 
                """,
                (room_id, value["turn"], self_name, *value["data"]),
            )
        else:
            self.con.execute(
                f"""
                    UPDATE fields SET bulls = ?, cows = ? 
                        WHERE room_id = ? AND turn = ? AND player_name = ?
                """,
                (*value["data"], room_id, value["turn"], self_name),
            )
        self.con.commit()
        response = self.con.execute(
            f"""
                SELECT {value["type"]} FROM fields 
                    WHERE room_id = ? AND turn = ? AND player_name = ?
            """,
            (room_id, value["turn"], op_name),
        ).fetchone()

        if response and response[0]:
            # TODO: как сделать гарантию доставки?
            await self.send_data(
                op_con_id,
                {
                    "action": "send_value",
                    "value": value,
                },
            )
            return {"type": value["type"], "data": response}


if __name__ == "__main__":
    BCServer()
