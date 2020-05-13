"""
Module that contains classes representing love letter's cards
"""

from gettext import gettext as _
from telebot import types


card_names = [
    'Принцесса',
    'Графиня',
    'Король',
    'Принц',
    'Служанка',
    'Барон',
    'Священник',
    'Стражница'
]


class Card:
    """
    An abstract class that represents the arbitrary card
    """

    def __init__(self, name, value, need_victim=False, need_guess=False):
        """
        Creates a card, used by inherited card classes
        to create a card with specific name and value

        :param name:
            str, name of the card, needs to
            display in chat, which card is played right now
        :param value:
            int, value of the card, at end of the game
            the player with largest card value is won
        :param need_victim:
            bool, checks if dealer needs to select another
            player for which this card feature is applied
        :param need_guess:
            bool, checks if dealer needs to guess which
            card is in victim's hands
        :param owner:
            User, owner of the card (who holding it right now)
            or None if the card still lies in deck
        """

        self.name = name
        self.value = value
        self.need_victim = need_victim
        self.need_guess = need_guess
        self.owner = None

    def play(self, game):
        """
        Virtual function, that plays this card
        within given game and applies feature of specific card

        :param game:
            Game, game in which this card is played
        """

        raise NotImplementedError

    def __eq__(self, other):
        return self.name == other

    def __le__(self, other):
        return self.value <= other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value


class Princess(Card):
    """
    Princess card

    The Princess is most powerful card because player who holds it
    at the end of the game definitely wins. But if player accidentally
    drop this card he would instantly loose. As soon as playing this card
    assumes, you should drop it from hand, playing it is surely a suicide)
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Princess"), 8)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        message = _("@{} drops a Princess and loses.").format(self.owner.name)

        game.bot.send_message(game.group_chat, message)
        game.bot.send_message(self.owner.user_id, message, reply_markup=markup)
        game.used_cards.append(self.owner.card)
        game.users.kill(self.owner)


class Countess(Card):
    """
    Countess card

    Has the less power than Princess, but still it better than other cards
    Just drop it you wanna play it. Yes it does absolutely nothing, if you don't
    count that it must be played if you have King or Prince cards (and actually Princess too)
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Countess"), 7)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        message = _("@{} drops a Countess.").format(self.owner.name)

        game.bot.send_message(game.group_chat,)
        game.bot.send_message(self.owner.user_id, message, reply_markup=markup)


class King(Card):
    """
    The King card

    King has less value than Countess but greater than Prince's one
    Playing the King means you drop him from hand and change your second card with
    selected player's one
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("King"), 6, need_victim=True)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            message = \
                _("@{} drops the King because all players are protected.").format(self.owner.name)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)
        else:
            message = \
                _("@{0} plays the King to exchange cards with @{1}.").format(self.owner.name,
                                                                             game.victim.name)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

            message = _("You've got a {} from player @{}").format(game.victim.card.name,
                                                                  game.victim.name)

            game.bot.send_message(game.dealer.user_id, message)
            game.bot.send_message(game.victim.user_id, message)

            game.dealer.card.owner = game.victim
            game.victim.card.owner = game.dealer
            game.dealer.card, game.victim.card = game.victim.card, game.dealer.card


class Prince(Card):
    """
    The Prince card

    Prince stands one step over Maid but one step below the King
    This card allows you to make one other player to drop off his card
    (note it: if he has the Princess, he will loose), and take a new one from deck.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Prince"), 5, need_victim=True)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        game.used_cards.append(game.victim.card)

        if isinstance(game.victim.card, Princess):
            message = _("@{0} uses Prince against @{1}. "
                        "@{1} drops a Princess and loses!").format(self.owner.name,
                                                                   game.victim.name)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)
            game.users.kill(game.victim)
            return

        message = \
            _("@{0} uses a Prince against @{1}. @{1} has the {2}.").format(self.owner.name,
                                                                           game.victim.name,
                                                                           game.victim.card.name)

        game.bot.send_message(game.group_chat, message)
        game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

        if not game.deck:
            game.deck.append(game.first_card)

        game.victim.take_card(game.deck)


class Maid(Card):
    """
    The Maid card

    The fourth card in the hierarchy
    Using this card makes you protected from actions of
    any targeted cards for the entire round (till your next turn)
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Maid"), 4)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        message = _("@{} is under Maid protection for a one full round.").format(self.owner.name)

        game.bot.send_message(game.group_chat, message)
        game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

        self.owner.defence = True


class Baron(Card):
    """
    The Baron card

    The third card by it's power
    Playing it allowes you to take out any player, but only if
    your second card (that remains in your hand) is greater than card
    which this player holds, else you will take out yourself.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Baron"), 3, need_victim=True)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            message = \
                _("@{} drops a Baron, because all players are protected.").format(self.owner.name)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)
        else:
            if self.owner.card > game.victim.card:
                message = _("@{0} uses the Baron against @{1} and wins. "
                            "@{1} has the {2} card").format(self.owner.name, game.victim.name,
                                                            game.victim.card.name)

                game.bot.send_message(game.group_chat, message)
                game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

                game.used_cards.append(game.victim.card)
                game.users.kill(game.victim)

            elif self.owner.card < game.victim.card:
                message = _("@{0} uses the Baron against @{1}, but looses. "
                            "@{0} has the {2} card").format(self.owner.name, game.victim.name,
                                                            self.owner.card.name)

                game.bot.send_message(game.group_chat, message)
                game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

                game.used_cards.append(self.owner.card)
                game.users.kill(self.owner)
            else:
                message = \
                    _("Aaaand... here goes nothing"
                      "Looks like @{0} and @{1} have the same cards... ").format(self.owner.name,
                                                                                 game.victim.name)

                game.bot.send_message(game.group_chat, message)
                game.bot.send_message(self.owner.user_id, message, reply_markup=markup)


class Priest(Card):
    """
    The Priest card

    Not very strong card (actually it can beat only Guard)
    but it allows you to peek anyone else's card, you just need to play it
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Priest"), 2, need_victim=True)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            message = \
                _("@{} drops Priest, because all players are protected.").format(self.owner.name)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

            return

        message = _("@{} uses a Priest card and looks at @{}'s card.").format(self.owner.name,
                                                                              game.victim.name)

        game.bot.send_message(game.group_chat, message)
        game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

        message = _("@{} показывает Вам свою карту. У него(нее) {}.").format(game.victim.name,
                                                                             game.victim.card.name)
        game.bot.send_message(self.owner.user_id, message)


class Guard(Card):
    """
    The Guard card

    The weakest card in the game, if you finish game with it
    you definitely won't win (only if you don't kicked out other players),
    but it allows you to kick one player from game, you just need to play it
    and guess which card this player holds.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        super().__init__(_("Guard"), 1, need_victim=True, need_guess=True)

    def play(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            message = \
                _("@{} drops the Guard, because all players are protected.").format(self.owner.name)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

            return

        if game.victim.card.name == game.guess:
            message = '@{} использует Стражницу и угадывает что у @{} {}.'.format(self.owner.name,
                                                                                  game.victim.name,
                                                                                  game.guess)

            game.bot.send_message(game.group_chat, message)
            game.bot.send_message(self.owner.user_id, message, reply_markup=markup)

            game.used_cards.append(game.victim.card)
            game.users.kill(game.victim)

            return

        message = _("@{} использует Стражницу, предполагая "
                    "что у @{} {}, но не угадывает.").format(self.owner.name, game.victim.name,
                                                             game.guess)

        game.bot.send_message(game.group_chat, message)
        game.bot.send_message(self.owner.user_id, message, reply_markup=markup)
