import logging
import sys
import time
import random

import unittest
from telebot import types

from loveletter.bot import GameBot
from loveletter.cards import Guard
from loveletter.game import Game


class TestBot(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.users_id = 0
        self.messages_id = 0

        logging.basicConfig(
            stream=sys.stderr,
            level=logging.INFO,
            format='[%(levelname)s:%(asctime)s %(filename)s:%(lineno)s] %(message)s',
            datefmt='%Y-%m-%d %I:%M:%S'
        )

    def test_create_joins(self):
        bot = self.setup_bot()
        alice = self.new_user('alice')
        bob = self.new_user('bob')
        cinderella = self.new_user('cinderella')

        bot.process_new_messages([
            self.new_message(alice, '/create'),

            # wrong joins
            self.new_message(bob, '/join'),
            self.new_message(bob, '/join @cinderella'),

            # right join
            self.new_message(bob, '/join @alice'),

            # check if they cannot join after join
            self.new_message(alice, '/join @bob'),
            self.new_message(bob, '/join @alice'),

            # check if nobody cannot join after start
            self.new_message(alice, '/start'),
            self.new_message(cinderella, '/join @alice'),
            self.new_message(cinderella, '/join @bob'),
        ])

        # bot is asynchronous so we need to wait messages processing
        time.sleep(1)

        game = bot.get_game(alice.id)

        self.assertTrue(alice.id in game.users)
        self.assertTrue(bob.id in game.users)
        self.assertFalse(cinderella.id in game.users)

    def test_play_random_game(self):
        bot = self.setup_bot()
        users, game = self.setup_game_with_4_players(bot)

        self.play_random_game(bot, users, game)

        self.assertTrue(len(game.users) == 1 or not game.deck)

    def test_restart_game(self):
        bot = self.setup_bot()
        users, game = self.setup_game_with_4_players(bot)

        self.play_random_game(bot, users, game)

        bot.process_new_messages([
            self.new_message(users[0], '/restart')
        ])

        time.sleep(0.1)

        self.assertNotEqual(game.state, 'game_over')
        self.assertTrue(not game.users.loosers)

        self.play_random_game(bot, users, game)

    def setup_game_with_4_players(self, bot):
        users = [
            self.new_user('alice'),
            self.new_user('bob'),
            self.new_user('cinderella'),
            self.new_user('dolly'),
        ]

        bot.process_new_messages([
            self.new_message(users[0], '/create'),
            self.new_message(users[1], '/join @alice'),
            self.new_message(users[2], '/join @alice'),
            self.new_message(users[3], '/join @alice'),
            self.new_message(users[0], '/start')
        ])

        time.sleep(1)

        game = bot.get_game(users[0].id)

        return users, game

    def play_random_game(self, bot,  users, game):
        while game.state != 'game_over':
            player = game.dealer

            for user in users:
                if user.id == player:
                    break

            card = random.choice([player.card, player.new_card])

            bot.process_new_messages([
                self.new_message(user, card.name)
            ])

            time.sleep(0.1)

            if not card.targeted or game.card_without_action:
                continue

            victim = random.choice(game.list_possible_victims())

            bot.process_new_messages([
                self.new_message(user, victim)
            ])

            time.sleep(0.1)

            if not isinstance(card, Guard):
                continue

            guess = random.choice([card.name for card in Game.card_types[:-1]])

            bot.process_new_messages([
                self.new_message(user, guess)
            ])

        return game

    def new_user(self, name):
        user_id = self.users_id
        self.users_id += 1

        user = types.User(
            id=user_id,
            is_bot=False,
            first_name=name,
            username=name,
        )

        return user

    def new_message(self, user: types.User, message):
        message_id = self.messages_id
        self.messages_id += 1

        chat = types.Chat(
            id=user.id,
            type='private'
        )

        message = types.Message(
            message_id=message_id,
            from_user=user,
            date=None,
            chat=chat,
            content_type='text',
            options={'text': message},
            json_string='',
        )

        return message

    @staticmethod
    def setup_bot():
        def fake_send_message(chat_id, text, reply_markup=None, parse_mode=None):
            logging.info("[#%d] %s", chat_id, text)

        bot = GameBot('')
        bot.send_message = fake_send_message

        return bot


if __name__ == '__main__':
    tester = TestBot()
    tester.run()
