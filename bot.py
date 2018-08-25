from poker import Game, Player
from discord.ext import commands
import discord
import asyncio
import collections
import logging


class Bot(commands.Bot):

    async def on_ready(self):
        print(f'{self.user.name} is online')
        print(f'https://discordapp.com/api/oauth2/authorize?client_id={self.user.id}&permissions=-1&scope=bot')


class Poker:

    chips_question = ('How many chips should you start with? (default: 10000)\n'
                      'Type `cancel` to cancel')

    member_question = ('Mention your friend\'s to invite them\n\n'
                       '{member_list}'
                       '\n\nType `done` when you\'re done\n'
                       'Type `cancel` to cancel')

    def __init__(self, bot):
        self.bot = bot
        self.tournaments = collections.defaultdict(dict)
        self.invites = collections.defaultdict(dict)

    @commands.command()
    @commands.guild_only()
    async def tournament(self, ctx):

        self.tournaments[ctx.author]['settings'] = {'chips': 10000, 'players': [ctx.author]}

        def from_this_channel(m):
            return m.channel == ctx.channel and m.author == ctx.author


        # GET STARTING CHIPS
        chips_question_msg = await ctx.send(self.chips_question)

        try:
            msg = await self.bot.wait_for('message', check=from_this_channel, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send('User failed to respond in 60 seconds')
        else:
            if msg.content.isdigit():
                self.tournaments[ctx.author]['settings']['chips'] = int(msg.content)
                await chips_question_msg.delete()
            elif msg.content == 'cancel':
                return await ctx.send('Tournament setup canceled')

        # INVITE FRIENDS
        member_question_msg = await ctx.send(self.member_question.format(
            member_list='\n'.join(map(str, self.tournaments[ctx.author]['settings']['players']))))

        while True:
            msg = await self.bot.wait_for('message', check=from_this_channel)
            if msg.content == 'done':
                break
            elif msg.content == 'cancel':
                return await ctx.send('Tournament setup canceled')
            try:
                member = await commands.MemberConverter().convert(ctx, msg.content)
            except commands.errors.BadArgument:
                await ctx.send('Member not found')
            else:
                await msg.add_reaction('⚙')
                self.invites[ctx.author][member.id] = self.bot.loop.create_task(self.send_invite(ctx, member, member_question_msg, msg))

        self.bot.loop.create_task(poker_game(ctx, self.bot, self.tournaments[ctx.author]))

    async def send_invite(self, ctx, member, member_question_msg, msg):

        def yes_or_no(reaction, user):
            return str(reaction.emoji) in ('✅', '❎') and user.id in self.invites[ctx.author]


        tmp = await member.send(f':telephone: **{ctx.author.name}** has invited you to join a '
                                f'game of poker in the **{ctx.guild.name}** server. Use the reactions '
                                'to accept or deny.')

        await tmp.add_reaction('✅')
        await tmp.add_reaction('❎')

        reaction, user = await self.bot.wait_for('reaction_add', check=yes_or_no)
        await tmp.delete()

        self.invites[ctx.author].pop(member.id)
        await msg.delete()

        if str(reaction.emoji) == '✅':
            await member.send("Invite accepted.")
            self.tournaments[ctx.author]['settings']['players'].append(member)
            await member_question_msg.edit(content=self.member_question.format(
                member_list='\n'.join(map(str, self.tournaments[ctx.author]['settings']['players']))))
            return True
        await member.send("Invite declined.")
        return False


    @commands.command(name='eval')
    async def _eval(self, ctx, *, args):
        try:
            r = eval(args)
            await ctx.send(f"```{str(r)}```")
        except Exception as e:
            await ctx.send(f"```{str(e)}```")

    @commands.command()
    async def stop(self, ctx):
        quit()


def get_player_string(game):
    player_string = ''
    for player in game.players:
        if player == game.current_player:
            player_string += '**🢒 '
        player_string += player.id.name
        if player.dealer:
            player_string += ' (D)'
        if player == game.current_player:
            player_string += '**'
        player_string += ' - {}\n'.format(player.chips)
    return player_string


async def poker_game(ctx, bot, tournament_info):
    board_string = '''**Poker Tournament**

{board}

💰 **Pot:** {pot}
💵 **Current Bet:** {bet}

{players}

**[**   ☑ Check   **|**   ❎ Fold   **|**   ☎ Call   **|**   💸 Bet   **]**'''

    settings = tournament_info['settings']

    players = dict((user, Player(user)) for user in settings['players'])
    game = Game(chips=settings['chips'], players=list(players.values()))

    player_string = get_player_string(game)
    board_message = await ctx.send('Setting up the board...')
    await board_message.add_reaction('☑')
    await board_message.add_reaction('❎')
    await board_message.add_reaction('☎')
    await board_message.add_reaction('💸')

    def check(reaction, user):
        return reaction.message.id == board_message.id and user in players.keys()

    while len(game.players) > 1:
        game.initialize_round()
        player_string = get_player_string(game)
        await board_message.edit(content=board_string.format(board=' '.join(map(str, game.board)), pot=game.pot, bet=game.current_bet,
                                                     players=player_string))
        while not game.round_ended:
            player_string = get_player_string(game)
            await board_message.edit(content=board_string.format(board=' '.join(map(str, game.board)), pot=game.pot, bet=game.current_bet,
                                                         players=player_string))
            reaction, user = await bot.wait_for('reaction_add', check=check)
            await board_message.remove_reaction(reaction, user)
            if players[user] == game.current_player:
                if str(reaction) == '☑':
                    game.check(players[user])
                elif str(reaction) == '❎':
                    game.fold(players[user])
                elif str(reaction) == '☎':
                    game.call(players[user])
                elif str(reaction) == '💸':
                    tmp = await ctx.send("How much would you like to bet?")
                    bet = await bot.wait_for('message', check=lambda x: x.author==user and x.channel==ctx.channel)
                    game.bet(players[user], int(bet.content))
                game.next_betting_round()
            else:
                await user.send("It is not your turn yet.")
        earnings = game.round_win_info
        for amount, information in earnings.items():
            player, reason = information
            await ctx.send("{} won {} chips ({}) with {}".format(player.id.name, amount, reason, ''.join(map(str, player.hand))))
        break


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bot = Bot('?')
    bot.add_cog(Poker(bot))

    with open('token.txt') as file:
        token = file.read().strip()

    bot.run(token)
