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