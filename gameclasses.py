import random
from cardclasses import *
from telebot import types


class Game:
    def __init__(self, bot, group_chat):
        self.bot = bot
        self.group_chat = group_chat
        self.users = Users()
        self.started = False
        self.deck = [
            Princess(),
            Countess(),
            King(),
            Prince(),
            Prince(),
            Maid(),
            Maid(),
            Baron(),
            Baron(),
            Priest(),
            Priest(),
            Guard(),
            Guard(),
            Guard(),
            Guard(),
            Guard()
        ]
        self.used_cards = []
        self.dealer = None
        self.victim = None
        self.guess = None
        self.first_card = None
        self.no_victims = False
        self.double_deck = False
        self.state = 'change_turn'
        self.bot.send_message(self.group_chat, 'Игра создана.')

    def start(self):
        if len(self.users.users) < 2:
            self.bot.send_message(self.group_chat, 'Слишком мало игроков, должно быть минимум 2')
            return

        if self.double_deck:
            self.deck *= 2
        random.shuffle(self.deck)
        self.first_card = self.deck[-1]
        del self.deck[-1]
        self.users.shuffle()
        for user in self.users.users:
            user.take_card(self.deck)
        self.started = True
        self.state = 'change_turn'
        users = 'Игра началась.\nПорядок игроков:\n'
        for user in self.users.users:
            users += ' - {}\n'.format(user.name)
        self.bot.send_message(self.group_chat, users)

    def check_end(self):
        if len(self.users.users) == 1 or len(self.deck) == 0:
            self.started = False
            cards = []
            for user in self.users.users:
                cards.append(user.card)

            winner = max(cards).owner

            results = 'Игра закончилась.\nПобедил {}\nОстались:\n'.format(winner.name)
            for i, card in enumerate(reversed(sorted(cards))):
                results += '{}. {} - {} ({})\n'.format(i+1, card.owner.name, card.name, card.value)

            markup = types.ReplyKeyboardRemove(selective=False)
            self.bot.send_message(self.group_chat, results, reply_markup=markup)

            self.bot.send_message(winner.uid, 'Вы выиграли!')
            for user in self.users.users:
                if user != winner:
                    self.bot.send_message(user.uid, 'Вы проиграли!')
            return

        self.start_turn()

    def start_turn(self):
        if self.state != 'change_turn' or not self.started:
            return

        self.dealer = self.users.next()
        self.dealer.defence = False

        markup = types.ReplyKeyboardRemove(selective=False)
        self.bot.send_message(self.group_chat, 'Ходит игрок @{}'.format(self.dealer.name), reply_markup=markup)
        self.dealer.take_new_card(self.deck)

        markup = types.ReplyKeyboardMarkup(row_width=2)
        button1 = types.KeyboardButton(self.dealer.card.name)
        button2 = types.KeyboardButton(self.dealer.new_card.name)
        markup.add(button1, button2)

        self.bot.send_message(self.dealer.private_chat, 'Выберите карту которой хотите сыграть:', reply_markup=markup)
        self.state = 'select_card'

    def select_card(self, card_type):
        if self.state != 'select_card':
            return

        if card_type in ['Принц', 'Король'] and 'Графиня' in [self.dealer.card.name, self.dealer.new_card.name]:
            self.bot.send_message(self.dealer.uid, 'Ай-ай-ай... Необходимо скинуть графиню.')
            return

        if card_type != self.dealer.new_card.name:
            self.dealer.new_card, self.dealer.card = self.dealer.card, self.dealer.new_card
        
        if self.dealer.new_card.need_victim:
            markup = types.ReplyKeyboardMarkup()
            self.no_victims = True
            for user in self.users.users:
                if not user.defence and user.uid != self.dealer.uid:
                    button = types.KeyboardButton(user.name)
                    markup.add(button)
                    self.no_victims = False

            if self.no_victims:
                button = types.KeyboardButton(self.dealer.name)
                markup.add(button)

            self.bot.send_message(self.dealer.private_chat,
                                  'Выберите против кого использовать карту:', reply_markup=markup)
            self.state = 'select_victim'
            return

        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)
        active_card.activate(self)
        self.state = 'change_turn'
        self.check_end()

    def select_victim(self, victim_name):
        if self.state != 'select_victim':
            return
        
        for user in self.users.users:
            if user.name == victim_name:
                self.victim = user

        if self.dealer.new_card.need_guess:
            markup = types.ReplyKeyboardMarkup()
            for card in card_names[:-1]:
                button = types.KeyboardButton(card)
                markup.add(button)
            self.bot.send_message(self.dealer.private_chat,
                                  'Угадайте карту @{}:'.format(self.victim.name), reply_markup=markup)
            self.state = 'guess_card'
            return

        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)
        active_card.activate(self)
        self.state = 'change_turn'
        self.check_end()

    def guess_card(self, guess):
        if self.state != 'guess_card':
            return

        self.guess = guess
        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)
        active_card.activate(self)
        self.state = 'change_turn'
        self.check_end()

    def end(self):
        self.started = False


class Users:
    def __init__(self):
        self.users = []
        self.next_dealer = 0

    def add(self, user):
        self.users.append(user)

    def shuffle(self):
        random.shuffle(self.users)

    def next(self):
        self.next_dealer = (self.next_dealer + 1) % len(self.users)
        return self.users[self.next_dealer - 1]

    def __contains__(self, user):
        return user in self.users

    def kill(self, user):
        user.bot.send_message(user.uid, 'Вы проиграли')
        if self.next_dealer > self.users.index(user):
            self.next_dealer -= 1
        self.users.remove(user)

    def get_victims(self, dealer):
        victims = []
        for user in self.users:
            if not user.defence and user.uid != dealer.uid:
                victims.append(user.name)
        return victims


class User:
    def __init__(self, name, uid, bot):
        self.name = name
        self.uid = uid
        self.private_chat = uid
        print(self.private_chat)
        print(self.uid)
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
            return self.uid == other.uid
        return self.uid == other
        
    def __ne__(self, other):
        return not self == other 

