import datetime
import time

from models import User, Attempt


def init_handlers(bot, dp):
    @dp.callback_query_handler(lambda call: int(call.message.date.timestamp()) > 1602229656)
    async def callback(call):
        user = User.select().where(User.telegram_user_id == call["from"].id).get()
        attempt = Attempt.select().where(
            (Attempt.user_id == user.id) &
            (Attempt.message_id == call.message.message_id)).get()
        choosed_answer = call.data.split('_')[1]
        if choosed_answer == attempt.question.correct_answer:
            await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.edit_message_text(text=attempt.question.generate_answer_true(),
                                        chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.answer_callback_query(callback_query_id=call.id, text=attempt.question.generate_answer_true())
            attempt.stat.correct = True
        else:
            await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.edit_message_text(text=attempt.question.generate_answer_false(),
                                        chat_id=call.message.chat.id, message_id=call.message.message_id)
            await bot.answer_callback_query(callback_query_id=call.id, text=attempt.question.generate_answer_false())
            attempt.stat.correct = False
        attempt.stat.answer_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        attempt.stat.save()

    @dp.callback_query_handler(lambda call: True)
    async def default(call):
        await bot.answer_callback_query(callback_query_id=call.id,
                                        text="К сожалению данный тип вопросов больше не поддерживается", show_alert=True)
        await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                            reply_markup=types.inline_keyboard.InlineKeyboardMarkup())
