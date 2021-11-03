import time
from tkinter import *

from PIL import ImageTk, Image

import main

root = Tk()
current_guess = '0123'
guess_counter = 1

def guess():
    global guess_counter
    global current_guess

    def get_new_guess():
        global current_guess
        c = cows.get()
        b = bulls.get()
        if not c:
            cows.insert(0, '0')
        if not b:
            bulls.insert(0, '0')
        current_guess += '1'

    Label(
        root,
        text=current_guess,
        pady=10,
    ).grid(row=guess_counter + 2, column=0, stick='w')
    Label(
        root,
        text='0123',
        pady=10,
    ).grid(row=guess_counter + 2, column=1, stick='w')
    bulls = Entry(root)
    cows = Entry(root)
    bulls.grid(row=guess_counter + 2, column=2, stick='w')
    cows.grid(row=guess_counter + 2, column=3, stick='w')

    Button(root, text='Answer!', command=get_new_guess).grid(row=guess_counter + 3, column=4, stick='w')

    guess_counter += 1


def ready():
    current_guess = '0123'

    def get_new_guess():
        nonlocal current_guess
        c = cows.get()
        b = bulls.get()
        if not c:
            cows.insert(0, '0')
        if not b:
            bulls.insert(0, '0')
        current_guess += '1'

    Label(root, text='№', justify=LEFT, pady=10).grid(row=2, column=0, stick='w')
    Label(
        root,
        text='Guesses',
        justify=LEFT,
        pady=10,
    ).grid(row=2, column=1, stick='w')
    Label(root, text='Bulls', pady=10).grid(row=2, column=2, stick='w')
    Label(root, text='Cows', pady=10).grid(row=2, column=3, stick='w')
    guess_counter = 1
    while True:


def new_game():
    pass


def _main():
    # photo = PhotoImage(file='icon2.png')
    photo = ImageTk.PhotoImage(Image.open('icon.jpeg'))
    root.iconphoto(False, photo)
    root.title('Bulls and cows!')
    root.geometry('600x500')

    Button(root, text='New game', command=new_game).grid(row=0, column=0, stick='we')
    Button(root, text='Quit', command=lambda: root.quit()).grid(row=0, column=1, stick='w')
    Label(
        root,
        text='Come up with a 4-digit number with non-repeating digits!\nI\'ll try to guess.',
        justify=LEFT,
        pady=10,
    ).grid(row=1, column=0, columnspan=4, stick='w')
    Button(root, text='Ready!', command=ready).grid(row=1, column=4, stick='w')

    root.grid_columnconfigure(0, minsize=30)
    root.grid_columnconfigure(1, minsize=30)
    root.grid_columnconfigure(2, minsize=30)
    root.grid_columnconfigure(3, minsize=30)
    root.grid_columnconfigure(4, minsize=50)
    root.grid_columnconfigure(5, minsize=50)

    root.mainloop()


if __name__ == '__main__':
    _main()
