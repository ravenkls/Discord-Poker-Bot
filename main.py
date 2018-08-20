from poker import Deck, Evaluator
import random


class Player:
    def __init__(self, name):
        self.name = name
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
        if difference < 0:
            self.total_bet += difference
        self._bet = value
    
    def __repr__(self):
        return f'{self.__class__.__name__}(\'{self.name}\')'


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
        self.initialize_game()
        self.current_bet = 0
        self.pot = 0

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
        
        for player in self.players:
            player.folded = False
            player.total_bet = 0

        while self.players[0].dealer is False:
            self.players.append(self.players.pop(0))
        
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

    def finish_round(self):
        side_pots = {}
        pot_order = sorted([x for x in self.players if not x.folded], key=lambda x: x.total_bet)
        total_bet_delta = 0
        for n, player in enumerate(pot_order):
            if player.total_bet == 0:
                continue

            amount = (player.total_bet + total_bet_delta) * len(pot_order[n:])
            side_pots[amount] = pot_order[n:]
            total_bet_delta -= player.total_bet + total_bet_delta
        print(side_pots)
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
                earnings[amount // len(winners)] = (p, win_reason)
        
        for amount, information in earnings.items():
            player, win_reason = information
            player.chips += amount
        
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
                player.chips -= self.current_bet
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
                player.chips -= amount
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
        
        while self.players[0].dealer is False:
            self.players.append(self.players.pop(0))
        
        for player in self.players:
            player.bet = 0
            player.folded = False

        self.current_bet = 0

        d = self.current_player
        self.rotate_player()
        d.made_action = False


players = [Player('John'), Player('Bob'), Player('Daniel'), Player('Matthew')]
game = Game(players=players, chips=10000)


game.initialize_round()
while not game.round_ended:
    for player in game.players_to_act():
        print("===== {} =====".format(player.name))
        print("Pot: {}".format(game.pot))
        print("The Board: {}".format(' '.join(map(str, game.board))))
        print("Current bet: {}".format(game.current_bet))
        print("Your bet: {}".format(player.bet))
        print("Your cards: {}".format(' '.join(map(str, player.hand))))
        print("Your chips: {}".format(player.chips))
        action = input("Action: ")
        if action.startswith('bet'):
            game.bet(player, int(action.split()[1]))
        elif action.startswith('check'):
            game.check(player)
        elif action.startswith('call'):
            game.call(player)
        elif action.startswith('fold'):
            game.fold(player)
    game.next_betting_round()

earnings = game.round_win_info
print(earnings)
for amount, information in earnings.items():
    player, reason = information
    print("{} won {} chips ({}) with {}".format(player.name, amount, reason, ''.join(map(str, player.hand))))