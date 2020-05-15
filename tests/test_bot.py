import unittest
from bot import GameBot


class TestUser:
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


class TestChat:
    def __init__(self, char_id):
        self.id = char_id


class TestMessage:
    def __init__(self, chat_id, user_id=None, username="user", text=""):
        self.chat = TestChat(chat_id)
        self.from_user = TestUser(user_id, username)
        self.text = text


class TestBot(unittest.TestCase):
    def test_show_help(self):
        def mock_self_message(chat_id, text):
            self.assertEqual(chat_id, 123)

        bot = GameBot("no token")
        bot.send_message = mock_self_message

        message = TestMessage(chat_id=123)
        bot.show_help(message)

    def test_create_game(self):
        def mock_self_message(chat_id, text):
            self.assertEqual(chat_id, 123)

        bot = GameBot("no token")
        bot.send_message = mock_self_message

        message = TestMessage(chat_id=123)

        self.assertFalse(bot.games)

        bot.create_game(message)

        self.assertTrue(len(bot.games) == 1)
        self.assertTrue(123 in bot.games.keys())

        message = TestMessage(123, user_id=1, username='vasya')

        bot.join_user(message)
        self.assertTrue(bot.games[123].users)

    def test_create_several_games(self):
        def mock_self_message(chat_id, text):
            pass

        bot = GameBot("no token")
        bot.send_message = mock_self_message

        message = TestMessage(chat_id=1)
        bot.create_game(message)

        message = TestMessage(chat_id=2)
        bot.create_game(message)

        self.assertTrue(len(bot.games) == 2)
