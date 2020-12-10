import configparser

from models import db
from bot import start_bot

config = configparser.ConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
config.read("config.ini")

tokens = config.getlist("Bot", "Tokens")
for token in tokens:
    start_bot(token)

db.connect()
