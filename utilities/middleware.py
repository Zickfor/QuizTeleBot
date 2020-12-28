from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from utilities.converters import create_user_if_not_exist, get_chat_id_from_message, get_chat_id_from_callback


class DatabaseCheckExistance(BaseMiddleware):

    def __init__(self):
        super(DatabaseCheckExistance, self).__init__()

    async def on_process_message(self, message: Message, data: dict):
        create_user_if_not_exist(get_chat_id_from_message(message))

    async def on_process_callback_query(self, call: CallbackQuery, data: dict):
        create_user_if_not_exist(get_chat_id_from_callback(call))
