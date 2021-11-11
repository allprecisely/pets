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

import guesser
import multiplayer

root = Tk()
WAIT_CONNECTION_TIME = 60000  # ms


def guess(generator):
    def get_new_guess():
        nonlocal current_guess, guess_counter, widgets
        c = widgets[3].get()
        b = widgets[2].get()
        if not c:
            widgets[3].insert(0, "0")
        if not b:
            widgets[2].insert(0, "0")
        widgets[2]["state"] = DISABLED
        widgets[3]["state"] = DISABLED
        widgets[4]["state"] = DISABLED

        current_guess = generator.send(f"{b or 0} {c or 0}")
        if not current_guess:
            messagebox.showinfo("Неверные данные!")
            for widget in widgets:
                widget.destroy()
            widgets = draw_round(guess_counter)
            return
        if len(current_guess) > 4:
            messagebox.showinfo(
                f"Победа за {current_guess[4:]} попыток",
                f"Ваше число: {current_guess[:4]}",
            )
            return
        guess_counter += 1

        widgets = draw_round(guess_counter)

    guess_counter = 1
    current_guess = next(generator)
    widgets = draw_round(guess_counter)


def answer(game_field, generator, rounds):
    b, c = rounds[-1]["op_bulls"], rounds[-1]["op_cows"]
    if not (b.get() or c.get()):
        messagebox.showinfo("Error", "Fields cannot be empty")
        return
    current_guess = generator.send(f"{b.get()} {c.get()}")
    if not current_guess:
        messagebox.showinfo("Error", "Data you sent are not valid")
        return

    if len(current_guess) > 4:
        messagebox.showinfo(
            f"Opponent won in {current_guess[4:]} rounds",
            f"Your number: {current_guess[:4]}",
        )
        return

    insert_value(rounds[-1]["op_guess"], next(guesser))
    rounds[-1]["you_guess"].config(state=DISABLED)
    rounds[-1]["op_cows"].config(state=NORMAL)
    rounds[-1]["op_bulls"].config(state=NORMAL)


def guess(game_field, generator, rounds):
    rounds.append(draw_round(len(rounds)))
    rounds[-1]["you_guess"].config(state=NORMAL)
    rounds[-1]["you_guess"].focus_set()
    insert_value(rounds[-1]["op_guess"], next(generator))
    rounds[-1]["you_guess"].config(state=DISABLED)
    rounds[-1]["op_cows"].config(state=NORMAL)
    rounds[-1]["op_bulls"].config(state=NORMAL)
    game_field["btn_send"].config(command=lambda: answer(game_field, generator, rounds))


def handle_single_game_key(event, generator, rounds):
    focus = root.focus_get()
    print(focus)
    if not focus:
        rounds[-1]["you_guess"].focus_set()
        root.after(1, rounds[-1]["you_guess"].insert, END, event.char)
    if event.char == "\r":
        guess(generator, rounds)


def single_game():
    for widget in root.winfo_children():
        widget.destroy()
    rounds = []
    generator = guesser.graphical_main()
    game_field = draw_game_field()
    game_field["btn_send"].config(command=lambda: guess(generator, rounds))
    root.bind(
        "<Key>",
        lambda event: handle_single_game_key(event, guesser.graphical_main(), rounds),
    )


def insert_value(entry_form, value):
    if entry_form:
        entry_form.config(state=NORMAL)
        entry_form.insert(0, value)
        entry_form.config(state=DISABLED)


class MainGame:
    """
    Класс, который описывает саму игру
    """

    fields = ("you_guess", "you_bulls", "you_cows", "op_guess", "op_bulls", "op_cows")

    def __init__(self, interface, game_field):
        # self.rounds_frame = Frame(root)
        # self.rounds_frame.grid(row=2, column=0, columnspan=9)
        self.rounds = {0: {}}
        self.interface = interface
        self.game_field = game_field
        self.game_field["btn_send"].config(command=self.send)
        self.game_field["btn_quit"].config(command=self.quit)
        self.start_time = datetime.now()
        self.game_field["lbl_time_started"].config(
            text=self.start_time.strftime("%H:%M:%S")
        )
        self.send_entries = []
        self.thread = None

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
            # pop_up(
            #     yes=self.wait_new_game,
            #     no=self.end_game,
            #     text="You lost. Do you want a revenge?",
            #     title="Defeat",
            # )
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

    # тут можно доорганизовать логику новой игры
    # def wait_new_game(self):
    #     if not self.thread:
    #         Label(root, text="Waiting your opponent...").grid(
    #             row=self.round + 2, column=0, colomnspan=5
    #         )
    #         self.game_field["btn_new_game"].config(text="Revenge!", state=DISABLED)
    #         threading.Thread(target=lambda: self.interface.send_data("y")).start()
    #         self.thread = threading.Thread(target=self.interface.get_data)
    #         self.thread.start()
    #     if self.thread.is_alive():
    #         root.after(250, self.wait_new_game)
    #     elif self.interface.data == 'y':
    #         self.rounds_frame.destroy()
    #         self.rounds = {0: {form: EntryCap() for form in self.fields}}
    #
    #     else:
    #         messagebox.showinfo('Reject', "Opponent doesn't want to play")
    #
    #
    #
    # def end_game(self):
    #     self.game_field["btn_new_game"].config(
    #         text="Revenge!", state=NORMAL, command=self.wait_new_game
    #     )
    #     threading.Thread(target=lambda: self.interface.send_data("n")).start()

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

    def quit(self):
        self.interface.close()
        root.quit()


def multiplayer_new_game(interface):
    for widget in root.winfo_children():
        widget.destroy()
    game_field = draw_game_field()

    if isinstance(interface, multiplayer.Server):
        Label(root, text="P").grid(row=11, column=0)
        Label(root, text=interface.port).grid(row=11, column=1)
        messagebox.showinfo("Game started", "Your turn. Guess...")
        MainGame(interface, game_field).prepare_send()
    else:
        game_field["btn_send"].config(state=DISABLED)
        MainGame(interface, game_field).recv()


def check_status(interface, lbl, counter, *active_btns):
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


def quit_after_connection(interface):
    interface.close()
    root.quit()


def start_game(*active_btns, btn_quit=None, entry_ip=None):
    if entry_ip:
        port = entry_ip.get()
        interface = multiplayer.Client(port)
    else:
        interface = multiplayer.Server()

    if btn_quit:
        btn_quit.config(command=lambda: quit_after_connection(interface))

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


def entry_handle(entry, default_text):
    if entry.get() == default_text:
        entry.delete(0, END)
        entry.config(fg="black")
    elif entry.get() == "":
        entry.insert(0, default_text)
        entry.config(fg="grey")


def handle_keys_join_game(event, entry_ip, active_button):
    if root.focus_get() != entry_ip and event.char in "0123456789.":
        entry_ip.focus_set()
        root.after(1, entry_ip.insert, END, event.char)
    if event.char == "\r":
        start_game(active_button, entry_ip=entry_ip)


def get_val_before_validate(act, ind, new_val, old_val):
    if act == "0":
        return old_val[: int(ind)] + old_val[int(ind) + len(new_val) :]
    else:
        return old_val[: int(ind)] + new_val + old_val[int(ind) :]


def validate_ip_address(act, ind, new_val, old_val):
    # это просто что за жесть?))))
    # осталась проблема, что при выделении участка и заменой его - происходит хрень)
    # отсутствие обработки ctrl комманд
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


def decor_register(widget, func):
    return widget.register(func), "%d", "%i", "%S", "%s"


def join_game(old_frame):
    old_frame.destroy()
    entry_ip = Entry(
        root,
        fg="grey",
        validate="key",
    )
    entry_ip.config(validatecommand=decor_register(entry_ip, validate_ip_address))
    entry_ip_default_text = "192.168.0.1"
    entry_ip.insert(0, entry_ip_default_text)
    entry_ip.bind(
        "<FocusIn>", lambda event: entry_handle(entry_ip, entry_ip_default_text)
    )
    entry_ip.bind(
        "<FocusOut>", lambda event: entry_handle(entry_ip, entry_ip_default_text)
    )
    active_button = Button(
        root,
        text="Connect",
        command=lambda: start_game(active_button, entry_ip=entry_ip),
    )
    root.bind(
        "<Key>", lambda event: handle_keys_join_game(event, entry_ip, active_button)
    )
    btns = [
        entry_ip,
        active_button,
        Button(root, text="Quit", command=root.quit),
    ]
    for btn in btns:
        btn.pack()


def local_game(old_frame):
    old_frame.destroy()
    frame_local_game = Frame(root)
    join_btn = Button(
        frame_local_game,
        text="Join game",
        command=lambda: join_game(frame_local_game),
    )
    create_button_btn = Button(
        frame_local_game,
        text="Create game",
        command=lambda: start_game(join_btn, create_button_btn),
    )
    btns = [
        create_button_btn,
        join_btn,
        Button(frame_local_game, text="Quit", command=root.quit),
    ]
    for btn in [frame_local_game, *btns]:
        btn.pack()


def draw_main_menu():
    for widget in root.winfo_children():
        widget.destroy()
    Label(
        root, text="BULLS & COWS", font=("Arial", 30), height=3, anchor="s", pady=20
    ).pack()
    frame_main_menu = Frame(root)
    btns = [
        Button(frame_main_menu, text="Single game", command=single_game),
        Button(
            frame_main_menu,
            text="Local game",
            command=lambda: local_game(frame_main_menu),
        ),
        Button(frame_main_menu, text="Quit", command=root.quit),
    ]
    for btn in [frame_main_menu, *btns]:
        btn.pack()


def pop_up(yes=None, no=None, text="Are you sure?", title="Attention!"):
    def inner(func):
        if func:
            func()
        top_level.destroy()

    top_level = Toplevel(root)
    top_level.title = title
    Label(top_level, text=text).grid(row=0, column=0, columnspan=2)
    Button(top_level, text="Yes", command=lambda: inner(yes)).grid(row=1, column=0)
    Button(top_level, text="No", command=lambda: inner(no)).grid(row=1, column=1)


def draw_game_field():
    game_field = {}
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

    game_field["btn_send"] = Button(root, text="Send")
    game_field["btn_send"].grid(row=0, column=11, columnspan=2, rowspan=2)

    Label(root, text="STATISTICS", pady=5).grid(row=2, column=11, columnspan=2)
    Label(root, text="Time started   ", pady=5).grid(row=3, column=11, stick="w")
    game_field["lbl_time_started"] = Label(root, text="?", pady=5)
    game_field["lbl_time_started"].grid(row=3, column=12)
    Label(root, text="Time ended", pady=5).grid(row=4, column=11, stick="w")
    game_field["lbl_time_ended"] = Label(root, text="?", pady=5)
    game_field["lbl_time_ended"].grid(row=4, column=12)
    Label(root, text="Duration", pady=5).grid(row=5, column=11, stick="w")
    game_field["lbl_duration"] = Label(root, text="?", pady=5)
    game_field["lbl_duration"].grid(row=5, column=12)

    Label(root, text=" ", pady=5).grid(row=6, column=11)

    Label(root, text="Player won", pady=5).grid(row=7, column=11, stick="w")
    game_field["lbl_player_won"] = Label(root, text="?", pady=5)
    game_field["lbl_player_won"].grid(row=7, column=12)

    Label(root, text=" ", pady=5).grid(row=8, column=11)

    game_field["btn_new_game"] = Button(
        root,
        text="New game",
        command=multiplayer_new_game,
        state=DISABLED,
    )
    game_field["btn_new_game"].grid(row=9, column=11, columnspan=2)
    Button(
        root,
        text="Main menu",
        command=lambda: pop_up(
            yes=draw_main_menu, text="Are you sure, that you want to leave the game?"
        ),
    ).grid(row=10, column=11, columnspan=2)
    game_field["btn_quit"] = Button(root, text="Quit", command=root.quit)
    game_field["btn_quit"].grid(row=11, column=11, columnspan=2)
    return game_field


def validate_guess(act, ind, new_val, old_val):
    val = get_val_before_validate(act, ind, new_val, old_val)
    if val.isdigit() and len(val) <= 4:
        return len(val) == len(set(val))
    return False


def validate_digit(act, ind, new_val, old_val):
    if not old_val:
        return new_val.is_digit()
    return False


def draw_round(n, frame=root):
    Label(frame, text=str(n), pady=5).grid(row=n + 1, column=0)
    Label(frame, text=str(n), pady=5).grid(row=n + 1, column=6)
    dct = {
        "you_guess": Entry(frame, width=5, state=DISABLED),
        "you_bulls": Entry(frame, width=2, state=DISABLED),
        "you_cows": Entry(frame, width=2, state=DISABLED),
        "op_guess": Entry(frame, width=5, state=DISABLED),
        "op_bulls": Entry(frame, width=2, state=DISABLED),
        "op_cows": Entry(frame, width=2, state=DISABLED),
    }
    for key, entry in dct.items():
        if key.endswith("guess"):
            entry.config(
                validate="key", validatecommand=decor_register(entry, validate_guess)
            )
        else:
            entry.config(
                validate="key", validatecommand=decor_register(entry, validate_digit)
            )
    dct["you_guess"].grid(row=n + 1, column=1)
    dct["you_bulls"].grid(row=n + 1, column=2)
    dct["you_cows"].grid(row=n + 1, column=3)
    dct["op_guess"].grid(row=n + 1, column=7)
    dct["op_bulls"].grid(row=n + 1, column=8)
    dct["op_cows"].grid(row=n + 1, column=9)
    return dct


def main():
    root.title("Bulls and cows!")
    root.geometry("530x360")

    draw_main_menu()

    root.mainloop()


if __name__ == "__main__":
    main()
