import unittest
from bot import GameBot
from telebot import types
import logging
import sys


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

    def test_create_joins(self):
        assumed_messages = [
            (0, 'Game is created, resend next message to your freinds whith whom you would like to play'),
            (),
            (1, 'There is no username, try /join @username or /create'),
            (0, 'Player @bob joined to game'),
            (1, 'Player @bob joined to game'),
            (0, 'You already joined to game'),
            (1, 'You already joined to game'),


        ]

        def fake_send_message(chat_id, text, reply_markup=None, parse_mode=None):
            logging.info("[#%d] %s", chat_id, text)

        bot = GameBot('')
        bot.send_message = fake_send_message

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

            # check if nobody cannot join agter start
            self.new_message(alice, '/start'),
            self.new_message(cinderella, '/join @alice'),
            self.new_message(cinderella, '/join @bob'),
        ])


if __name__ == '__main__':
    tester = TestBot()
    tester.run()
