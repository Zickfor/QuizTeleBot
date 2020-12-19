import configparser
import datetime
import logging
import time

from aiogram import Bot, Dispatcher, executor, types

from utilities.converters import get_user_from_message, get_attempt_from_callback, get_attempt_from_message, \
    get_random_question, create_user, create_stat, create_attempt, generate_statistics_from_stats

config = configparser.ConfigParser()
config.read("config.ini")

token = config["bot"]["token"]

bot = Bot(token)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands=["start"])
async def next_handler(message):
    user = get_user_from_message(message)
    if user is None:
        user = create_user(chat_id=message.chat.id)
    await message.reply("Напишите /next для получения задания")


@dp.message_handler(commands=["next"])
async def next_handler(message):
    question = get_random_question()
    user = get_user_from_message(message)
    msg = await message.reply(text=question.generate_question_text(), reply_markup=question.generate_question_markup())
    stat = create_stat(user=user, asking_time=msg.date)
    create_attempt(
        question_id=question.id,
        message_id=msg.message_id,
        user=user,
        stat=stat)


@dp.message_handler(commands=["stats"])
async def next_handler(message):
    user = get_user_from_message(message)
    statistics = generate_statistics_from_stats(user.stats)
    if statistics["available"]:
        text = f"Ваша статистика:\n" \
               f"\n" \
               f"Всего было задано вопросов: {statistics['total_questions']}\n" \
               f"Правильно: {statistics['total_correct']} ({round(statistics['percents_correct'] * 100, 2)}%)\n" \
               f"Неправильно: {statistics['total_wrong']} ({round(statistics['percents_wrong'] * 100, 2)}%)\n" \
               f"Не дано ответа: {statistics['total_no_answer']} ({round(statistics['percents_no_answer'] * 100, 2)}%)\n" \
               f"Среднее время ответа: {round(statistics['median_answer_time'], 2)} c"
    else:
        text = "На данный момент статистика для вас недоступна"
    await message.reply(text)


@dp.message_handler(lambda message: message["reply_to_message"] is not None)
async def handle_messages(message):
    attempt = get_attempt_from_message(message["reply_to_message"])
    if attempt is not None:
        if attempt.stat.correct is None:
            if attempt.question.correct_answer.lower() == message.text.lower():
                await message.reply(attempt.question.generate_answer_true())
                attempt.stat.correct = True
            else:
                await message.reply(attempt.question.generate_answer_false())
                attempt.stat.correct = False
            attempt.stat.answer_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            attempt.stat.save()
        else:
            await message.reply(text="Вы уже отвечали на этот вопрос!\n\n/next", reply=True)


@dp.callback_query_handler(
    lambda call: (int(call.message.date.timestamp()) > 1602229656) and (call.data.split('_')[0] == "answer"))
async def callback(call):
    attempt = get_attempt_from_callback(call)
    choosed_answer = call.data.split('_')[1]
    if choosed_answer == attempt.question.correct_answer:
        await call.message.edit_text(text=attempt.question.generate_answer_true(), reply_markup=None)
        await bot.answer_callback_query(callback_query_id=call.id, text=attempt.question.generate_answer_true())
        attempt.stat.correct = True
    else:
        await call.message.edit_text(text=attempt.question.generate_answer_false(), reply_markup=None)
        await bot.answer_callback_query(callback_query_id=call.id, text=attempt.question.generate_answer_false())
        attempt.stat.correct = False
    attempt.stat.answer_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    attempt.stat.save()


@dp.callback_query_handler()
async def default(call):
    await bot.answer_callback_query(callback_query_id=call.id,
                                    text="К сожалению данный тип вопросов больше не поддерживается", show_alert=True)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=types.inline_keyboard.InlineKeyboardMarkup())


@dp.message_handler()
async def default_message(message):
    await message.reply("Sorry, what?\nЧто простите?")


if __name__ == "__main__":
    executor.start_polling(dp)
