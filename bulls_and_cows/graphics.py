"""
новая партия
валидация полей
"""
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
        self.round = 1
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
        insert_value(root.children[f"you_bulls_{self.round}"], self.you_bulls_val)
        insert_value(root.children[f"you_cows_{self.round}"], self.you_cows_val)
        if self.op_bulls.get() == "4":
            if self.you_bulls_val == "4":
                self.end_game("draw")
                return
            self.end_game("opponent")
            return
        elif self.you_bulls_val == "4":
            self.end_game("you")
            return
        self.round += 1
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
        insert_value(root.children[f"op_guess_{self.round}"], self.op_guess_val)
        self.op_bulls.config(state=NORMAL)
        self.op_cows.config(state=NORMAL)
        root.children["btn_send"].config(command=self.answer)
        handle_game_key(self.answer, self.op_bulls, self.op_cows)

    def guess(self):
        draw_round(self.round)
        self.you_guess = root.children[f"you_guess_{self.round}"]
        self.op_bulls = root.children[f"op_bulls_{self.round}"]
        self.op_cows = root.children[f"op_cows_{self.round}"]
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

        self.connect_to_server()

        self.start_time = None
        # self.round = 1
        # # for change data btwn functions
        # self.op_guess_val = self.you_bulls_val = self.you_cows_val = None
        # # for convenience
        # self.you_guess = self.op_bulls = self.op_cows = None
        #
        # self.polling_started = False
        # self.data = None
        #
        # self.start_connection()

    def connect_to_server(self):
        frame = root.nametowidget(".frame_local_game")
        name = frame.nametowidget('frame_name').children["entry_name"].get()
        if not name:
            messagebox.showinfo("Error", "Type name.")
            return
        lbl_connecting = Label(
            root.nametowidget(".frame_local_game"), pady=5, name="lbl_connecting"
        )
        entry_room_id = frame.children.get('frame_room')
        room_id = None
        if entry_room_id:
            room_id = entry_room_id.children["room_id"].get()
            if not room_id:
                messagebox.showinfo("Error", "Type room id.")
                return
            lbl_connecting.config(text="Connecting...")
        else:
            lbl_connecting.config(text="Creating room...")
        lbl_connecting.pack()
        self.button_state_change()
        self.client = self.client or client.BCClient(self.handle_responses)

        if not self.client.sock:
            lbl_connecting.destroy()
            self.button_state_change()
            self.client = None
            messagebox.showinfo("Error", "Problems with connection")
            return
        self.client.connect_to_room(room_id)

    def handle_responses(self, data):
        action = data["action"]
        value = data["value"]
        if action == "connect_to_room":
            if value[0] == 0:
                messagebox.showinfo("Error", value[1])
                self.button_state_change()
            elif value[0] == 1:
                root.nametowidget(".frame_local_game.lbl_connecting").config(
                    text=f"Waiting for connection... Room: {value[1]}",
                )
            elif value[0] == 2:
                self.start_new_game()

    def button_state_change(self):
        frame = root.nametowidget(".frame_local_game")
        frame.children["btn_quit"].config(command=lambda: _quit(self.client))
        frame.children["btn_main_menu"].config(
            command=lambda: draw_main_menu(self.client)
        )
        for widget_name in ("btn_create_game", "btn_join_game", "room_id"):
            btn = frame.children.get(widget_name)
            print(widget_name, btn)
            if btn:
                btn.config(state=DISABLED if btn["state"] == ACTIVE else ACTIVE)
                print(btn['state'])

    # def start_connection(self, counter=20000):
    #     if self.interface.closed:
    #         return
    #     if not counter or getattr(self.interface, "try_another_server", False):
    #         frame = root.nametowidget(".frame_local_game")
    #         frame.children["lbl_connecting"].destroy()
    #         frame.children["btn_create_game"].config(state=NORMAL)
    #         btn_join_game = frame.children.get("btn_join_game")
    #         if btn_join_game:
    #             btn_join_game.config(state=NORMAL)
    #         threading.Thread(target=self.interface.close).start()
    #         messagebox.showinfo("Error", self.interface.error_text)
    #     elif not self.interface.connected:
    #         root.after(250, self.start_connection, counter - 250)
    #     else:
    #         self.start_new_game()
    #
    def start_new_game(self):
        for widget in root.winfo_children():
            widget.destroy()
        draw_game_field()
        self.start_time = datetime.now()
        root.children["lbl_time_started"].config(
            text=self.start_time.strftime("%H:%M:%S")
        )
        Label(root, text="H").grid(row=11, column=0)
        # Label(root, text=f"{self.interface.ip_address}:{self.interface.port}").grid(
        #     row=11, column=1, columnspan=4
        # )

        # self.start_guess()

    #
    # def set_answers(self):
    #     validate = lambda answer: True  # Сделать валидацию
    #     bulls, cows = self.op_bulls.get(), self.op_cows.get()
    #     if not (bulls and cows):
    #         messagebox.showinfo("Error", "Fields cannot be empty")
    #         return
    #     self.data = f"{bulls} {cows}"
    #     if not validate(self.data):
    #         messagebox.showinfo("Error", "Data you sent are not valid")
    #         return
    #     self.op_bulls.config(state=DISABLED)
    #     self.op_cows.config(state=DISABLED)
    #     self.polling(self.start_guess)
    #
    # def start_answer(self):
    #     insert_value(root.children[f"op_guess_{self.round}"], self.interface.data)
    #     self.op_bulls.config(state=NORMAL)
    #     self.op_cows.config(state=NORMAL)
    #     root.children["btn_send"].config(command=self.set_answers)
    #     handle_game_key(self.set_answers, self.op_bulls, self.op_cows)
    #
    # def set_guesses(self):
    #     self.data = self.you_guess.get()
    #     if len(self.data) < 4:
    #         messagebox.showinfo("Error", "There should be 4 digits")
    #         return
    #     self.you_guess.config(state=DISABLED)
    #     self.polling(self.start_answer)
    #
    # def start_guess(self):
    #     if self.interface.data:
    #         bulls, cows = self.interface.data.split()
    #         insert_value(root.children[f"you_bulls_{self.round}"], bulls)
    #         insert_value(root.children[f"you_cows_{self.round}"], cows)
    #         if self.op_bulls.get() == "4":
    #             if bulls == "4":
    #                 self.end_game("draw")
    #                 return
    #             self.end_game("opponent")
    #             return
    #         elif bulls == "4":
    #             self.end_game("you")
    #             return
    #         self.round += 1
    #     draw_round(self.round)
    #     self.you_guess = root.children[f"you_guess_{self.round}"]
    #     self.op_bulls = root.children[f"op_bulls_{self.round}"]
    #     self.op_cows = root.children[f"op_cows_{self.round}"]
    #     self.you_guess.config(state=NORMAL)
    #     self.you_guess.focus_set()
    #     root.children["btn_send"].config(command=self.set_guesses)
    #     handle_game_key(self.set_guesses, self.you_guess)
    #
    # def polling(self, next_function):
    #     if not self.polling_started:
    #         root.children["btn_send"].config(state=DISABLED)
    #         if isinstance(self.interface, multiplayer.Client):
    #             threading.Thread(
    #                 target=self.interface.send_data, args=(self.data,)
    #             ).start()
    #             threading.Thread(target=self.interface.get_data).start()
    #         else:
    #             threading.Thread(target=self.interface.get_data).start()
    #             threading.Thread(
    #                 target=self.interface.send_data, args=(self.data,)
    #             ).start()
    #         self.polling_started = True
    #         self.polling(next_function)
    #     elif not self.interface.connected:
    #         messagebox.showinfo(
    #             "Lost connection",
    #             "There are some problems with connection, or your opponent has left.",
    #         )
    #         self.end_game("nobody")
    #     elif not (self.interface.sent and self.interface.received):
    #         root.after(1000, self.polling, next_function)
    #     else:
    #         root.children["btn_send"].config(state=NORMAL)
    #         self.polling_started = False
    #         next_function()
    #
    # def end_game(self, who_win):
    #     for entry in (self.you_guess, self.op_bulls, self.op_cows):
    #         if entry:
    #             entry.config(state=DISABLED)
    #     root.children["btn_send"].config(state=DISABLED)
    #     if who_win == "nobody":
    #         messagebox.showinfo("Attention", "You opponent has left")
    #         return
    #     root.children["lbl_player_won"].config(text=who_win)
    #     cur_time = datetime.now()
    #     root.children["lbl_time_ended"].config(text=cur_time.strftime("%H:%M:%S"))
    #
    #     duration = time.strftime(
    #         "%Mm%Ss", time.gmtime((cur_time - self.start_time).total_seconds())
    #     )
    #     root.children["lbl_duration"].config(text=duration)
    #     if who_win == "opponent":
    #         messagebox.showinfo("Defeat", "You lost.")
    #     elif who_win == "you":
    #         messagebox.showinfo("Win", "You won.")
    #     else:
    #         messagebox.showinfo("Draw", "Draw :)")


def draw_join_game():
    def validate_ip_address(act, ind, new_val, old_val):
        # при выделении участка и заменой его - ошибки
        # отсутствие обработки ctrl команд
        val = get_val_before_validate(act, ind, new_val, old_val)
        nums = val.split(".")
        if len(nums) <= 4:
            for num in nums:
                if not num:
                    continue
                if not num.isdigit():
                    break
                if not 0 <= int(num) <= 255:
                    break
            else:
                return True
        return False

    def entry_ip_handle(entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, END)
            entry.config(fg="black")
        elif entry.get() == "":
            entry.insert(0, default_text)
            entry.config(fg="grey")

    frame = root.nametowidget(".frame_local_game")
    btn_connect = frame.nametowidget("btn_create_game")
    btn_connect.config(text="Connect")
    frame.nametowidget("btn_join_game").destroy()

    entry_room = Entry(frame, fg="grey", validate="key", name="entry_name", width=5)
    entry_room.config(validatecommand=decor_register(entry_room, validate_ip_address))
    room_example = "6666"
    entry_room.insert(0, room_example)
    for sequence in ("<FocusIn>", "<FocusOut>"):
        entry_room.bind(sequence, lambda event: entry_ip_handle(entry_room, room_example))
    handle_game_key(MultiplayerGame, entry_room)
    frame_name = Frame(frame, name="frame_room")
    Label(frame_name, text="Room id", pady=5, padx=5).pack(side=LEFT)
    Entry(frame_name, name="entry_name", width=5).pack(side=RIGHT)
    frame_name.pack(before=btn_connect)


def draw_local_game(old_frame):
    old_frame.destroy()
    frame = Frame(root, name="frame_local_game")
    frame.pack()
    frame_name = Frame(frame, name="frame_name")
    frame_name.pack()
    Label(frame_name, text="Name", pady=5, padx=5).pack(side=LEFT)
    Entry(frame_name, name="entry_name", width=10).pack(side=RIGHT)
    Button(
        frame,
        text="Create game",
        command=MultiplayerGame,
        name="btn_create_game",
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
    Label(root, text="Time started   ", pady=5).grid(row=3, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_time_started").grid(row=3, column=12)
    Label(root, text="Time ended", pady=5).grid(row=4, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_time_ended").grid(row=4, column=12)
    Label(root, text="Duration", pady=5).grid(row=5, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_duration").grid(row=5, column=12)

    Label(root, text=" ", pady=5).grid(row=6, column=11)

    Label(root, text="Player won", pady=5).grid(row=7, column=11, stick="w")
    Label(root, text="?", pady=5, name="lbl_player_won").grid(row=7, column=12)

    Label(root, text=" ", pady=5).grid(row=8, column=11)

    Button(
        root,
        text="Main menu",
        command=lambda: pop_up(
            yes=draw_main_menu, text="Are you sure, that you want to leave the game?"
        ),
        name="btn_main_menu",
    ).grid(row=10, column=11, columnspan=2)
    Button(root, text="Quit", command=_quit, name="btn_quit").grid(
        row=11, column=11, columnspan=2
    )


def draw_round(n, frame=root):
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


def handle_game_key(func, *entry_fields):
    def inner_func(event):
        if event.char == "\r":
            func()
        elif root.focus_get() not in entry_fields:
            entry_fields[0].focus_set()
            root.after(1, entry_fields[0].insert, END, event.char)

    root.bind("<Key>", inner_func)


def insert_value(entry_form, value):
    if entry_form:
        entry_form.config(state=NORMAL)
        entry_form.insert(0, value)
        entry_form.config(state=DISABLED)


def _quit(interface=None):
    if interface:
        threading.Thread(target=interface.close).start()
    root.after(50, root.quit)


def main():
    root.title("Bulls and cows!")
    root.geometry("530x360")

    draw_main_menu()
    root.mainloop()


if __name__ == "__main__":
    utils.init_logger()
    main()
