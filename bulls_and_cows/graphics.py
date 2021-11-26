# TODO: разнести функцию на окошки/тулзы
# TODO: обмазаться логами

from datetime import datetime
import time
import threading
from tkinter import *
from tkinter import messagebox

import guesser
import client
import utils

root = Tk()
WAIT_CONNECTION_TIME = 60000  # ms


class SingleGame:
    def __init__(self):
        for widget in root.winfo_children():
            widget.destroy()
        self.turn = 1
        self.generator = guesser.graphical_main()
        draw_game_field()
        Button(root, text="Start new game", command=SingleGame).grid(
            row=9, column=11, columnspan=2
        )
        self.start_time = datetime.now()
        root.children["lbl_time_started"].config(
            text=self.start_time.strftime("%H:%M:%S")
        )
        # for change data btwn functions
        self.op_guess_val = self.you_bulls_val = self.you_cows_val = None
        # for convenience
        self.you_guess = self.op_bulls = self.op_cows = None

        self.guess()

    def answer(self):
        if not (self.op_bulls.get() and self.op_cows.get()):
            messagebox.showinfo("Error", "Fields cannot be empty")
            return
        is_correct = self.generator.send(f"{self.op_bulls.get()} {self.op_cows.get()}")
        if not is_correct:
            messagebox.showinfo("Error", "Data you sent are not valid")
            return
        self.op_guess_val = next(self.generator)
        self.op_bulls.config(state=DISABLED)
        self.op_cows.config(state=DISABLED)
        fill_entry(root.children[f"you_bulls_{self.turn}"], self.you_bulls_val)
        fill_entry(root.children[f"you_cows_{self.turn}"], self.you_cows_val)
        if self.op_bulls.get() == "4":
            if self.you_bulls_val == "4":
                self.end_game("draw")
                return
            self.end_game("opponent")
            return
        elif self.you_bulls_val == "4":
            self.end_game("you")
            return
        self.turn += 1
        self.guess()

    def get_guess_back(self):
        player_guess = self.you_guess.get()
        if len(player_guess) < 4:
            messagebox.showinfo("Error", "There should be 4 digits")
            return
        self.you_guess.config(state=DISABLED)
        if not self.op_guess_val:
            self.op_guess_val = next(self.generator)
        self.you_bulls_val, self.you_cows_val = self.generator.send(
            player_guess
        ).split()
        fill_entry(root.children[f"op_guess_{self.turn}"], self.op_guess_val)
        self.op_bulls.config(state=NORMAL)
        self.op_cows.config(state=NORMAL)
        root.children["btn_send"].config(command=self.answer)
        handle_game_key(self.answer, self.op_bulls, self.op_cows)

    def guess(self):
        draw_turn(self.turn)
        self.you_guess = root.children[f"you_guess_{self.turn}"]
        self.op_bulls = root.children[f"op_bulls_{self.turn}"]
        self.op_cows = root.children[f"op_cows_{self.turn}"]
        self.you_guess.config(state=NORMAL)
        self.you_guess.focus_set()
        root.children["btn_send"].config(command=self.get_guess_back)
        handle_game_key(self.get_guess_back, self.you_guess)

    def end_game(self, who_win):
        for entry in (self.you_guess, self.op_bulls, self.op_cows):
            if entry:
                entry.config(state=DISABLED)
        root.children["btn_send"].config(state=DISABLED)
        root.children["lbl_player_won"].config(text=who_win)
        cur_time = datetime.now()
        root.children["lbl_time_ended"].config(text=cur_time.strftime("%H:%M:%S"))

        duration = time.strftime(
            "%Mm%Ss", time.gmtime((cur_time - self.start_time).total_seconds())
        )
        root.children["lbl_duration"].config(text=duration)
        if who_win == "opponent":
            messagebox.showinfo("Defeat", "You lost.")
        elif who_win == "you":
            messagebox.showinfo("Win", "You won.")
        else:
            messagebox.showinfo("Draw", "Draw :)")


class MultiplayerGame:
    def __init__(self):
        self.client = None
        self.is_polling = False
        self.active_widgets = []
        self.name = ""
        self.opponent_name = ""
        self.room_id = ""
        self.start_time = None
        self.turn = 0
        # for convenience
        self.you_guess = self.op_bulls = self.op_cows = self.btn_send = None

        frame = root.nametowidget(".frame_local_game")
        frame.nametowidget("btn_create_game").config(command=self.connect_to_server)
        self.connect_to_server()

    def connect_to_server(self):
        if not self.is_polling:
            if not self.name:
                self.handle_widgets_menu()
                if not self.name:
                    return
                self.client = self.client or client.BCClient(self.handle_responses)
                frame = root.nametowidget(".frame_local_game")
                frame.children["btn_quit"].config(command=lambda: _quit(self.client))
                frame.children["btn_main_menu"].config(
                    command=lambda: draw_main_menu(self.client)
                )
            else:
                self.widget_state_change(DISABLED)
            threading.Thread(target=self.client.connect).start()
            self.is_polling = True
        if self.client.server_connected:
            self.is_polling = False
            if not self.active_widgets:
                self.connect_to_room()
            else:
                self.widget_state_change(NORMAL)
        elif self.client.server_connected is None:
            root.after(250, self.connect_to_server)
        else:
            self.is_polling = False
            if not self.active_widgets:
                self.widget_state_change(NORMAL)
            else:
                root.nametowidget(".lbl_connecting").config(text="Problems with server")

    def handle_widgets_menu(self):
        frame = root.nametowidget(".frame_local_game")
        self.name = frame.nametowidget("frame_name").children["entry_name"].get()
        if not self.name:
            messagebox.showinfo("Error", "Type name.")
            return
        entry_room_id = frame.children.get("frame_room")
        self.room_id = None
        if entry_room_id:
            self.room_id = entry_room_id.children["room_id"].get()
            if not self.room_id:
                messagebox.showinfo("Error", "Type room id.")
                return
        self.widget_state_change(DISABLED)

    def connect_to_room(self):
        if not self.name:
            self.handle_widgets_menu()
        self.client.connect_to_room(self.name, self.room_id)

    def handle_responses(self, data):
        if not data:
            self.is_polling = False
            root.after(250, self.connect_to_server)
            return
        action = data["action"]
        value = data["value"]
        if action == "connect_to_room" and not self.active_widgets:
            if value[0] == 0:
                self.widget_state_change(NORMAL)
                messagebox.showinfo("Error", value[1])
                self.name = self.room_id = ""
            elif value[0] == 1:
                self.room_id = value[1]
                root.nametowidget(".frame_local_game.lbl_connecting").config(
                    text=f"Waiting for connection... Room: {self.room_id}",
                )
            elif value[0] == 2:
                self.opponent_name = value[1]
                self.start_new_game()
                self.start_guess()
                if value[2]:
                    self.btn_send.config(state=DISABLED)
                    print(value[2])
                    for turn, player, guess, bulls, cows in value[2]:
                        print(turn, player, guess, bulls, cows)
                        if turn != self.turn:
                            self.turn = turn
                            draw_turn(self.turn)
                        g, bc = ("you", "op") if player == self.name else ("op", "you")
                        fill_entry(root.children[f"{g}_guess_{turn}"], guess)
                        fill_entry(root.children[f"{bc}_bulls_{turn}"], bulls)
                        fill_entry(root.children[f"{bc}_cows_{turn}"], cows)
                    if (
                        root.children[f"op_guess_{self.turn}"].get()
                        and root.children[f"you_guess_{self.turn}"].get()
                        and not root.children[f"op_bulls_{self.turn}"].get()
                    ):
                        self.start_answer()
                    elif (
                        root.children[f"op_bulls_{self.turn}"].get()
                        and root.children[f"you_bulls_{self.turn}"].get()
                    ):
                        self.start_guess()
                    self.op_bulls = root.children[f"op_bulls_{self.turn}"]
                    self.op_cows = root.children[f"op_cows_{self.turn}"]
                    messagebox.showinfo("Attention", "Continue playing...")
        elif action == "send_value":
            if value["type"] == "guess":
                fill_entry(root.children[f"op_guess_{self.turn}"], value["data"][0])
                self.start_answer()
            else:
                bulls, cows = value["data"]
                fill_entry(root.children[f"you_bulls_{self.turn}"], bulls)
                fill_entry(root.children[f"you_cows_{self.turn}"], cows)
                winner = None
                print(self.name, bulls, type(bulls))
                if self.op_bulls.get() == "4":
                    if bulls == "4":
                        winner = "draw"
                    else:
                        winner = "opponent"
                elif bulls == "4":
                    winner = "you"
                if winner:
                    self.end_game(winner)
                    return
                self.start_guess()

    def widget_state_change(self, state):
        frame = root.children.get("frame_local_game", root)
        if state == NORMAL:
            frame.children["lbl_connecting"].destroy()
        else:
            lbl = Label(frame, text="Connecting...", pady=5, name="lbl_connecting")
            if frame == root:
                lbl.grid(row=12, column=5, columnspan=4)
            else:
                lbl.pack()
        for widget_name in ("btn_create_game", "btn_join_game"):
            widget = frame.children.get(widget_name)
            if widget:
                widget.config(state=state)
        for widget in self.active_widgets + [self.btn_send]:
            if widget:
                widget.config(state=state)

    def start_new_game(self):
        for widget in root.winfo_children():
            widget.destroy()
        draw_game_field()
        self.btn_send = root.children["btn_send"]
        self.start_time = datetime.now()
        root.children["lbl_time_started"].config(
            text=self.start_time.strftime("%H:%M:%S")
        )
        root.children["btn_quit"].config(
            command=lambda: pop_up(
                yes=lambda: _quit(self.client),
                text="Are you sure, that you want to quit?",
            )
        )
        root.children["btn_main_menu"].config(
            command=lambda: pop_up(
                yes=lambda: draw_main_menu(self.client),
                text="Are you sure, that you want to leave the game?",
            )
        )
        root.children["lbl_versus"].config(text=f"{self.name} vs. {self.opponent_name}")
        Label(root, text="room").grid(row=12, column=0, columnspan=2)
        Label(root, text=self.room_id).grid(row=12, column=2)

    def start_guess(self):
        self.turn += 1
        draw_turn(self.turn)
        self.you_guess = root.children[f"you_guess_{self.turn}"]
        self.you_guess.config(state=NORMAL)
        self.you_guess.focus_set()
        self.btn_send.config(command=self.set_guesses, state=NORMAL)
        handle_game_key(self.set_guesses, self.you_guess)
        self.active_widgets = [self.you_guess]

    def set_guesses(self):
        data = self.you_guess.get()
        if len(data) < 4:
            messagebox.showinfo("Error", "There should be 4 digits")
            return
        self.you_guess.config(state=DISABLED)
        self.btn_send.config(state=DISABLED)
        self.client.send_value({"type": "guess", "data": (data,), "turn": self.turn})
        self.active_widgets = []

    def start_answer(self):
        self.op_bulls = root.children[f"op_bulls_{self.turn}"]
        self.op_cows = root.children[f"op_cows_{self.turn}"]
        self.op_bulls.config(state=NORMAL)
        self.op_cows.config(state=NORMAL)
        self.btn_send.config(command=self.set_answers, state=NORMAL)
        handle_game_key(self.set_answers, self.op_bulls, self.op_cows)
        self.active_widgets = [self.op_bulls, self.op_cows]

    def set_answers(self):
        bulls, cows = self.op_bulls.get(), self.op_cows.get()
        if not bulls:
            if bulls == "4" and not cows:
                fill_entry(self.op_cows, "0")
                cows = "0"
            else:
                messagebox.showinfo("Error", "Fields cannot be empty")
                return
        # TODO: Сделать валидацию data через guessing
        self.op_bulls.config(state=DISABLED)
        self.op_cows.config(state=DISABLED)
        self.btn_send.config(state=DISABLED)
        self.client.send_value(
            {"type": "bulls, cows", "data": (bulls, cows), "turn": self.turn}
        )
        self.active_widgets = []

    def end_game(self, who_win):
        for widget in self.active_widgets:
            widget.config(state=DISABLED)
        root.children["btn_main_menu"].config(
            command=lambda: draw_main_menu(self.client)
        )
        if who_win == "nobody":
            messagebox.showinfo("Attention", "You opponent has left")
            return
        root.children["lbl_player_won"].config(text=who_win)
        cur_time = datetime.now()
        root.children["lbl_time_ended"].config(text=cur_time.strftime("%H:%M:%S"))

        duration = time.strftime(
            "%Mm%Ss", time.gmtime((cur_time - self.start_time).total_seconds())
        )
        root.children["lbl_duration"].config(text=duration)
        if who_win == "opponent":
            messagebox.showinfo("Defeat", "You lost.")
        elif who_win == "you":
            messagebox.showinfo("Win", "You won.")
        else:
            messagebox.showinfo("Draw", "Draw :)")


def draw_join_game():
    frame = root.nametowidget(".frame_local_game")
    btn_connect = frame.nametowidget("btn_create_game")
    btn_connect.config(text="Connect")
    frame.nametowidget("btn_join_game").destroy()

    frame_room = Frame(frame, name="frame_room")
    Label(frame_room, text="Room id", pady=5, padx=5).pack(side=LEFT)
    entry_room = Entry(frame_room, fg="grey", name="room_id", width=5)
    entry_room.pack(side=RIGHT)

    entry_handle(entry_room, "777")
    frame_room.pack(before=btn_connect)
    frame_name = frame.children["frame_name"]
    frame_room.lift(aboveThis=frame_name)
    handle_game_key(MultiplayerGame, frame_name.children["entry_name"], entry_room)


def draw_local_game(old_frame):
    old_frame.destroy()

    frame = Frame(root, name="frame_local_game")
    frame.pack()
    frame_name = Frame(frame, name="frame_name")
    frame_name.pack()
    Label(frame_name, text="Name", pady=5, padx=5).pack(side=LEFT)
    entry_name = Entry(frame_name, fg="grey", name="entry_name", width=10)
    entry_name.pack(side=RIGHT)
    entry_handle(entry_name, "player")
    handle_game_key(MultiplayerGame, entry_name)

    Button(
        frame, text="Create game", command=MultiplayerGame, name="btn_create_game"
    ).pack()
    Button(frame, text="Join game", command=draw_join_game, name="btn_join_game").pack()
    Button(frame, text="Main menu", command=draw_main_menu, name="btn_main_menu").pack()
    Button(frame, text="Quit", command=_quit, name="btn_quit").pack()


def draw_main_menu(interface=None):
    if interface:
        threading.Thread(target=interface.close).start()
    for widget in root.winfo_children():
        widget.destroy()
    Label(
        root, text="BULLS & COWS", font=("Arial", 30), height=3, anchor="s", pady=20
    ).pack()
    frame_main_menu = Frame(root)
    # TODO: окошечко со статистикой
    btns = [
        Button(frame_main_menu, text="Single game", command=SingleGame),
        Button(
            frame_main_menu,
            text="Local game",
            command=lambda: draw_local_game(frame_main_menu),
        ),
        Button(frame_main_menu, text="Quit", command=_quit),
    ]
    for btn in [frame_main_menu, *btns]:
        btn.pack()


def draw_game_field():
    Label(root, text="YOU", pady=5).grid(row=0, column=0, columnspan=4)
    Label(root, text="№", pady=5).grid(row=1, column=0)
    Label(root, text="Guess", pady=5).grid(row=1, column=1)
    Label(root, text="Bulls", pady=5).grid(row=1, column=2)
    Label(root, text="Cows", pady=5).grid(row=1, column=3)

    Label(root, text=" " * 10, pady=5).grid(row=1, column=4)

    Label(root, text="OPPONENT", pady=5).grid(row=0, column=5, columnspan=4)
    Label(root, text="№", pady=5).grid(row=1, column=6)
    Label(root, text="Guess", pady=5).grid(row=1, column=7)
    Label(root, text="Bulls", pady=5).grid(row=1, column=8)
    Label(root, text="Cows", pady=5).grid(row=1, column=9)

    Label(root, text=" " * 10, pady=5).grid(row=1, column=10)

    Button(root, text="Send", name="btn_send").grid(
        row=0, column=11, columnspan=2, rowspan=2
    )

    Label(root, text="STATISTICS", pady=5).grid(row=2, column=11, columnspan=2)
    Label(root, text="you vs. comp", pady=5, name="lbl_versus").grid(
        row=3, column=11, columnspan=2
    )
    Label(root, text="Time started   ", pady=5).grid(row=4, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_time_started").grid(row=4, column=12)
    Label(root, text="Time ended", pady=5).grid(row=5, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_time_ended").grid(row=5, column=12)
    Label(root, text="Duration", pady=5).grid(row=6, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_duration").grid(row=6, column=12)

    Label(root, text=" ", pady=5).grid(row=7, column=11)

    Label(root, text="Player won", pady=5).grid(row=8, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_player_won").grid(row=8, column=12)

    Label(root, text=" ", pady=5).grid(row=9, column=11)

    # TODO: кнопочка с новой игрой
    Button(
        root,
        text="Main menu",
        command=lambda: pop_up(
            yes=draw_main_menu, text="Are you sure, that you want to leave the game?"
        ),
        name="btn_main_menu",
    ).grid(row=11, column=11, columnspan=2)
    Button(
        root,
        text="Quit",
        command=lambda: pop_up(yes=quit, text="Are you sure, that you want to quit?"),
        name="btn_quit",
    ).grid(row=12, column=11, columnspan=2)


def draw_turn(n, frame=root):
    def validate_guess(act, ind, new_val, old_val):
        val = get_val_before_validate(act, ind, new_val, old_val)
        if val.isdigit() and len(val) <= 4:
            return len(val) == len(set(val))
        return False

    def validate_digit(act, ind, new_val, old_val):
        if not old_val or act == "0":
            return new_val in set("01234")
        return False

    Label(frame, text=str(n), pady=5).grid(row=n + 1, column=0)
    Label(frame, text=str(n), pady=5).grid(row=n + 1, column=6)
    # TODO: если раундов слишком много, добавить скролл
    entries = {
        1: Entry(frame, width=5, name=f"you_guess_{n}"),
        2: Entry(frame, width=2, name=f"you_bulls_{n}"),
        3: Entry(frame, width=2, name=f"you_cows_{n}"),
        7: Entry(frame, width=5, name=f"op_guess_{n}"),
        8: Entry(frame, width=2, name=f"op_bulls_{n}"),
        9: Entry(frame, width=2, name=f"op_cows_{n}"),
    }
    for column, entry in entries.items():
        validate_func = validate_guess if column in (1, 7) else validate_digit
        entry.config(
            validate="key",
            validatecommand=decor_register(entry, validate_func),
            state=DISABLED,
        )
        entry.grid(row=n + 1, column=column)


def get_val_before_validate(act, ind, new_val, old_val):
    if act == "0":
        return old_val[: int(ind)] + old_val[int(ind) + len(new_val) :]
    else:
        return old_val[: int(ind)] + new_val + old_val[int(ind) :]


def decor_register(widget, func):
    return widget.register(func), "%d", "%i", "%S", "%s"


def pop_up(yes=None, no=None, text="Are you sure?", title="Attention!"):
    def inner(func):
        if func:
            func()
        top_level.destroy()

    assert yes or no
    top_level = Toplevel(root)
    top_level.title = title
    Label(top_level, text=text).grid(row=0, column=0, columnspan=2)
    Button(top_level, text="Yes", command=lambda: inner(yes)).grid(row=1, column=0)
    Button(top_level, text="No", command=lambda: inner(no)).grid(row=1, column=1)


def handle_game_key(func, *entry_fields):
    def inner_func(event):
        if event.char == "\r":
            func()
        elif root.focus_get() not in entry_fields and event.char != "\t":
            entry_fields[0].focus_set()
            root.after(1, entry_fields[0].insert, END, event.char)

    root.bind("<Key>", inner_func)


def entry_handle(entry, default_text):
    def inner_func(event):
        if entry.get() == default_text:
            entry.delete(0, END)
            entry.config(fg="black")
        elif entry.get() == "":
            entry.insert(0, default_text)
            entry.config(fg="grey")

    entry.insert(0, default_text)
    for sequence in ("<FocusIn>", "<FocusOut>"):
        entry.bind(sequence, inner_func)


def fill_entry(entry_form, value):
    if entry_form and value:
        entry_form.config(state=NORMAL)
        entry_form.insert(0, value)
        entry_form.config(state=DISABLED)


def _quit(interface=None):
    if interface:
        threading.Thread(target=interface.close).start()
    root.after(50, root.quit)


def main():
    root.title("Bulls and cows!")
    root.geometry("550x360")

    draw_main_menu()
    root.mainloop()


if __name__ == "__main__":
    utils.init_logger()
    main()
