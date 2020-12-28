import json
import random

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from peewee import *
from playhouse.fields import PickleField

db = SqliteDatabase("app1.db")


class BaseModel(Model):
    class Meta:
        database = db


class Category(BaseModel):
    id = PrimaryKeyField(column_name="id")
    name = CharField(column_name="name", max_length=64)


class Question(BaseModel):
    id = PrimaryKeyField(column_name="id")
    value = CharField(column_name="value", max_length=256)
    type = CharField(column_name="type", max_length=8)
    correct_answer = CharField(column_name="correct_answer", max_length=64)
    wrong_answers: list = PickleField(column_name="wrong_answers", null=True)
    answers_amount = IntegerField(column_name="answers_amount", null=True)
    category_id = ForeignKeyField(Category, backref="questions")

    def generate_question_text(self):
        return self.value

    def generate_question_markup(self):
        if self.type == "choose":
            answers = [self.correct_answer] + random.sample(self.wrong_answers, self.answers_amount - 1)
            random.shuffle(answers)
            buttons = [{"text": answer, "callback_data": f"answer_{answer}"} for answer in answers]
            return json.dumps({'inline_keyboard': [[*buttons]]})
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
    chat_id = CharField(column_name="chat_id", max_length=64)

    def get_possible_questions(self):
        questions = []
        for category in self.get_subscribed_categories():
            for question in category.questions:
                questions.append(question)
        return questions

    def get_subscribed_categories(self):
        return list(Category.select().join(UserCategory).join(User).where(User.id == self.id))

    def gen_user_categories_markup(self):
        markup = InlineKeyboardMarkup(resize_keyboard=True)
        buttons = []
        not_subscribed_categories = [cat for cat in Category.select() if cat not in self.get_subscribed_categories()]
        for category in self.get_subscribed_categories():
            buttons.append(InlineKeyboardButton(text=f"✓{category.name}", callback_data=f"categorysubscription_{category.id}"))
        for category in not_subscribed_categories:
            buttons.append(InlineKeyboardButton(text=f"{category.name}", callback_data=f"categorysubscription_{category.id}"))
        markup.add(*buttons)
        return markup

    def category_switch(self, category):
        if category in self.get_subscribed_categories():
            UserCategory.select().where(UserCategory.user == self, UserCategory.category == category).get().delete_instance()
            return False
        else:
            UserCategory.create(user=self, category=category)
            return True


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


class UserCategory(BaseModel):
    user = ForeignKeyField(User)
    category = ForeignKeyField(Category)


for subclass in BaseModel.__subclasses__():
    try:
        subclass.create_table()
    except InternalError as px:
        print(str(px))
