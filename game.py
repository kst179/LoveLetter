import random
from cards import *
from telebot import types


class Game:
    def __init__(self, bot, chat_id):
        self.bot = bot
        self.chat_id = chat_id
        self.users = Users()
        self.started = False
        self.deck = self.generate_deck()
        self.used_cards = []
        self.dealer = None
        self.victim = None
        self.guess = None
        self.first_card = None
        self.can_choose_yourself = False
        self.card_without_action = False
        self.double_deck = False
        self.state = 'change_turn'
        self.bot.send_message(self.chat_id, 'Игра создана.')

    def start(self):
        if len(self.users.users) < 2:
            self.bot.send_message(self.chat_id, 'Слишком мало игроков, должно быть минимум 2.')
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
        self.bot.send_message(self.chat_id, users)

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


            self.bot.send_message(self.chat_id, results)

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

        self.bot.send_message(self.chat_id, 'Ходит игрок @{}.'.format(self.dealer.name))
        self.dealer.take_new_card(self.deck)
        if len(self.deck) > 0:
            self.bot.send_message(self.chat_id, 'В колоде осталось {} карт.'.format(len(self.deck)))
        else:
            self.bot.send_message(self.chat_id, 'Внимание! Последний ход.')

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

    @staticmethod
    def generate_deck():
        return [
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
            *(Guard() for i in range(5))
        ]
