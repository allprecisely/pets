import logging

from decouple import config
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import Updater

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
    )


def echo(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


def caps(update: Update, context: CallbackContext):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def main():
    updater = Updater(token=config("TOKEN"))
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    caps_handler = CommandHandler('caps', caps)
    dispatcher.add_handler(caps_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
