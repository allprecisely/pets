"""
Хочется еще наверное одновременной игры
кнопка назад
начать новую партию
валидацию полей
единый класс
"""
from datetime import datetime
import time
import threading
from tkinter import *
from tkinter import messagebox

import guesser2 as guesser
import multiplayer

root = Tk()
WAIT_CONNECTION_TIME = 60000  # ms


class SingleGame:
    def __init__(self):
        for widget in root.winfo_children():
            widget.destroy()
        self.rounds = []
        self.generator = guesser.graphical_main()
        self.game_field = draw_game_field()
        self.op_guess = None
        self.you_bulls, self.you_cows = None, None
        self.op_bulls, self.op_cows = None, None
        self.guess()

    def answer(self):
        if not (self.op_bulls.get() and self.op_cows.get()):
            messagebox.showinfo("Error", "Fields cannot be empty")
            return
        is_correct = self.generator.send(f"{self.op_bulls.get()} {self.op_cows.get()}")
        if not is_correct:
            messagebox.showinfo("Error", "Data you sent are not valid")
            return
        self.op_guess = next(self.generator)
        self.op_bulls.config(state=DISABLED)
        self.op_cows.config(state=DISABLED)
        insert_value(self.rounds[-1]["you_bulls"], self.you_bulls)
        insert_value(self.rounds[-1]["you_cows"], self.you_cows)
        self.guess()

    def get_guess_back(self):
        player_guess = self.rounds[-1]["you_guess"].get()
        if len(player_guess) < 4:
            messagebox.showinfo("Error", "There should be 4 digits")
            return
        self.rounds[-1]["you_guess"].config(state=DISABLED)
        if not self.op_guess:
            self.op_guess = next(self.generator)
        self.you_bulls, self.you_cows = self.generator.send(player_guess).split()
        insert_value(self.rounds[-1]["op_guess"], self.op_guess)
        self.op_bulls.config(state=NORMAL)
        self.op_cows.config(state=NORMAL)
        self.game_field["btn_send"].config(command=self.answer)
        handle_game_key(self.answer, self.op_bulls, self.op_cows)

    def guess(self):
        self.rounds.append(draw_round(len(self.rounds) + 1))
        self.op_bulls, self.op_cows = (
            self.rounds[-1]["op_bulls"],
            self.rounds[-1]["op_cows"],
        )
        self.rounds[-1]["you_guess"].config(state=NORMAL)
        self.rounds[-1]["you_guess"].focus_set()
        self.game_field["btn_send"].config(command=self.get_guess_back)
        handle_game_key(self.get_guess_back, self.rounds[-1]["you_guess"])


class MultiplayerGame:
    """
    Класс, который описывает саму игру
    """

    def __init__(self, interface, game_field):
        self.rounds = {0: {}}
        self.interface = interface
        self.game_field = game_field
        self.game_field["btn_send"].config(command=self.send)
        self.game_field["btn_main_menu"].config(command=lambda: _quit(interface))
        self.game_field["btn_quit"].config(command=lambda: _quit(interface))
        self.start_time = datetime.now()
        self.game_field["lbl_time_started"].config(
            text=self.start_time.strftime("%H:%M:%S")
        )
        self.send_entries = []
        self.thread = None

    def create_connection(self):
        pass
        # if entry_ip:
        #     port = entry_ip.get()
        #     interface = multiplayer.Client(port)
        # else:
        #     interface = multiplayer.Server()
        #
        # if btn_quit:
        #     btn_quit.config(command=lambda: _quit(interface))
        # if btn_main_menu:
        #     btn_main_menu.config(command=lambda: draw_main_menu(interface))
        #
        # for btn in active_btns:
        #     btn["state"] = DISABLED
        # lbl = Label(root, text=interface.connect_text, pady=5)
        # lbl.pack()
        #
        # thread_connection = threading.Thread(target=interface.connect, daemon=True)
        # check_status(
        #     interface,
        #     lbl,
        #     WAIT_CONNECTION_TIME,
        #     *active_btns,
        # )
        # thread_connection.start()

    def prepare_send(self):
        if self.interface.data:
            op_guess, you_bulls, you_cows = self.interface.data.split("\n")
            if you_bulls == "4":
                self.end_game("you")
                return
        self.game_field["btn_send"].config(state=NORMAL)
        rnd = len(self.rounds)
        self.rounds[rnd] = draw_round(rnd)
        tmp_dct = self.rounds[rnd - 1]
        if isinstance(self.interface, multiplayer.Client):
            tmp_dct = self.rounds[rnd]

        if self.interface.data:
            insert_value(self.rounds[rnd - 1].get("you_bulls"), you_bulls)
            insert_value(self.rounds[rnd - 1].get("you_cows"), you_cows)
            insert_value(tmp_dct.get("op_guess"), op_guess)

        self.send_entries = [
            self.rounds[rnd]["you_guess"],
            tmp_dct.get("op_bulls"),
            tmp_dct.get("op_cows"),
        ]
        for entry_form in self.send_entries:
            entry_form.config(state=NORMAL)

    def send(self):
        data = "\n".join(entry.get() for entry in self.send_entries)
        threading.Thread(target=lambda: self.interface.send_data(data)).start()
        for entry in self.send_entries:
            entry.config(state=DISABLED)
        self.game_field["btn_send"].config(state=DISABLED)
        if self.send_entries[1].get() == "4":
            self.end_game("opponent")
        else:
            self.recv()

    def recv(self):
        if not self.thread:
            self.thread = threading.Thread(target=self.interface.get_data)
            self.thread.start()
        if self.thread.is_alive():
            root.after(250, self.recv)
        elif self.interface.connected:
            self.thread = None
            self.prepare_send()
        else:
            messagebox.showinfo(
                "Lost connection",
                "There are some problems with connection, or your opponent has left.",
            )

    def end_game(self, who_win):
        self.game_field["lbl_player_won"].config(text=who_win)
        cur_time = datetime.now()
        self.game_field["lbl_time_ended"].config(text=cur_time.strftime("%H:%M:%S"))

        duration = time.strftime(
            "%Mm%Ss", time.gmtime((cur_time - self.start_time).total_seconds())
        )
        self.game_field["lbl_duration"].config(text=duration)
        if who_win == "opponent":
            messagebox.showinfo("Defeat", "You lost.")
        else:
            messagebox.showinfo("Win", "You won.")


def multiplayer_new_game(interface):
    for widget in root.winfo_children():
        widget.destroy()
    game_field = draw_game_field()

    if isinstance(interface, multiplayer.Server):
        Label(root, text="H").grid(row=11, column=0)
        Label(root, text=interface.ip_address).grid(row=11, column=1, columnspan=4)
        messagebox.showinfo("Game started", "Your turn. Guess...")
        MultiplayerGame(interface, game_field).prepare_send()
    else:
        game_field["btn_send"].config(state=DISABLED)
        MultiplayerGame(interface, game_field).recv()


def check_status(interface, lbl, counter, *active_btns):
    if interface.closed:
        return
    if not counter or getattr(interface, "try_another_server", False):
        threading.Thread(target=interface.close).start()
        messagebox.showinfo("Error", interface.error_text)
        lbl.destroy()
        for btn in active_btns:
            btn["state"] = ACTIVE
    elif not interface.connected:
        root.after(
            250,
            check_status,
            interface,
            lbl,
            counter - 250,
            *active_btns,
        )
    else:
        multiplayer_new_game(interface)


def start_game(*active_btns, btn_quit=None, btn_main_menu=None, entry_ip=None):
    if entry_ip:
        port = entry_ip.get()
        interface = multiplayer.Client(port)
    else:
        interface = multiplayer.Server()

    if btn_quit:
        btn_quit.config(command=lambda: _quit(interface))
    if btn_main_menu:
        btn_main_menu.config(command=lambda: draw_main_menu(interface))

    for btn in active_btns:
        btn["state"] = DISABLED
    lbl = Label(root, text=interface.connect_text, pady=5)
    lbl.pack()

    thread_connection = threading.Thread(target=interface.connect, daemon=True)
    check_status(
        interface,
        lbl,
        WAIT_CONNECTION_TIME,
        *active_btns,
    )
    thread_connection.start()


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
    btn_connect.config(text='Connect')
    frame.nametowidget("btn_join_game").destroy()

    entry_ip = Entry(frame, fg="grey", validate="key", name="entry_ip")
    entry_ip.config(validatecommand=decor_register(entry_ip, validate_ip_address))
    ip_example = "192.168.0.1"
    entry_ip.insert(0, ip_example)
    for sequence in ("<FocusIn>", "<FocusOut>"):
        entry_ip.bind(sequence, lambda event: entry_ip_handle(entry_ip, ip_example))
    handle_game_key(start_game, entry_ip)
    entry_ip.pack(before=btn_connect)


def draw_local_game(old_frame):
    old_frame.destroy()
    frame = Frame(root, name='frame_local_game')
    frame.pack()
    Button(frame, text="Create game", command=start_game, name='btn_create_game').pack()
    Button(frame, text="Join game", command=draw_join_game, name='btn_join_game').pack()
    Button(
        frame,
        text="Main menu",
        command=draw_main_menu,
        name='btn_main_menu'
    ).pack()
    Button(frame, text="Quit", command=_quit, name='btn_quit').pack()


def draw_main_menu(interface=None):
    if interface:
        interface.close()
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

    Button(root, text="Send", name='btn_send').grid(
        row=0, column=11, columnspan=2, rowspan=2
    )

    Label(root, text="STATISTICS", pady=5).grid(row=2, column=11, columnspan=2)
    Label(root, text="Time started   ", pady=5).grid(row=3, column=11, stick="w")
    Label(root, text="?", pady=5, name='lbl_time_started').grid(row=3, column=12)
    Label(root, text="Time ended", pady=5).grid(row=4, column=11, stick="w")
    Label(root, text="?", pady=5, name='lbl_time_ended').grid(row=4, column=12)
    Label(root, text="Duration", pady=5).grid(row=5, column=11, stick="w")
    Label(root, text="?", pady=5, name='lbl_duration').grid(row=5, column=12)

    Label(root, text=" ", pady=5).grid(row=6, column=11)

    Label(root, text="Player won", pady=5).grid(row=7, column=11, stick="w")
    Label(root, text="?", pady=5, name='lbl_player_won').grid(row=7, column=12)

    Label(root, text=" ", pady=5).grid(row=8, column=11)

    Button(
        root,
        text="New game",
        command=multiplayer_new_game,
        state=DISABLED,
        name='btn_new_game'
    ).grid(row=9, column=11, columnspan=2)
    Button(
        root,
        text="Main menu",
        command=lambda: pop_up(
            yes=draw_main_menu, text="Are you sure, that you want to leave the game?"
        ),
        name='btn_main_menu',
    ).grid(row=10, column=11, columnspan=2)
    Button(root, text="Quit", command=_quit, name='btn_quit').grid(row=11, column=11, columnspan=2)


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
        1: Entry(frame, width=5, name=f'you_guess_{n}'),
        3: Entry(frame, width=2, name=f'you_bulls_{n}'),
        7: Entry(frame, width=2, name=f'you_cows_{n}'),
        8: Entry(frame, width=5, name=f'op_guess_{n}'),
        9: Entry(frame, width=2, name=f'op_bulls_{n}'),
        2: Entry(frame, width=2, name=f'op_cows_{n}'),
    }
    for column, entry in entries.items():
        validate_func = validate_guess if column in (1, 8) else validate_digit
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
        interface.close()
    root.quit()


def main():
    root.title("Bulls and cows!")
    root.geometry("530x360")

    draw_main_menu()
    root.mainloop()


if __name__ == "__main__":
    main()
