# pylint: disable=undefined-variable
# pylint: disable=import-error

"""
Here contains the Game class that represents
the game table and handles all events within one game
"""

import random
from itertools import chain
import gettext

from telebot import types

from loveletter.users import Users
from loveletter.cards import (
    Princess,
    Countess,
    King,
    Prince,
    Maid,
    Baron,
    Priest,
    Guard
)

gettext.install('loveletter', localedir='./loveletter/locale', codeset='UTF-8')


class Game:
    """
    Class that handles one game, a virtual table if you prefer

    Game has several states, running cycle is:

    not_started (initial state) ─→ change_turn
    change_turn ─→ select_card
    select_card ┬→ select_victim (if card is targeted)
                ├→ change_turn
                └→ not_started (if game over)
    select_victim ┬→ guess_card (if card is Guard)
                  ├→ change_turn
                  └→ not_started (if game over)
    guess_card ┬→ change_turn
               └→ not_started (if game over)
    """

    card_types = (
        Princess,
        Countess,
        King,
        Prince,
        Maid,
        Baron,
        Priest,
        Guard,
    )

    def __init__(self, bot):
        """
        Creates a new game

        TODO This class has too many instances and needs to be broken into more abstract subclasses

        :param bot:
            Bot, the bot that handles all the player-to-game interactions
        :param game_id:
            int, unique game id (also user_id of the game creator)
        """

        self.bot = bot
        self.users = Users()
        self.used_cards = []
        self.dealer = None
        self.victim = None
        self.guess = None
        self.first_card = None
        self.can_choose_yourself = False
        self.card_without_action = False
        self.double_deck = False
        self.state = 'not_started'

        self.deck = self.generate_deck()

    def start(self):
        """
        Starts a new game and deals the cards.
        This method must be called after adding
        all players to game and configuring it.

        current_state: not_started
        next_state: change_turn
        """

        if self.state != 'not_started':
            raise RuntimeError('Trying to start a game, when it is already started')

        if self.double_deck:
            self.deck.extend(self.generate_deck())

        random.shuffle(self.deck)
        self.first_card = self.deck.pop()

        self.users.shuffle()
        for user in self.users:
            user.take_card(self.deck)

        message = _("The game is started!\n"
                    "Players order (top moves first):\n")

        for num, user in enumerate(self.users):
            if num == 0:
                message += '\t@{} <<\n'.format(user.name)
            else:
                message += '\t@{}\n'.format(user.name)

        self.public_message(message)

        self.state = 'change_turn'

    def restart(self):
        """
        Restarts the game

        current state: any
        next state: not_started
        """
        self.users.reset()
        self.deck = self.generate_deck()
        self.used_cards = []

        self.state = 'not_started'

        self.start()
        self.start_turn()

    def is_game_over(self):
        """
        Checks if game is over

        game ends if it is only one player left,
        or there is no cards in deck.
        If game is ended, sends game result to chat.
        If game is not ended, starts a new turn

        current state: any
        next state:
            game_over (if game ended)
            change_turn (if game not ended)
        """

        if len(self.users) == 1 or not self.deck:
            players_remains = sorted(self.users, key=lambda user: user.card, reverse=True)
            winner = players_remains[0]

            message = [_("Game is over\n"
                         "Winner is {}\n"
                         "Players remains\n").format(winner.name)]

            for i, user in enumerate(players_remains):
                message.append("\t#{} @{} - {} ({})\n".format(i+1, user.name, user.card.name,
                                                              user.card.value))

            message.append(_("Kicked off the game:\n"))

            for i, user in enumerate(self.users.loosers):
                message.append("\t@{}\n".format(user.name))

            self.public_message(''.join(message))

            self.bot.send_message(winner.user_id, _("Greetings! You've won!"))
            for user in self.users:
                if user != winner:
                    self.bot.send_message(user.user_id, _("You loose!"))

            self.state = 'game_over'

            return

        self.state = 'change_turn'
        self.start_turn()

    def start_turn(self):
        """
        Starts a player's turn

        If player has Maid's defence, removes it,
        sends messages to chat about number of card left and
        current player, make current dealer take new card
        offers player to choose which card to play.

        current state: change_turn
        next state: select_card
        """

        if self.state != 'change_turn':
            raise RuntimeError('Trying to start a turn while not in change_turn state')

        self.dealer = self.users.get_dealer()
        self.dealer.defence = False

        self.public_message(_("@{}'s turn").format(self.dealer.name))
        self.dealer.take_new_card(self.deck)

        if self.deck:
            self.public_message(_("It's {} cards left.").format(len(self.deck)))
        else:
            self.public_message(_("Attention! It's the last turn"))

        markup = types.ReplyKeyboardMarkup(row_width=2)
        button1 = types.KeyboardButton(self.dealer.card.name)
        button2 = types.KeyboardButton(self.dealer.new_card.name)
        markup.add(button1, button2)

        self.dealer_message(_("Choose a card which you want to play:"), markup)

        self.state = 'select_card'

    def select_card(self, card_name):
        """
        Applies card features selected by user in game

        If card is targeted, game changes state to select a victim,

        :param card_name:
            str, name of the card, which player want to play

        current_state: select_card
        next_state:
            select_victim (if card is targeted)
            change_turn (else)
        """
        if self.state != 'select_card':
            raise RuntimeError('Trying to select card while not in select_card state')

        if card_name in [_("Prince"), _("King")] and (isinstance(self.dealer.card, Countess) or
                                                      isinstance(self.dealer.new_card, Countess)):
            self.dealer_message(_("Woopsy-daisy... You need to drop a countess."))
            return

        if card_name != self.dealer.new_card.name:
            self.dealer.new_card, self.dealer.card = self.dealer.card, self.dealer.new_card

        if self.dealer.new_card.targeted:
            self.state = 'select_victim'

            self.can_choose_yourself = False
            self.card_without_action = False

            markup = types.ReplyKeyboardMarkup()
            possible_victims = self.list_possible_victims()

            for user_name in possible_victims:
                button = types.KeyboardButton(user_name)
                markup.add(button)

            if not self.card_without_action:
                self.dealer_message(_("Choose the player you want play this card with:"), markup)
                return

        active_card = self.dealer.new_card

        self.dealer.new_card = None
        self.used_cards.append(active_card)

        active_card.play(self)

        self.state = 'change_turn'
        self.is_game_over()

    def select_victim(self, victim_name):
        """

        :param victim_name:
        :return:
        """

        if self.state != 'select_victim':
            raise RuntimeError("Trying to select a victim, while not in select_victim state")

        self.victim = self.users.find_by_name(victim_name)

        if self.card_without_action:
            active_card = self.dealer.new_card
            self.dealer.new_card = None
            self.used_cards.append(active_card)
            active_card.play(self)
            self.is_game_over()

            self.state = 'change_turn'

            return

        if isinstance(self.dealer.new_card, Guard):
            markup = types.ReplyKeyboardMarkup()

            for card in Game.card_types[:-1]:
                button = types.KeyboardButton(card.name)
                markup.add(button)

            self.dealer_message(_("Guess the @{}'s card:").format(self.victim.name), markup)
            self.state = 'guess_card'
            return

        self.state = 'change_turn'

        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)

        active_card.play(self)
        self.is_game_over()

    def guess_card(self, guess):
        """

        :param guess:
        :return:
        """

        if self.state != 'guess_card':
            raise RuntimeError('Guessing card while not in guess state')

        active_card = self.dealer.new_card
        self.dealer.new_card = None
        self.used_cards.append(active_card)

        self.guess = guess
        active_card.play(self)

        self.is_game_over()

    def list_possible_victims(self):
        """
        Returns a list of possible victims within one game
        Player can be a victim only if he is not defended by Maid
        and he is not a dealer. Howewer if everybody are defended,
        dealer can become the only one victim, or he can use Prince on himself

        :return:
            list, list of victims
        """
        victims_list = []
        for user in self.users:
            if not user.defence and user != self.dealer:
                victims_list.append(user.name)

        if isinstance(self.dealer.new_card, Prince) or len(victims_list) == 0:
            victims_list.append(self.dealer.name)

            if not isinstance(self.dealer.new_card, Prince):
                self.card_without_action = True
            else:
                self.can_choose_yourself = True

        return victims_list

    def public_message(self, message, markup=None, but=None):
        """
        sends message to all users in this game

        :param message:
            message to be sent
        :param markup:
            markup with helper buttons
        :param but:
            int, user_id, who don't need a message
        """

        for user in self.users:
            if but is not None and user == but:
                continue
            self.bot.send_message(user.user_id, message, reply_markup=markup)

        for user in self.users.loosers:
            if but is not None and user == but:
                continue
            self.bot.send_message(user.user_id, message, reply_markup=markup)

    def dealer_message(self, message, markup=None):
        """
        sends message to dealer

        :param message:
            message to be sent
        :param markup:
            markup with helper buttons
        """
        self.bot.send_message(self.dealer.user_id, message, reply_markup=markup)

    def victim_message(self, message, markup=None):
        """
        sends message to victim

        :param message:
           message to be sent
        :param markup:
           markup with helper buttons
        """
        self.bot.send_message(self.victim.user_id, message, reply_markup=markup)

    @staticmethod
    def generate_deck():
        """
        Generates a standard deck of cards

        :return:
            list of Cards, the deck
        """
        return list(chain(*[
            [Card() for _ in range(Card.num_in_deck)]
            for Card in Game.card_types
        ]))
