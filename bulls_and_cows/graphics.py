import time
from tkinter import *
from tkinter import messagebox

import guesser

root = Tk()


def draw_a_string(guess_counter, current_guess, foo):
    widgets = [
        Label(root, text=guess_counter, pady=5),
        Label(root, text=current_guess, pady=5,),
        Entry(root),
        Entry(root),
        Button(root, text='Answer!', command=foo),
    ]
    for i, widget in enumerate(widgets):
        widget.grid(row=guess_counter + 2, column=i, stick='w')

    return widgets


def guess(generator):
    def get_new_guess():
        nonlocal current_guess, guess_counter, widgets
        c = widgets[3].get()
        b = widgets[2].get()
        if not c:
            widgets[3].insert(0, '0')
        if not b:
            widgets[2].insert(0, '0')
        widgets[2]['state'] = DISABLED
        widgets[3]['state'] = DISABLED
        widgets[4]['state'] = DISABLED

        current_guess = generator.send(f'{b or 0} {c or 0}')
        if not current_guess:
            messagebox.showinfo('Неверные данные!')
            for widget in widgets:
                widget.destroy()
            widgets = draw_a_string(guess_counter, current_guess, get_new_guess)
            return
        if len(current_guess) > 4:
            messagebox.showinfo(
                f'Победа за {current_guess[4:]} попыток', f'Ваше число: {current_guess[:4]}'
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
    draw_game_field()
    generator = guesser.graphical_main()


def main_menu():
    Label(
        root, text='BULLS & COWS', font=('Arial', 30),
        height=3, anchor='s', pady=20
    ).pack()
    Button(root, text='New game', command=new_game).pack()
    Button(root, text='Local game', command=main_menu).pack()
    Button(root, text='Quit', command=lambda: root.quit()).pack()


def send():
    pass


def draw_game_field():
    Label(root, text='YOU', pady=5).grid(row=0, column=0, columnspan=4)
    Label(root, text='№', pady=5).grid(row=1, column=0)
    Label(root, text='Guess', pady=5).grid(row=1, column=1)
    Label(root, text='Bulls', pady=5).grid(row=1, column=2)
    Label(root, text='Cows', pady=5).grid(row=1, column=3)

    Label(root, text=' ' * 10, pady=5).grid(row=1, column=4)

    Label(root, text='OPPONENT', pady=5).grid(row=0, column=5, columnspan=4)
    Label(root, text='№', pady=5).grid(row=1, column=6)
    Label(root, text='Guess', pady=5).grid(row=1, column=7)
    Label(root, text='Bulls', pady=5).grid(row=1, column=8)
    Label(root, text='Cows', pady=5).grid(row=1, column=9)

    Label(root, text=' ' * 10, pady=5).grid(row=1, column=10)

    Button(root, text='Send', command=send).grid(row=0, column=11, columnspan=2, rowspan=2)

    Label(root, text='STATISTICS', pady=5).grid(row=2, column=11, columnspan=2)
    Label(root, text='Time started   ', pady=5).grid(row=3, column=11, stick='w')
    Label(root, text=time.strftime("%H:%M"), pady=5).grid(row=3, column=12)
    Label(root, text='Time ended', pady=5).grid(row=4, column=11, stick='w')
    Label(root, text='?', pady=5).grid(row=4, column=12)
    Label(root, text='Duration', pady=5).grid(row=5, column=11, stick='w')
    Label(root, text='?', pady=5).grid(row=5, column=12)

    Label(root, text=' ', pady=5).grid(row=6, column=11)

    Label(root, text='Player won', pady=5).grid(row=7, column=11, stick='w')
    Label(root, text='?', pady=5).grid(row=7, column=12)

    Label(root, text=' ', pady=5).grid(row=8, column=11)

    Button(root, text='New game', command=new_game).grid(row=9, column=11, columnspan=2)
    Button(root, text='Main menu', command=main_menu).grid(row=10, column=11, columnspan=2)
    Button(root, text='Quit', command=lambda: root.quit()).grid(row=11, column=11, columnspan=2)


def draw_round(n):
    Label(root, text=str(n), pady=5).grid(row=n + 1, column=0)
    Label(root, text=str(n), pady=5).grid(row=n + 1, column=6)
    dct = {
        'you_guess': Entry(width=5),
        'you_bulls': Entry(width=2),
        'you_cows': Entry(width=2),
        'op_guess': Entry(width=5),
        'op_bulls': Entry(width=2),
        'op_cows': Entry(width=2),
    }
    dct['you_guess'].grid(row=n + 1, column=1)
    dct['you_bulls'].grid(row=n + 1, column=1)
    dct['you_cows'].grid(row=n + 1, column=1)
    dct['op_guess'].grid(row=n + 1, column=1)
    dct['op_bulls'].grid(row=n + 1, column=1)
    dct['op_cows'].grid(row=n + 1, column=1)
    return dct


def main():
    root.title('Bulls and cows!')
    root.geometry('530x360')

    main_menu()
    # draw_game_field()
    # draw_round(1)

    root.mainloop()


if __name__ == '__main__':
    main()
