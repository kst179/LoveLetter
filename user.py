from cards import *
from telebot import types

class User:
    def __init__(self, name, user_id, bot):
        self.name = name
        self.user_id = user_id
        self.private_chat = user_id
        self.bot = bot
        self.card = None
        self.new_card = None
        self.defence = False

    def take_card(self, deck):
        self.card = deck[-1]
        self.card.owner = self
        del deck[-1]
        self.bot.send_message(self.private_chat, 'Ваша карта "{}"'.format(self.card.name))

    def take_new_card(self, deck):
        self.new_card = deck[-1]
        self.new_card.owner = self
        del deck[-1]
        self.bot.send_message(self.private_chat, 'Вы взяли из колоды карту "{}"'.format(self.new_card.name))

    def __eq__(self, other):
        if type(other) is User:
            return self.user_id == other.uid
        return self.user_id == other

    def __ne__(self, other):
        return not self == other
