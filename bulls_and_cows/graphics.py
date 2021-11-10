import socket
import time
import threading
from tkinter import *
from tkinter import messagebox

import guesser
import multiplayer

root = Tk()
WAIT_CONNECTION_TIME = 60000  # ms


def draw_a_string(guess_counter, current_guess, foo):
    widgets = [
        Label(root, text=guess_counter, pady=5),
        Label(
            root,
            text=current_guess,
            pady=5,
        ),
        Entry(root),
        Entry(root),
        Button(root, text="Answer!", command=foo),
    ]
    for i, widget in enumerate(widgets):
        widget.grid(row=guess_counter + 2, column=i, stick="w")

    return widgets


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
            widgets = draw_a_string(guess_counter, current_guess, get_new_guess)
            return
        if len(current_guess) > 4:
            messagebox.showinfo(
                f"Победа за {current_guess[4:]} попыток",
                f"Ваше число: {current_guess[:4]}",
            )
            return
        guess_counter += 1

        widgets = draw_a_string(guess_counter, current_guess, get_new_guess)

    guess_counter = 1
    current_guess = next(generator)
    widgets = draw_a_string(guess_counter, current_guess, get_new_guess)


def new_game():
    for widget in root.winfo_children():
        widget.destroy()
    round = 1
    btn_send = draw_game_field()
    btn_send["command"] = guess
    root.bind("<Key>", btn_send)
    dct = draw_round(round)
    generator = guesser.graphical_main()
    dct["op_guess"]["state"] = NORMAL
    dct["op_guess"].insert(0, next(generator))
    dct["op_guess"]["state"] = DISABLED


class Tmp:
    a = ""

    def get(self):
        return ""

    def __getitem__(self, item):
        return self.a


def multiplayer_guess(conn, last_dct, new_dct, btn_send, rnd):
    data = "\n".join(
        [
            new_dct["you_guess"].get(),
            last_dct.get("op_bulls", Tmp()).get() or "",
            last_dct.get("op_cows", Tmp()).get() or "",
        ]
    ).encode("utf8")
    conn.send(data)
    new_dct["you_guess"]["state"] = DISABLED
    last_dct.get("op_bulls", {"state": ""})["state"] = DISABLED
    last_dct.get("op_cows", {"state": ""})["state"] = DISABLED
    time.sleep(1)
    rcv_data = conn.recv(1024).decode("utf8").split("\n")
    for i, btn in enumerate(["op_guess", "you_bulls", "you_cows"]):
        new_dct[btn]["state"] = NORMAL
        new_dct[btn].insert(0, rcv_data[i])
        new_dct[btn]["state"] = DISABLED
    new_dct["op_bulls"]["state"] = NORMAL
    new_dct["op_cows"]["state"] = NORMAL
    dct = draw_round(rnd)
    dct["you_guess"]["state"] = NORMAL
    btn_send["command"] = lambda: multiplayer_guess(
        conn, new_dct, dct, btn_send, rnd + 1
    )


#
#
# def press_key(event, conn, dct, btn_send, rnd):
#     if event.char == "\r":
#         multiplayer_guess(conn, dct, btn_send, rnd)


def multiplayer_new_game(conn, sock=None, port=None):
    for widget in root.winfo_children():
        widget.destroy()
    rnd = 1
    btn_send = draw_game_field(conn, sock)
    last_dct = draw_round(rnd)

    if port:
        Label(root, text="P").grid(row=11, column=0)
        Label(root, text=str(port)).grid(row=11, column=1)
        messagebox.showinfo("Game started", "Your turn. Guess...")
        btn_send["command"] = lambda: multiplayer_guess(
            conn, {}, last_dct, btn_send, rnd + 1
        )
        # root.bind("<Key>", lambda event: press_key(event, conn, dct, btn_send, rnd + 1))
        last_dct["you_guess"]["state"] = NORMAL
    else:
        rcv_data = conn.recv(1024).decode("utf8").split("\n")
        messagebox.showinfo("Game started", "Your turn. Guess...")
        for i, btn in enumerate(["op_guess", "you_bulls", "you_cows"]):
            last_dct["op_guess"]["state"] = NORMAL
            last_dct[btn].insert(0, rcv_data[i])
            last_dct["op_guess"]["state"] = DISABLED
        last_dct["you_guess"]["state"] = NORMAL
        last_dct["op_bulls"]["state"] = NORMAL
        last_dct["op_cows"]["state"] = NORMAL
        btn_send["command"] = lambda: multiplayer_guess(
            conn,
            last_dct,
            draw_round(rnd),
            btn_send,
            rnd + 1,
        )
        # root.bind(
        #     "<Key>",
        #     lambda event: press_key(
        #         event,
        #         conn,
        #         draw_round(rnd),
        #         btn_send,
        #         rnd + 1,
        #     ),
        # )


def check_status(interface, port_entry, lbl, counter, *active_btns):
    if not counter or getattr(interface, 'try_another_server'):
        threading.Thread(target=interface.close).start()
        messagebox.showinfo("Ошибка", interface.error_text)
        if port_entry:
            port_entry.delete(0, LAST)
        lbl.destroy()
        for btn in active_btns:
            btn["state"] = ACTIVE
    elif not interface.connected:
        root.after(
            250,
            check_status,
            interface,
            port_entry,
            lbl,
            counter - 250,
            *active_btns,
        )
    else:
        multiplayer_new_game(interface)


def start_game(*active_btns, port_entry=None):
    if port_entry:
        port = int(port_entry.get())
        interface = multiplayer.Client(port)
    else:
        interface = multiplayer.Server()

    for btn in active_btns:
        btn["state"] = DISABLED
    lbl = Label(root, text=interface.connect_text, pady=5)
    lbl.pack()

    thread_connection = threading.Thread(target=interface.connect, daemon=True)
    root.after(
        250,
        check_status,
        interface,
        port_entry,
        lbl,
        WAIT_CONNECTION_TIME,
        *active_btns,
    )
    thread_connection.start()


def join_game(old_frame):
    old_frame.destroy()
    port_entry = Entry(root)
    port_entry.insert(0, str(multiplayer.PORT))
    active_button = Button(
        root,
        text="Connect",
        command=lambda: start_game(active_button, port_entry=port_entry),
    )
    btns = [
        port_entry,
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


def main_menu():
    for widget in root.winfo_children():
        widget.destroy()
    Label(
        root, text="BULLS & COWS", font=("Arial", 30), height=3, anchor="s", pady=20
    ).pack()
    frame_main_menu = Frame(root)
    btns = [
        Button(frame_main_menu, text="New game", command=new_game),
        Button(
            frame_main_menu,
            text="Local game",
            command=lambda: local_game(frame_main_menu),
        ),
        Button(frame_main_menu, text="Quit", command=root.quit),
    ]
    for btn in [frame_main_menu, *btns]:
        btn.pack()


def send():
    pass


def quit_game(conn=None, sock=None):
    if conn:
        conn.close()
    if sock:
        sock.close()
    root.quit()


def draw_game_field(conn=None, sock=None):
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

    btn_send = Button(root, text="Send", command=send)
    btn_send.grid(row=0, column=11, columnspan=2, rowspan=2)

    Label(root, text="STATISTICS", pady=5).grid(row=2, column=11, columnspan=2)
    Label(root, text="Time started   ", pady=5).grid(row=3, column=11, stick="w")
    Label(root, text=time.strftime("%H:%M"), pady=5).grid(row=3, column=12)
    Label(root, text="Time ended", pady=5).grid(row=4, column=11, stick="w")
    Label(root, text="?", pady=5).grid(row=4, column=12)
    Label(root, text="Duration", pady=5).grid(row=5, column=11, stick="w")
    Label(root, text="?", pady=5).grid(row=5, column=12)

    Label(root, text=" ", pady=5).grid(row=6, column=11)

    Label(root, text="Player won", pady=5).grid(row=7, column=11, stick="w")
    Label(root, text="?", pady=5).grid(row=7, column=12)

    Label(root, text=" ", pady=5).grid(row=8, column=11)

    Button(root, text="New game", command=new_game).grid(row=9, column=11, columnspan=2)
    Button(root, text="Main menu", command=main_menu).grid(
        row=10, column=11, columnspan=2
    )
    Button(root, text="Quit", command=lambda: quit_game(conn, sock)).grid(
        row=11, column=11, columnspan=2
    )
    return btn_send


def draw_round(n):
    Label(root, text=str(n), pady=5).grid(row=n + 1, column=0)
    Label(root, text=str(n), pady=5).grid(row=n + 1, column=6)
    dct = {
        "you_guess": Entry(width=5, state=DISABLED),
        "you_bulls": Entry(width=2, state=DISABLED),
        "you_cows": Entry(width=2, state=DISABLED),
        "op_guess": Entry(width=5, state=DISABLED),
        "op_bulls": Entry(width=2, state=DISABLED),
        "op_cows": Entry(width=2, state=DISABLED),
    }
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

    main_menu()

    # threading.Thread(target=root.mainloop).run()
    root.mainloop()


if __name__ == "__main__":
    main()
