card_names = ['Принцесса', 'Графиня', 'Король', 'Принц', 'Служанка', 'Барон', 'Священник', 'Стражница']


class Card:
    value = None
    need_victim = False
    need_guess = False
    owner = None

    def activate(self, game):
        pass

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
    name = 'Принцесса'
    value = 8

    def activate(self, game):
        game.bot.send_message(game.group_chat, '@{} сбросил Принцессу и проиграл.'.format(self.owner.name))
        game.used_cards.append(self.owner.card)
        game.users.kill(self.owner)


class Countess(Card):
    name = 'Графиня'
    value = 7

    def activate(self, game):
        game.bot.send_message(game.group_chat, '@{} сбросил Графиню.'.format(self.owner.name))


class King(Card):
    name = 'Король'
    value = 6
    need_victim = True

    def activate(self, game):
        game.bot.send_message(game.group_chat,
                              '@{} использовал Короля чтобы обменяться с @{} картами.'.format(self.owner.name,
                                                                                              game.victim.name))
        self.owner, game.victim.card.owner = game.victim.card.owner, self.owner
        self.owner.card, game.victim.card = game.victim.card, self.owner.card
        
        game.bot.send_message(self.owner.uid, 'Вам получили карту "{}" от @{}'.format(self.owner.card.name,
                                                                                      game.victim.name))
        game.bot.send_message(game.victim.uid, 'Вы получили карту "{}" от @{}'.format(game.victim.card.name,
                                                                                      self.owner.name))


class Prince(Card):
    name = 'Принц'
    value = 5
    need_victim = True

    def activate(self, game):
        game.used_cards.append(game.victim.card)
        if game.victim.card.name == 'Принцесса':
            game.bot.send_message(game.group_chat,
                                  '@{0} использовал Принца против @{1}. '
                                  '@{1} Сбрасывает Принцессу и проигрывает.'.format(self.owner.name, game.victim.name))
            game.users.kill(game.victim)
            return

        game.bot.send_message(game.group_chat,
                              '@{0} использовал Принца против @{1}. У @{1} был(а) {2}.'.format(self.owner.name,
                                                                                               game.victim.name,
                                                                                               game.victim.card.name))
        if len(game.deck) == 0:
            game.deck.append(game.first_card)

        game.victim.take_card(game.deck)


class Maid(Card):
    name = 'Служанка'
    value = 4

    def activate(self, game):
        game.bot.send_message(game.group_chat, '@{} защищен Служанкой в течение круга.'.format(self.owner.name))
        self.owner.defence = True


class Baron(Card):
    name = 'Барон'
    value = 3
    need_victim = True

    def activate(self, game):
        if self.owner.card > game.victim.card:
            game.bot.send_message(game.group_chat,
                                  '@{0} использует Барона против @{1} и выигрывает. '
                                  'У @{1} оказалась карта "{2}"'.format(self.owner.name,
                                                                        game.victim.name, game.victim.card.name))
            game.used_cards.append(game.victim.card)
            game.users.kill(game.victim)
        elif self.owner.card < game.victim.card:
            game.bot.send_message(game.group_chat,
                                  '@{0} использует Барона против @{1}, но проигрывает. '
                                  'у {0} оказалась карта "{2}"'.format(self.owner.name,
                                                                       game.victim.name, self.owner.card.name))
            game.used_cards.append(self.owner.card)
            game.users.kill(self.owner)
        else:
            game.bot.send_message(game.group_chat,
                                  'похоже у @{} и @{} одинаковые карты... '
                                  'Барон уходит впустую.'.format(self.owner.name, game.victim.name))


class Priest(Card):
    name = 'Священник'
    value = 2
    need_victim = True

    def activate(self, game):
        game.bot.send_message(game.group_chat,
                              '@{} сбрасывает Священника и смотрит карту @{}.'.format(self.owner.name,
                                                                                      game.victim.name))
        game.bot.send_message(self.owner.uid,
                              '@{} показывает Вам свою карту. У него(нее) {}.'.format(game.victim.name,
                                                                                      game.victim.card.name))


class Guard(Card):
    name = 'Стражница'
    value = 1
    need_victim = True
    need_guess = True

    def activate(self, game):
        if game.victim.card.name == game.guess:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Стражницу и угадывает что у @{} {}.'.format(self.owner.name,
                                                                                              game.victim.name,
                                                                                              game.guess))
            game.used_cards.append(game.victim.card)
            game.users.kill(game.victim)
        else:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Стражницу, предполагая '
                                  'что у @{} {}, но не угадывает.'.format(self.owner.name,
                                                                          game.victim.name,
                                                                          game.guess))
