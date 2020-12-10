from aiogram import Bot, Dispatcher, executor

from bot.handlers import message, callback


def start_bot(token):
    bot = Bot(token)
    dp = Dispatcher(bot)

    message.init_handlers(bot, dp)
    callback.init_handlers(bot, dp)

    executor.start_polling(dp)
