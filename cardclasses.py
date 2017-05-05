card_names = ['Принцесса', 'Графиня', 'Король', 'Принц', 'Служанка', 'Барон', 'Священник', 'Стражница']
from telebot import types

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
        markup = types.ReplyKeyboardRemove(selective=False)
        game.bot.send_message(game.group_chat, '@{} сбрасывает Принцессу и проигрывает.'.format(self.owner.name))
        game.bot.send_message(self.owner.uid, '@{} сбрасывает Принцессу и проигрывает.'.format(self.owner.name),
                              reply_markup=markup)
        game.used_cards.append(self.owner.card)
        game.users.kill(self.owner)


class Countess(Card):
    name = 'Графиня'
    value = 7

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        game.bot.send_message(game.group_chat, '@{} сбрасывает Графиню.'.format(self.owner.name))
        game.bot.send_message(self.owner.uid, '@{} сбрасывает Графиню.'.format(self.owner.name), reply_markup=markup)


class King(Card):
    name = 'Король'
    value = 6
    need_victim = True

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Короля впустую.'.format(
                                      self.owner.name))
            game.bot.send_message(self.owner.uid,
                                  '@{} использует Короля впустую.'.format(
                                      self.owner.name),
                                  reply_markup=markup)
        else:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Короля чтобы обменяться с @{} картами.'.format(self.owner.name,
                                                                                                  game.victim.name))
            game.bot.send_message(self.owner.uid,
                                  '@{} использует Короля чтобы обменяться с @{} картами.'.format(self.owner.name,
                                                                                                  game.victim.name),
                                  reply_markup=markup)

            game.bot.send_message(game.dealer.uid, 'Вы получили карту "{}" от @{}'.format(game.victim.card.name,
                                                                                          game.victim.name))
            game.bot.send_message(game.victim.uid, 'Вы получили карту "{}" от @{}'.format(game.dealer.card.name,
                                                                                          game.dealer.name))

            game.dealer.card.owner = game.victim
            game.victim.card.owner = game.dealer
            game.dealer.card, game.victim.card = game.victim.card, game.dealer.card


class Prince(Card):
    name = 'Принц'
    value = 5
    need_victim = True

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        game.used_cards.append(game.victim.card)
        if game.victim.card.name == 'Принцесса':
            game.bot.send_message(game.group_chat,
                                  '@{0} использует Принца против @{1}. '
                                  '@{1} Сбрасывает Принцессу и проигрывает.'.format(self.owner.name, game.victim.name))
            game.bot.send_message(self.owner.uid,
                                  '@{0} использует Принца против @{1}. '
                                  '@{1} Сбрасывает Принцессу и проигрывает.'.format(self.owner.name, game.victim.name),
                                  reply_markup=markup)
            game.users.kill(game.victim)
            return

        game.bot.send_message(game.group_chat,
                              '@{0} использует Принца против @{1}. У @{1} был(а) {2}.'.format(self.owner.name,
                                                                                               game.victim.name,
                                                                                               game.victim.card.name))
        game.bot.send_message(self.owner.uid,
                              '@{0} использует Принца против @{1}. У @{1} был(а) {2}.'.format(self.owner.name,
                                                                                               game.victim.name,
                                                                                               game.victim.card.name),
                              reply_markup=markup)
        if len(game.deck) == 0:
            game.deck.append(game.first_card)

        game.victim.take_card(game.deck)


class Maid(Card):
    name = 'Служанка'
    value = 4

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)
        game.bot.send_message(game.group_chat, '@{} защищен Служанкой в течение круга.'.format(self.owner.name))
        game.bot.send_message(self.owner.uid, '@{} защищен Служанкой в течение круга.'.format(self.owner.name),
                              reply_markup=markup)
        self.owner.defence = True


class Baron(Card):
    name = 'Барон'
    value = 3
    need_victim = True

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Барона впустую.'.format(
                                      self.owner.name))
            game.bot.send_message(self.owner.uid,
                                  '@{} использует Барона впустую.'.format(
                                      self.owner.name),
                                  reply_markup=markup)
        else:
            if self.owner.card > game.victim.card:
                game.bot.send_message(game.group_chat,
                                      '@{0} использует Барона против @{1} и выигрывает. '
                                      'У @{1} оказалась карта "{2}"'.format(self.owner.name,
                                                                            game.victim.name, game.victim.card.name))
                game.bot.send_message(self.owner.uid,
                                      '@{0} использует Барона против @{1} и выигрывает. '
                                      'У @{1} оказалась карта "{2}"'.format(self.owner.name,
                                                                            game.victim.name, game.victim.card.name),
                                      reply_markup=markup)
                game.used_cards.append(game.victim.card)
                game.users.kill(game.victim)
            elif self.owner.card < game.victim.card:
                game.bot.send_message(game.group_chat,
                                      '@{0} использует Барона против @{1}, но проигрывает. '
                                      'у {0} оказалась карта "{2}"'.format(self.owner.name,
                                                                           game.victim.name, self.owner.card.name))
                game.bot.send_message(self.owner.uid,
                                      '@{0} использует Барона против @{1}, но проигрывает. '
                                      'у {0} оказалась карта "{2}"'.format(self.owner.name,
                                                                           game.victim.name, self.owner.card.name),
                                      reply_markup=markup)
                game.used_cards.append(self.owner.card)
                game.users.kill(self.owner)
            else:
                game.bot.send_message(game.group_chat,
                                      'похоже у @{} и @{} одинаковые карты... '
                                      'Барон уходит впустую.'.format(self.owner.name, game.victim.name))
                game.bot.send_message(self.owner.uid,
                                      'похоже у @{} и @{} одинаковые карты... '
                                      'Барон уходит впустую.'.format(self.owner.name, game.victim.name),
                                      reply_markup=markup)


class Priest(Card):
    name = 'Священник'
    value = 2
    need_victim = True

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Священника впустую.'.format(
                                      self.owner.name))
            game.bot.send_message(self.owner.uid,
                                  '@{} использует Священника впустую.'.format(
                                      self.owner.name),
                                  reply_markup=markup)
        else:
            game.bot.send_message(game.group_chat,
                                  '@{} сбрасывает Священника и смотрит карту @{}.'.format(self.owner.name,
                                                                                          game.victim.name))
            game.bot.send_message(self.owner.uid,
                                  '@{} сбрасывает Священника и смотрит карту @{}.'.format(self.owner.name,
                                                                                          game.victim.name),
                                  reply_markup=markup)
            game.bot.send_message(self.owner.uid,
                                  '@{} показывает Вам свою карту. У него(нее) {}.'.format(game.victim.name,
                                                                                          game.victim.card.name))


class Guard(Card):
    name = 'Стражница'
    value = 1
    need_victim = True
    need_guess = True

    def activate(self, game):
        markup = types.ReplyKeyboardRemove(selective=False)

        if game.card_without_action:
            game.bot.send_message(game.group_chat,
                                  '@{} использует Стражницу впустую.'.format(
                                      self.owner.name))
            game.bot.send_message(self.owner.uid,
                                  '@{} использует Стражницу впустую.'.format(
                                      self.owner.name),
                                  reply_markup=markup)
        else:
            if game.victim.card.name == game.guess:
                game.bot.send_message(game.group_chat,
                                      '@{} использует Стражницу и угадывает что у @{} {}.'.format(self.owner.name,
                                                                                                  game.victim.name,
                                                                                                  game.guess))
                game.bot.send_message(self.owner.uid,
                                      '@{} использует Стражницу и угадывает что у @{} {}.'.format(self.owner.name,
                                                                                                  game.victim.name,
                                                                                                  game.guess),
                                      reply_markup=markup)
                game.used_cards.append(game.victim.card)
                game.users.kill(game.victim)
            else:
                game.bot.send_message(game.group_chat,
                                      '@{} использует Стражницу, предполагая '
                                      'что у @{} {}, но не угадывает.'.format(self.owner.name,
                                                                              game.victim.name,
                                                                              game.guess))
                game.bot.send_message(self.owner.uid,
                                      '@{} использует Стражницу, предполагая '
                                      'что у @{} {}, но не угадывает.'.format(self.owner.name,
                                                                              game.victim.name,
                                                                              game.guess),
                                      reply_markup=markup)
