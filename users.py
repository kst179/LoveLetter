from gettext import gettext as _


class User:
    """
    class that represents a player

    :attr name:
        user's @nickname from telegram
    :attr user_id:
        inner telegram id, used for writing
        private messages to user
    :attr bot:
        link to the bot which handles game where
        this user is playing
    :attr card:
        currently card on the user's hand
    :attr new_card:
        card that was taken to hand on the move
    :attr defence:
        is this user protected by 'Maid' card
    """
    def __init__(self, name, user_id, bot):
        """
        Creates a new user
        As soon as user can be created only
        before the game starts, all game attrs (such as card,
        new_card and defence) are set to None

        :param name:
            user's @nickname from telegram
        :param user_id:
            inner telegram id, used for writing
            private messages to user
        :param bot:
            link to the bot which handles game where
            this user is playing
        """
        self.name = name
        self.user_id = user_id
        self.private_chat = user_id
        self.bot = bot
        self.card = None
        self.new_card = None
        self.defence = False

    def take_card(self, deck):
        """
        Takes a top card from the deck,
        if user currently not holding any cards
        (at start of the game or after he drops all his cards)

        :param deck:
            list of Cards, deck from where the card is taken
        """

        self.card = deck[-1]
        self.card.owner = self
        del deck[-1]
        self.bot.send_message(self.private_chat, _("Your card is '{}'").format(self.card.name))

    def take_new_card(self, deck):
        """
        Take new card on user's turn, so he handle
        two cards at the same time. One of the cards must be played
        on this turn

        :param deck:
            list of Cards, deck from where the card is taken
        """

        self.new_card = deck[-1]
        self.new_card.owner = self
        del deck[-1]
        self.bot.send_message(self.private_chat, _("You have taken the '{}' card").format(self.new_card.name))

    def __eq__(self, other):
        if isinstance(other, User):
            return self.user_id == other.user_id
        return self.user_id == other

    def __ne__(self, other):
        return not self == other


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
        user.bot.send_message(user.uid, _("You've lost!"))
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
