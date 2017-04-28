import config
from gameclasses import Game, Users, User
from cardclasses import card_names
import telebot
import time
from telebot import types
import numpy as np

bot = telebot.TeleBot(config.token)
game = None


@bot.message_handler(commands=['help'])
def show_help(message):
    hints = '''
/help - показывает это сообщение

/rules - правила игры (TODO)
/hint - карточка с кратким описанием и стоимостью карт

/create - создает полностью новую игру с пустым списком игроков
/join - добавляет игрока в игру
/start - после добавления всех игроков начинает игру
/newround - перезапускает игру с теми же игроками и настройками (TODO)

/cards - показывает все сброшенные с рук карты
/players - показывает всех оставшихся в игре игроков

/doubledeck - играть в 2 колоды: больше карт, больше народу, больше веселья!
'''
    bot.send_message(message.chat.id, hints)


@bot.message_handler(commands=['hint'])
def show_hint(message):
    hints = '''
8. Принцесса (x1) - если вы сбрасываете эту карту, оказываетесь вне игры
7. Графиня (x1) - если на руке Принц или Король, то Графиню надо сбросить
6. Король (x1) - скинув Короля обменяйтесь картами с одним из игроков
5. Принц (x2) - выбранный вами игрок должен скинуть свою карту и взять новую
4. Служанка (x2) - сбросив Служанку получаете защиту на следующий круг
3. Барон (x2) - сравните свою карту с другим игроком, у кого значение меньше - тот вылетает из игры
2. Священник (x2) - позволяет посмотреть карту другого игрока
1. Стражница (x5) - назовите карту другого игрока (не стражницу), если угадаете - он вылетет из игры
'''
    bot.send_message(message.chat.id, hints)


@bot.message_handler(commands=['create'])
def start(message):
    print('create')
    global game
    game = Game(bot, message.chat.id)


@bot.message_handler(commands=['doubledeck'])
def start(message):
    print('dd')
    global game

    if game is None:
        print('game is None')
        return

    if not game.double_deck:
        game.double_deck = True
        bot.send_message(message.chat.id, 'Добавлена вторая колода.')
    else:
        game.double_deck = False
        bot.send_message(message.chat.id, 'Убрана вторая колода.')


@bot.message_handler(commands=['join'])
def join_user(message):
    print('join')
    global game
    if game is None:
        print('game is None')
        return
    if game.started:
        bot.send_message(message.chat.id, 'Игра уже началась.')
        return
    username = message.from_user.username or message.from_user.first_name
    uid = message.from_user.id
    if uid in game.users:
        bot.send_message(message.chat.id, '@{} уже в игре.'.format(username))
        return
    game.users.add(User(username, uid, bot))
    bot.send_message(message.chat.id, '@{} присоединился к игре.'.format(username))


@bot.message_handler(commands=['start'])
def start_game(message):
    print('start')
    global game
    if game is None:
        print('game is None')
        return
    game.start()
    game.start_turn()


@bot.message_handler(commands=['cards'])
def show_cards(message):
    global game
    if game is None:
        print('game is None')
        return
    used_cards = 'Сброшенные карты:\n'
    unique_used_cards = np.unique(sorted(game.used_cards), return_counts=True)
    for num, card in enumerate(unique_used_cards[0]):
        used_cards += ' - {:10s} [{}]\n'.format(card.name, unique_used_cards[1][num])
    bot.send_message(message.chat.id, used_cards)


@bot.message_handler(commands=['players'])
def show_users(message):
    global game
    if game is None:
        print('game is None')
        return
    users = 'Оставшиеся игроки: \n'
    for user in game.users.users:
        users += ' - {} '.format(user.name)
        if user.defence:
            users += '#'
        if user == game.dealer:
            users += '<<'
        users += '\n'

    bot.send_message(message.chat.id, users)


@bot.message_handler(content_types=['text'])
def text_message(message):
    print('text')
    global game
    if game is None:
        print('game is None')
        return

    if game.dealer is None:
        return

    if message.chat.id == game.dealer.uid:
        if game.state is 'select_card' and \
           message.text in [game.dealer.card.name, game.dealer.new_card.name]:

            game.select_card(message.text)

        if game.state is 'select_victim' and (message.text in game.users.get_victims(game.dealer) or
                                              game.no_victims and message.text == game.dealer.name):
            game.select_victim(message.text)

        if game.state is 'guess_card' and message.text in card_names[:-1]:
            game.guess_card(message.text)

if __name__ == '__main__':
    # while True:
    #     try:
    #         bot.polling(none_stop=True)
    #         # ConnectionError and ReadTimeout because of possible timout of the requests library
    #         # TypeError for moviepy errors
    #         # maybe there are others, therefore Exception
    #     except Exception as e:
    #         print('Error, restarting bot')
    #         time.sleep(15)
    bot.polling(none_stop=True)
