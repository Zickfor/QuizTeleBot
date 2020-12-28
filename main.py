import configparser
import datetime
import logging
import time

from aiogram import Bot, Dispatcher, executor, types

from utilities.converters import get_user_from_message, get_attempt_from_callback, get_attempt_from_message, \
    get_random_question, create_stat, create_attempt, generate_statistics_from_stats, \
    get_user_from_callback, get_category
from utilities.middleware import DatabaseCheckExistance

config = configparser.ConfigParser()
config.read("config.ini")

token = config["bot"]["token"]

bot = Bot(token)
dp = Dispatcher(bot)
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                    filename="log", filemode='a')


@dp.message_handler(commands=["start"])
async def next_handler(message):
    await message.reply("Напишите /next для получения задания")


@dp.message_handler(commands=["next"])
async def next_handler(message):
    user = get_user_from_message(message)
    question = get_random_question(user)
    if question is not None:
        msg = await message.reply(text=question.generate_question_text(),
                                  reply_markup=question.generate_question_markup())
        stat = create_stat(user_id=user.id, asking_time=msg.date)
        create_attempt(question_id=question.id, message_id=msg.message_id, user_id=user.id, stat=stat)
    else:
        await message.reply(
            text="Похоже, что вы не подписаны ни на одну категорию\n\nОтправьте /categories, чтобы подписаться")


@dp.message_handler(commands=["categories"])
async def next_handler(message):
    user = get_user_from_message(message)
    await message.reply(text="Нажмите ниже на категорию, чтобы переключить её состояние",
                        reply_markup=user.gen_user_categories_markup())


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
    lambda call: (int(call.message.date.timestamp()) > 1608674862) and (get_attempt_from_callback(call) is not None))
async def callback(call):
    attempt = get_attempt_from_callback(call)
    choosed_answer = call.data.split('_')[1]
    if choosed_answer == attempt.question.correct_answer:
        await call.message.edit_text(text=attempt.question.generate_answer_true(), reply_markup=None)
        await call.answer(text=attempt.question.generate_answer_true())
        attempt.stat.correct = True
    else:
        await call.message.edit_text(text=attempt.question.generate_answer_false(), reply_markup=None)
        await call.answer(text=attempt.question.generate_answer_false())
        attempt.stat.correct = False
    attempt.stat.answer_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
    attempt.stat.save()


@dp.callback_query_handler(lambda call: call.data.split('_')[0] == "categorysubscription")
async def default(call):
    user = get_user_from_callback(call)
    user.category_switch(get_category(call.data.split('_')[1]))
    await call.answer(text="Переключено")
    await call.message.edit_reply_markup(reply_markup=user.gen_user_categories_markup())


@dp.callback_query_handler()
async def default(call):
    await call.answer(text="К сожалению данное действие больше не поддерживается", show_alert=True)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                        reply_markup=types.inline_keyboard.InlineKeyboardMarkup())


@dp.message_handler()
async def default_message(message):
    await message.reply("Sorry, what?\nЧто простите?")


if __name__ == "__main__":
    dp.middleware.setup(DatabaseCheckExistance())
    executor.start_polling(dp)
