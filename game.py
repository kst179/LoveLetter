import random
from cardclasses import *
from telebot import types


def generate_deck():
    return [Princess(),
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
            Guard()]


class Game:
    def __init__(self, bot, group_chat):
        self.bot = bot
        self.group_chat = group_chat
        self.users = Users()
        self.started = False
        self.deck = generate_deck()
        self.used_cards = []
        self.dealer = None
        self.victim = None
        self.guess = None
        self.first_card = None
        self.can_choose_yourself = False
        self.card_without_action = False
        self.double_deck = False
        self.state = 'change_turn'
        self.bot.send_message(self.group_chat, 'Игра создана.')

    def start(self):
        if len(self.users.users) < 2:
            self.bot.send_message(self.group_chat, 'Слишком мало игроков, должно быть минимум 2.')
            return

        if self.double_deck:
            self.deck.extend(generate_deck())
        random.shuffle(self.deck)
        self.first_card = self.deck[-1]
        del self.deck[-1]
        self.users.shuffle()
        for user in self.users.users:
            user.take_card(self.deck)
        self.started = True
        self.state = 'change_turn'
        users = 'Игра началась.\nПорядок игроков:\n'
        for num, user in enumerate(self.users.users):
            if num == 0:
                users += ' - {} <<\n'.format(user.name)
            else:
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


            self.bot.send_message(self.group_chat, results)

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

        self.bot.send_message(self.group_chat, 'Ходит игрок @{}.'.format(self.dealer.name))
        self.dealer.take_new_card(self.deck)
        if len(self.deck) > 0:
            self.bot.send_message(self.group_chat, 'В колоде осталось {} карт.'.format(len(self.deck)))
        else:
            self.bot.send_message(self.group_chat, 'Внимание! Последний ход.')

        markup = types.ReplyKeyboardMarkup(row_width=2)
        button1 = types.KeyboardButton(self.dealer.card.name)
        button2 = types.KeyboardButton(self.dealer.new_card.name)
        markup.add(button1, button2)

        self.state = 'select_card'
        self.bot.send_message(self.dealer.private_chat, 'Выберите карту которой хотите сыграть:', reply_markup=markup)

    def select_card(self, card_type):
        if self.state != 'select_card':
            return

        if card_type in ['Принц', 'Король'] and 'Графиня' in [self.dealer.card.name, self.dealer.new_card.name]:
            self.bot.send_message(self.dealer.uid, 'Ай-ай-ай... Необходимо скинуть графиню.')
            return

        if card_type != self.dealer.new_card.name:
            self.dealer.new_card, self.dealer.card = self.dealer.card, self.dealer.new_card
        
        if self.dealer.new_card.need_victim:
            self.state = 'select_victim'

            self.can_choose_yourself = False
            self.card_without_action = False
            markup = types.ReplyKeyboardMarkup()
            possible_victims = self.list_of_possible_victims()
            for user_name in possible_victims:
                button = types.KeyboardButton(user_name)
                markup.add(button)

            if not self.card_without_action:
                self.bot.send_message(self.dealer.private_chat,
                                      'Выберите, против кого использовать карту:', reply_markup=markup)
                return

        self.state = 'change_turn'

        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)
        active_card.activate(self)
        self.check_end()

    def select_victim(self, victim_name):
        if self.state != 'select_victim':
            return
        
        for user in self.users.users:
            if user.name == victim_name:
                self.victim = user

        if self.card_without_action:
            self.state = 'change_turn'

            active_card = self.dealer.new_card
            self.dealer.new_card = None
            self.used_cards.append(active_card)
            active_card.activate(self)
            self.check_end()
        else:
            if self.dealer.new_card.need_guess:
                self.state = 'guess_card'

                markup = types.ReplyKeyboardMarkup()
                for card in card_names[:-1]:
                    button = types.KeyboardButton(card)
                    markup.add(button)
                self.bot.send_message(self.dealer.private_chat,
                                      'Угадайте карту @{}:'.format(self.victim.name), reply_markup=markup)
                return
            self.state = 'change_turn'

            active_card = self.dealer.new_card
            self.dealer.new_card = None
            self.used_cards.append(active_card)
            active_card.activate(self)
            self.check_end()

    def guess_card(self, guess):
        if self.state != 'guess_card':
            return
        self.state = 'change_turn'

        self.guess = guess
        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)
        active_card.activate(self)
        self.check_end()

    def end(self):
        self.started = False

    def list_of_possible_victims(self):
        list_of_victims = []
        for user in self.users.users:
            if not user.defence and user.uid != self.dealer.uid:
                    list_of_victims.append(user.name)
        if self.dealer.new_card == 'Принц' or len(list_of_victims) == 0:
            list_of_victims.append(self.dealer.name)
            if self.dealer.new_card != 'Принц':
                self.card_without_action = True
            else:
                self.can_choose_yourself = True

        return list_of_victims

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
        user.bot.send_message(user.uid, 'Вы проиграли!')
        if self.next_dealer > self.users.index(user):
            self.next_dealer -= 1
        self.users.remove(user)

    def get_victims(self, dealer):
        victims = []
        for user in self.users:
            if not user.defence and user.uid != dealer.uid:
                victims.append(user.name)
        return victims

    def num_users(self):
        return len(self.users)


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
