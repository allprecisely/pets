from tkinter import *
from tkinter import messagebox

from PIL import ImageTk, Image

import main as handler

root = Tk()


def draw_a_string(guess_counter, current_guess, foo):
    widgets = [
        Label(root, text=guess_counter, pady=10),
        Label(root, text=current_guess, pady=10,),
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
    Label(root, text='№', justify=LEFT, pady=10).grid(row=2, column=0, stick='w')
    Label(
        root,
        text='Guesses',
        justify=LEFT,
        pady=10,
    ).grid(row=2, column=1, stick='w')
    Label(root, text='Bulls', pady=10).grid(row=2, column=2, stick='w')
    Label(root, text='Cows', pady=10).grid(row=2, column=3, stick='w')
    widgets = draw_a_string(guess_counter, current_guess, get_new_guess)


def new_game():
    for widget in root.winfo_children():
        widget.destroy()
    generator = handler.graphical_main()
    Button(root, text='New game', command=new_game).grid(row=0, column=0, stick='we')
    Button(root, text='Quit', command=lambda: root.quit()).grid(row=0, column=1, stick='w')
    Label(
        root,
        text='Come up with a 4-digit number with non-repeating digits!\nI\'ll try to guess.',
        justify=LEFT,
        pady=10,
    ).grid(row=1, column=0, columnspan=4, stick='w')
    Button(root, text='Ready!', command=lambda: guess(generator)).grid(row=1, column=4, stick='w')


def _main():
    photo = ImageTk.PhotoImage(Image.open('icon.jpeg'))
    root.iconphoto(False, photo)
    root.title('Bulls and cows!')
    root.geometry('600x500')
    new_game()

    root.grid_columnconfigure(0, minsize=30)
    root.grid_columnconfigure(1, minsize=30)
    root.grid_columnconfigure(2, minsize=30)
    root.grid_columnconfigure(3, minsize=30)
    root.grid_columnconfigure(4, minsize=50)
    root.grid_columnconfigure(5, minsize=50)

    root.mainloop()


if __name__ == '__main__':
    _main()
