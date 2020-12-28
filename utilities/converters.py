import random

from models import User, Question, Stat, Attempt, Category


def get_random_question(user):
    possible_questions = user.get_possible_questions()
    if len(possible_questions) == 0:
        return None
    else:
        return random.choice(user.get_possible_questions())


def get_chat_id_from_chat(chat):
    return chat["id"]


def get_chat_id_from_message(message):
    return get_chat_id_from_chat(message["chat"])


def get_message_id_from_message(message):
    return message["message_id"]


def get_user_from_message(message):
    try:
        return User.select().where(User.chat_id == get_chat_id_from_message(message)).get()
    except User.DoesNotExist:
        return None


def get_attempt_from_message(message):
    try:
        return Attempt.select().where(Attempt.user_id == get_user_from_message(message).id,
                                      Attempt.message_id == get_message_id_from_message(message)).get()
    except Attempt.DoesNotExist:
        return None


def get_stat_from_attempt(attempt):
    return Stat.get(attempt.stat_id)


def get_stat_from_message(message):
    return get_stat_from_attempt(get_attempt_from_message(message))


def get_question_from_attempt(attempt):
    return Question.get(attempt.question_id)


def get_question_from_message(message):
    return get_question_from_attempt(get_attempt_from_message(message))


def get_message_from_callback(callback):
    return callback["message"]


def get_chat_id_from_callback(callback):
    return get_chat_id_from_message(get_message_from_callback(callback))


def get_user_attempt_stat_question_from_message(message):
    user = get_user_from_message(message)
    attempt = get_message_id_from_message(message)
    stat = get_attempt_from_message(message)
    question = get_question_from_message(message)
    return user, attempt, stat, question


def get_user_attempt_stat_question_from_callback(callback):
    return get_user_attempt_stat_question_from_message(get_message_from_callback(callback))


def get_user_from_callback(callback):
    return get_user_from_message(get_message_from_callback(callback))


def get_message_id_from_callback(callback):
    return get_message_id_from_message(get_message_from_callback(callback))


def get_text_from_message(message):
    return message["text"]


def get_text_from_callback(callback):
    return get_text_from_message(get_message_from_callback(callback))


def get_attempt_from_callback(callback):
    return get_attempt_from_message(get_message_from_callback(callback))


def create_stat(**kwargs):
    return Stat.create(**kwargs)


def create_attempt(**kwargs):
    return Attempt.create(**kwargs)


def create_user(**kwargs):
    return User.create(**kwargs)


def calculate_median_answer_time(stats):
    total_answer_time = 0
    total_answered_questions = 0
    for stat in stats:
        if stat.correct is not None:
            answer_time = stat.answer_time - stat.asking_time
            total_answer_time += answer_time.seconds
            total_answered_questions += 1
    if total_answered_questions == 0:
        return None
    median_answer_time = total_answer_time / total_answered_questions
    return median_answer_time


def generate_statistics_from_stats(stats):
    total_correct = 0
    total_wrong = 0
    total_no_answer = 0
    total_questions = len(stats)

    if total_questions == 0:
        return {"available": False}

    for stat in stats:
        if stat.correct is True:
            total_correct += 1
        elif stat.correct is False:
            total_wrong += 1
        elif stat.correct is None:
            total_no_answer += 1

    return {"available": True,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "total_wrong": total_wrong,
            "total_no_answer": total_no_answer,
            "percents_correct": total_correct / total_questions,
            "percents_wrong": total_wrong / total_questions,
            "percents_no_answer": total_no_answer / total_questions,
            "median_answer_time": calculate_median_answer_time(stats)}


def get_category(id):
    return Category.get_by_id(id)


def create_user_if_not_exist(chat_id):
    try:
        return create_user(chat_id=chat_id)
    except User.DoesNotExist:
        return None
