from itertools import combinations, product
import random

class Card:
    def __init__(self, card_type):
        self.rank = card_type[0].upper()
        self.suit = card_type[1].lower()
        self.rank_number = '..23456789TJQKA'.index(self.rank)
        self.suit_number = int('cshd'.index(self.suit))
        self.suit_symbol = '♣♠♥♦'[self.suit_number]
    
    def __repr__(self):
        return f'{self.__class__.__name__}{self.rank, self.suit}'

    def __str__(self):
        return f'[ {self.rank}  {self.suit_symbol} ]'


class Evaluator:
    def __init__(self):
        self.rank_meanings = {9: "Royal Flush",
                              8: "Straight Flush",
                              7: "Four of a Kind",
                              6: "Full House",
                              5: "Flush",
                              4: "Straight",
                              3: "Three of a Kind",
                              2: "Two Pair",
                              1: "One Pair",
                              0: "High Card",}

    def evaluate(self, cards):
        hand = max(combinations(cards, 5), key=self._get_evaluation_score)
        rank_evaluation = self._get_evaluation_score(hand)
        return rank_evaluation

    def _get_evaluation_score(self, hand):
        ranks = self._ranks(hand)
        unique = list(set(ranks))
        if self._straight(ranks) and self._flush(hand):
            if max(ranks) == 14:
                return (9)
            return (8, max(ranks))
        elif self._kind(4, ranks):
            return (7, self._kind(4, ranks), self._kind(1, ranks))
        elif self._kind(3, ranks) and self._kind(2, ranks):
            return (6, self._kind(3, ranks), self._kind(2, ranks))
        elif self._flush(hand):
            return (5, ranks)
        elif self._straight(ranks):
            return (4, max(ranks))
        elif self._kind(3, ranks):
            return (3, self._kind(3, ranks), ranks)
        elif self._two_pair(ranks):
            return (2, self._two_pair(ranks), ranks)
        elif self._kind(2, ranks):
            return (1, self._kind(2, ranks), ranks)
        else:
            return (0, ranks)

    def _ranks(self, hand):
        return sorted([card.rank_number for card in hand], reverse=True)
    
    def _full_house(self, ranks):
        return self._kind(3, ranks) and self._kind(2, ranks)
    
    def _flush(self, hand):
        return len(set(card.suit for card in hand)) == 1

    def _straight(self, ranks):
        return sorted(ranks) == list(range(min(ranks), max(ranks)+1))
    
    def _two_pair(self, ranks):
        tp = sorted([r for r in set(ranks) if ranks.count(r) == 2], reverse=True)
        if len(tp) == 2:
            return tp
        else:
            return []
    
    def _kind(self, size, ranks):
        return ([r for r in set(ranks) if ranks.count(r) == size] + [0])[0]


class Deck:
    def __init__(self):
        self.refill()
    
    def draw(self, amount):
        return [self._deck.pop(random.randrange(len(self._deck))) for _ in range(amount)]
    
    def refill(self):
        suits = 'cshd'
        ranks = '23456789TJQKA'
        self._deck = [Card(''.join([r, s])) for r, s in product(ranks, suits)]
        random.shuffle(self._deck)


class Player:
    def __init__(self, id):
        self.id = id
        self.hand = []
        self.chips = 0
        self._bet = 0
        self.dealer = False
        self.made_action = False
        self.folded = False
        self.total_bet = 0
    
    @property
    def bet(self):
        return self._bet
    
    @bet.setter
    def bet(self, value):
        difference = value - self._bet
        if difference > 0:
            self.total_bet += difference
        self._bet = value
    
    def __repr__(self):
        return f'{self.__class__.__name__}(\'{self.name}\')'
    
    @property
    def full_name(self):
        n = self.name
        if self.dealer:
            n += ' (D)'
        return n


class Game:
    def __init__(self, players=[], chips=10000):
        self.players = players
        self.deck = Deck()
        self.evaluator = Evaluator()
        self.chips = chips
        self.small_blind = round(self.chips / 200, -1)
        self.big_blind = self.small_blind * 2
        self.board = []
        self.round_ended = False
        self.round_win_info = {}
        self.current_bet = 0
        self.pot = 0
        self.current_player = None

        if players:
            self.initialize_game()

    def players_to_act(self):
        while not all(p.made_action and (p.bet == self.current_bet or not p.chips) or p.folded 
                      for p in self.players):
            yield self.current_player

    def deal(self):
        for player in self.players:
            player.hand = self.deck.draw(2)
    
    def initialize_game(self):
        if not any(p.dealer for p in self.players):
            random.choice(self.players).dealer = True
            
        self.players = self.players

        for player in self.players:
            player.chips = self.chips

    def initialize_round(self):
        self.deck.refill()
        self.deal()
        self.pot = 0
        self.board = []
        self.current_bet = 0

        for player in self.players:
            player.folded = False
            player.total_bet = 0
            player.bet = 0

        while self.players[-1].dealer is False:
            self.players.append(self.players.pop(0))
        
        self.players[-1].dealer = False
        self.players[0].dealer = True
        
        if len(self.players) > 2:
            self.current_player = self.players[1]
        else:
            self.current_player = self.players[0]
        sb = self.current_player
        self.bet(self.current_player, self.small_blind)
        bb = self.current_player
        self.bet(self.current_player, self.big_blind)
        sb.made_action = False
        bb.made_action = False

        self.round_ended = False

    def evaluate_player(self, player):
        return self.evaluator.evaluate(player.hand + self.board)

    def generate_side_pots(self):
        side_pots = {}
        pot_order = sorted(self.players, key=lambda x: x.total_bet)
        pot_dict = dict((x.total_bet, y+1) for y, x in enumerate(reversed(pot_order)))
        total_bet_delta = 0
        for n, player in enumerate(pot_order):
            amount = (player.total_bet + total_bet_delta) * pot_dict[player.total_bet]
            if amount <= 0:
                continue
            side_pots[amount] = [x for x in pot_order[n:] if not x.folded]
            total_bet_delta -= player.total_bet + total_bet_delta

        for amount, players in side_pots.items():
            if len(players) == 1:
                players[0].chips += amount
                side_pots.pop(amount)

        return side_pots

    def finish_round(self):
        side_pots = self.generate_side_pots()
        earnings = {}
        for amount, players in side_pots.items():
            winners = []
            winning_hand = ()
            for p in players:
                evaluation = self.evaluate_player(p)
                if evaluation > winning_hand:
                    winning_hand = evaluation
                    winners = [p]
                elif evaluation == winning_hand:
                    winners.append(p)
            for w in winners:
                win_reason = self.evaluator.rank_meanings[winning_hand[0]]
                earnings[amount // len(winners)] = (w, win_reason)
        
        for amount, information in earnings.items():
            player, win_reason = information
            player.chips += amount
        
        self.players = [p for p in self.players if p.chips > 0]

        self.round_win_info = earnings
        self.round_ended = True

    def check(self, player):
        if player.bet == self.current_bet:
            self.rotate_player()
        else:
            raise ValueError("You can only check if no one else has bet more than what you have bet")
    
    def call(self, player):
        if player.bet < self.current_bet:
            if player.chips >= self.current_bet:
                difference = self.current_bet - player.bet
                player.bet = self.current_bet
                player.chips -= difference
            else:
                difference = player.chips
                player.bet += player.chips
                player.chips = 0
            self.pot += difference
            self.rotate_player()
        else:
            raise ValueError("You can't call when no one else has bet more than you")
    
    def bet(self, player, amount):
        if amount >= self.current_bet * 2:
            if player.chips >= amount:
                difference = amount - player.bet
                player.bet = amount
                player.chips -= difference
            else:
                difference = player.chips
                player.bet += player.chips
                player.chips = 0
            self.pot += difference
            self.current_bet = player.bet
            self.rotate_player()
        else:
            raise ValueError("The bet amount must be atleast double the current bet")
    
    def fold(self, player):
        self.rotate_player()
        player.folded = True
    
    def rotate_player(self):
        while True:
            self.current_player.made_action = True
            current_player = self.players.index(self.current_player)
            next_player = 0 if current_player + 1 == len(self.players) else current_player + 1
            self.current_player = self.players[next_player]
            if not self.current_player.folded:
                break
    
    def next_betting_round(self):
        if not len(self.board):
            self.board += self.deck.draw(3)
        elif len(self.board) < 5:
            self.board += self.deck.draw(1)
        else:
            self.finish_round()
        
        for player in self.players:
            player.bet = 0
            player.made_action = False

        self.current_bet = 0

        d = self.current_player = self.players[0]
        self.rotate_player()
        d.made_action = False