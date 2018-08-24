from poker import Game, Player
import random


if __name__ == '__main__':
    players = [Player('John'), Player('Bob')]
    game = Game(players=players, chips=10000)

    while len(game.players) > 1:
        game.initialize_round()
        while not game.round_ended:
            print(', '.join([n.full_name for n in game.players]))
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
        for amount, information in earnings.items():
            player, reason = information
            print("{} won {} chips ({}) with {}".format(player.name, amount, reason, ''.join(map(str, player.hand))))