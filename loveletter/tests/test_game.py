import unittest
from game import Game
from users import User
from cards import (
    Princess,
    Countess,
    King,
    Prince,
    Maid,
    Baron,
    Priest,
    Guard
)
import mock


class TestBot:
    def __init__(self, test_case: unittest.TestCase, assumed_messages: list):
        self.test_case = test_case
        self.assumed_messages = assumed_messages[::-1]

    def send_message(self, chat_id, text):
        requires = self.assumed_messages.pop()

        if requires[0] is not None:
            self.test_case.assertEqual(chat_id, requires[0])

        if requires[1] is not None:
            self.test_case.assertEqual(text, requires[1])


class TestGame(unittest.TestCase):
    def test_game(self):
        # no randomness

        bot = TestBot(self, [
            (123, "Game is created"),
            (0, None),
            (1, None),
            # (None, None),
            # (123, None),
            # (0, "")
        ])
        game = Game(bot, 123)

        alice = User('Alice', 0, bot, game)
        bob = User('Bob', 1, bot, game)

        game.users.add(alice)
        game.users.add(bob)

        Guard.num_in_deck = 1
        Princess.num_in_deck = 1
        Game.card_types = (
            Princess,
            Guard
        )

        with mock.patch('random.shuffle', lambda x: x):
            game.start()
