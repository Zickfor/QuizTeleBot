import random


def get_random_question(Question):
    return random.choice(Question.select())
