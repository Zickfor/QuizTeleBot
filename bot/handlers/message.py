import datetime, time

from models import User, Attempt, Stat, Question
from utilities import get_random_question


def init_handlers(bot, dp):
    @dp.message_handler(commands=["next"])
    async def next_handler(message):
        question = get_random_question(Question)
        try:
            user = User.select().where(User.telegram_user_id == message["from"].id).get()
        except User.DoesNotExist:
            user = User.create(telegram_user_id=message["from"].id,
                               first_name=message["from"].first_name,
                               last_name=message["from"].last_name,
                               username=message["from"].username,
                               chat_id=message.chat.id)
        msg = await bot.send_message(message.chat.id, text=question.generate_question_text(),
                                     reply_markup=question.generate_question_markup())
        stat = Stat.create(user=user,
                           asking_time=msg.date)
        Attempt.create(
            question_id=question.id,
            message_id=msg.message_id,
            asking_time=msg.date,
            user=user,
            stat=stat)

    @dp.message_handler()
    async def handle_messages(message):
        try:
            user = User.select().where(User.telegram_user_id == message["from"].id).get()
            attempt = Attempt.select().where(
                (Attempt.user_id == user.id) &
                (Attempt.message_id == message.reply_to_message.message_id)).get()
            if attempt.stat.correct is None:
                if attempt.question.correct_answer.lower() == message.text.lower():
                    await bot.send_message(message.chat.id,
                                           text=attempt.question.generate_answer_true(),
                                           reply_to_message_id=message.message_id)
                    attempt.stat.correct = True
                else:
                    await bot.send_message(message.chat.id,
                                           text=attempt.question.generate_answer_false(),
                                           reply_to_message_id=message.message_id)
                    attempt.stat.correct = False
                attempt.stat.answer_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                attempt.stat.save()
            else:
                await bot.send_message(message.chat.id, text="Вы уже отвечали на этот вопрос!\n\n/next",
                                       reply_to_message_id=message.message_id)
        except AttributeError:
            await bot.send_message(message.chat.id, text="Sorry, what?\nЧто простите?\n\n/next",
                                   reply_to_message_id=message.message_id)