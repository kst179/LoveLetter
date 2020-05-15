"""
module docstring
"""
import gettext
import logging
import sys

import telebot
from telebot import types

import numpy as np

from game import Game
from users import User
import config


class GameBot(telebot.TeleBot):
    """
    Class that represents a TelegramBot
    that handles all games and players interactions

    :attribute games: dict of {chat_id: game}
    """

    def __init__(self, token):
        """
        Creates a bot

        :param token:
            token (str) for game bot, if you don't have one,
            you should go to @BotFather in telegram and
            create a new bot (just send him a '/newbot'
            message and follow instructions, it's pretty easy)
        """
        super().__init__(token)
        self.games = {}
        self.users = {}
        self.register_handlers()

    def register_handlers(self):
        """
        Registers handlers for bot.
        Handler is a function with '@bot.message_handler' descriptor,
        once created, bot will continuously accept special commands from players
        and handle it.
        """
        # This functions would be called only by base class methods,
        # so linter thinks they are unused
        # pylint: disable=unused-variable

        @self.message_handler(commands=['help'])
        def show_help(message):
            self.show_help(message)

        @self.message_handler(commands=['hint'])
        def show_hint(message):
            self.show_hint(message)

        @self.message_handler(commands=['create'])
        def create_game(message):
            self.create_game(message)

        @self.message_handler(commands=['doubledeck'])
        def double_deck(message):
            self.double_deck(message)

        @self.message_handler(commands=['join'])
        def join_user(message):
            self.join_user(message)

        @self.message_handler(commands=['start'])
        def start_game(message):
            self.start_game(message)

        @self.message_handler(commands=['cards'])
        def show_cards(message):
            self.show_cards(message)

        @self.message_handler(commands=['players'])
        def show_users(message):
            self.show_users(message)

        @self.message_handler(content_types=['text'])
        def text_handler(message):
            self.text_handler(message)

    def get_game(self, chat_id):
        """
        Helper function to get game by chat_id
        where it is playing, if game not found returns None

        :param chat_id:
            int, id of the chat where game is played
        :return:
            Game, if game was created in chat with given id,
            else None
        """
        if chat_id not in self.games.keys():
            self.send_message(chat_id, _("There no game in this chat yet"))
            return None

        return self.games[chat_id]

    def show_help(self, message):
        """
        Shows help in chat

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        print(message.chat.type)

        self.send_message(message.chat.id, _("help"))

    def show_hint(self, message):
        """
        Shows hint (small copy of game rules) in chat

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """

        self.send_message(message.chat.id, _("hints"))

    def create_game(self, message):
        """
        Creates game in chat from where message is came

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        chat_id = message.chat.id
        if chat_id in self.games.keys():
            markup = types.ReplyKeyboardRemove(selective=False)

            self.send_message(chat_id,
                              _("The game has been already created in this chat, restart it?"))
            return

        self.games[chat_id] = Game(self, chat_id)

        logging.info('Chat #{}: game created'.format(chat_id))

    def double_deck(self, message):
        """
        Toggles second set of cards,
        it can be useful if more than 5
        players are in game

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        chat_id = message.chat.id
        game = self.get_game(chat_id)

        if not game:
            return

        if game.state != 'not_started':
            self.send_message(chat_id, _("The game is already started"))
            return

        if not game.double_deck:
            game.double_deck = True
            self.send_message(chat_id, _("The second deck is added"))
        else:
            game.double_deck = False
            self.send_message(chat_id, _("The second deck is removed"))

        logging.info('Chat #{}: set doubledeck'.format(chat_id))

    def join_user(self, message):
        """
        Adds user who wrote this message to game

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        chat_id = message.chat.id
        game = self.get_game(chat_id)

        if not game:
            return

        if game.started:
            self.send_message(chat_id, _("Game has been already started"))
            return

        username = message.from_user.username or message.from_user.first_name
        user_id = message.from_user.id

        if user_id in game.users:
            self.send_message(chat_id, _("Player @{} already joined to game.").format(username))
            return

        user = User(username, user_id, self, game)
        self.users[user_id] = user

        game.users.add(user)
        self.send_message(chat_id, 'Player @{} joined to game'.format(username))

        if game.users.num_users() == 6 and not game.double_deck:
            game.double_deck = True
            self.send_message(
                chat_id,
                _("The number of players reached 6, the second deck is automatically added")
            )

        logging.info('Chat #{}: user #{} added'.format(chat_id, user_id))

    def start_game(self, message):
        """
        Starts game, and make first turn.
        There is no way to change number of players or
        toggle double deck if game is already started.

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        chat_id = message.chat.id
        game = self.get_game(chat_id)

        if not game:
            return

        game.start()
        game.start_turn()

        logging.info("Chat #{}: game started".format(chat_id))

    def show_cards(self, message):
        """
        Shows all cards that was already played

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        chat_id = message.chat.id
        game = self.get_game(chat_id)

        if game is None:
            return

        used_cards = _("Dropped cards list:\n")
        unique_used_cards = np.unique(sorted(game.used_cards), return_counts=True)
        for num, card in enumerate(unique_used_cards[0]):
            used_cards += ' - {:10s} [{}]\n'.format(card.name, unique_used_cards[1][num])
        self.send_message(chat_id, used_cards)

    def show_users(self, message):
        """
        Shows all players, who is current dealer,
        and who is currently protected by the 'Maid' card to chat

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        :return:
        """
        chat_id = message.chat.id
        game = self.get_game(chat_id)

        if not game:
            return

        users = _("Players remained: \n")
        for user in game.users.users:
            users += ' - @{} '.format(user.name)
            if user.defence:
                users += '^'
            if user == game.dealer:
                users += '<<'
            users += '\n'

        self.send_message(chat_id, users)

    def text_handler(self, message):
        """
        Handles all free-text messages, that are
        used for moving between states

        :param message:
            telebot.types.Message, message that contains
            info about chat where it was written and user who wrote it
        """
        chat_id = message.chat.id

        if message.chat.type == 'private':
            game = self.users[chat_id].game
        else:
            game = self.get_game(chat_id)

        if not game:
            return

        if game.dealer is None:
            return

        if chat_id == game.dealer.user_id:
            if game.state == 'select_card' and \
                    message.text in [game.dealer.card.name, game.dealer.new_card.name]:
                game.select_card(message.text)

            if (game.state == 'select_victim' and
                    (message.text in game.users.get_victims(game.dealer) or
                     game.can_choose_yourself and message.text == game.dealer.name)):
                game.select_victim(message.text)

            if game.state == 'guess_card':
                game.guess_card(message.text)


if __name__ == '__main__':
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='[%(levelname)s:%(asctime)s %(filename)s:%(lineno)s] %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S'
    )

    gettext.install('bot', localedir='./locale', codeset='UTF-8')

    logging.info("Bot started")

    bot = GameBot(config.token)
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as ex:
            logging.error(ex)
            raise ex
