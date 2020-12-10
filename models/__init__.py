import random

import aiogram
from peewee import *

from utilities.fields import MultiField

db = SqliteDatabase("app1.db")


class BaseModel(Model):
    class Meta:
        database = db


class Question(BaseModel):
    id = PrimaryKeyField(column_name="id")
    value = CharField(column_name="value", max_length=64)
    type = CharField(column_name="type")
    correct_answer = CharField(column_name="correct_answer")
    wrong_answers = MultiField(column_name="wrong_answers", null=True)
    answers_amount = IntegerField(column_name="answers_amount", null=True)

    def generate_question_text(self):
        return self.value

    def generate_question_markup(self):
        if self.type == "choose":
            answers = [self.correct_answer] + random.sample(self.wrong_answers, self.answers_amount - 1)
            random.shuffle(answers)
            markup = aiogram.types.inline_keyboard.InlineKeyboardMarkup()
            buttons = list()
            for answer in answers:
                buttons.append(
                    aiogram.types.inline_keyboard.InlineKeyboardButton(text=answer,
                                                                       callback_data=f"{self.id}_{answer}"))
            markup.add(*buttons)
            return markup
        return None

    def generate_answer_true(self):
        return "Это правда!\n\n/next"

    def generate_answer_false(self):
        v = random.randint(1, 2)
        if v == 1:
            return f"Вы меня обманываете!\n\nПравильный ответ: {self.correct_answer}\n\n/next"
        else:
            return f"Это ложь!\n\nПравильный ответ: {self.correct_answer}\n\n/next"


class User(BaseModel):
    id = PrimaryKeyField(column_name="id")
    telegram_user_id = CharField(column_name="telegram_user_id", max_length=64)
    username = CharField(column_name="username", max_length=64, null=True)
    first_name = CharField(column_name="first_name", max_length=64, null=True)
    last_name = CharField(column_name="last_name", max_length=64, null=True)
    chat_id = CharField(column_name="chat_id", max_length=64)


class Stat(BaseModel):
    id = PrimaryKeyField(column_name="id")
    correct = BooleanField(column_name="correct", null=True)
    answer_time = DateTimeField(column_name="answer_time", null=True)
    asking_time = DateTimeField(column_name="asking_time")
    user = ForeignKeyField(User, backref="stats")


class Attempt(BaseModel):
    id = PrimaryKeyField(column_name="id")
    question = ForeignKeyField(Question, related_name="question")
    message_id = CharField(column_name="message_id", max_length=64)
    user = ForeignKeyField(User, backref="attempts")
    stat = ForeignKeyField(Stat, related_name="stat")


for subclass in BaseModel.__subclasses__():
    try:
        subclass.create_table()
    except InternalError as px:
        print(str(px))
