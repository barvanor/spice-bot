#!/usr/bin/env python3

from enum import Enum
from dataclasses import dataclass
import random

import discord
from discord import Message, User, Reaction, Member
from discord.ext import commands

emojis = {
    'hot_pepper': '🌶️',
    'bell_pepper': '🫑',
    'game_die': '🎲',
    'yes': '✅',
    'no': '❎'
}

class GameStates(Enum):
    JOIN = 'JOIN'     # Players can join by reacting to the join message. Await /startgame from GM
    START = 'STARTED' # The game has started. Main state of the game

@dataclass
class SpicePlayer:
    user:Member
    spice:int = 8

class SpiceBot(commands.Bot):
    def __init__(self, config):
        super().__init__(command_prefix=config['command_prefix'], description=None)

        self.config = config
        self.game_state = None
        self.game_master:Member = None
        self.players = {}
        self.turnorder = []
        self.turn = 0

        self.add_command(commands.command()(self.newgame))
        self.add_command(commands.command()(self.startgame))
        self.add_command(commands.command()(self.roll))
        self.add_command(commands.command()(self.stats))

    async def on_ready(self):
        print("Logged in as {}, ID: {}".format(self.user.name, self.user.id))

    async def on_reaction_add(self, reaction:Reaction, user:Member):
        #TODO: don't use this event. just read the reactions on startup.
        if self.game_state == GameStates.JOIN:
            if reaction.message == self.join_message and \
            not user == self.user:
                print('reaction:', reaction.emoji)
                print('{} joined the game'.format(user.name))
                self.players[user] = (SpicePlayer(user=user))

    async def newgame(self, ctx:commands.Context):
        if not self.game_state:
            self.game_master = ctx.author
            self.game_state = GameStates.JOIN
            self.players = {}
            print('new game')
            print('GM: '+self.game_master.name)

            msg_text = self.format_message('new_game', ctx.author)
            self.join_message = await ctx.send(msg_text)
            await self.join_message.add_reaction(emojis['hot_pepper'])

    async def stats(self, ctx:commands.Context):
        if not self.game_state == GameStates.START:
            return
        placings = sorted(self.turnorder, key=lambda p: p.spice)
        player_stats = [self.format_message('player_stat', p, placing=i) for i,p in enumerate(placings, start=1)]
        scoreboard = '\n'.join(player_stats)
        stats = self.format_message('get_stats', ctx.author,
                                    players=', '.join(p.user.name for p in self.turnorder),
                                    current=self.turnorder[self.turn].user.name,
                                    scoreboard=scoreboard)
        await ctx.send(stats)

    async def startgame(self, ctx:commands.Context):
        if not self.game_state == GameStates.JOIN:
            print('game not in join phase')
            return
        print('starting game')
        print('joined players:')
        print(self.players)
        self.turnorder = list(self.players.values())
        random.shuffle(self.turnorder)
        self.current_turn = 0
        self.game_state = GameStates.START
        msg_text = self.format_message('start_game', ctx.author,
                                       players=', '.join(p.user.name for p in self.turnorder))
        await ctx.send(msg_text)

    def next_turn(self):
        self.turn = (self.turn+1)%len(self.turnorder)
        self.game_state = GameStates.START

    async def spicy_roll(self, ctx:commands.Context, player:SpicePlayer):
        roll = self.roll_dice()
        await ctx.send(self.format_message('roll_result', player, roll=roll))
        resp=''
        if roll >= player.spice:
            resp = 'spicy_roll_success'
        else:
            spice_message = await self.send_message(ctx,'spicy_roll_fail', player, roll=roll)
            reaction = await self.get_reaction(spice_message, player.user, (emojis['yes'], emojis['no']))
            if reaction == emojis['yes']:
                resp = 'spice_price_accept'
                player.spice -= 1
            else:
                resp = 'spice_price_decline'
        await self.send_message(ctx, resp, player, roll=roll)

    async def mild_roll(self, ctx:commands.Context, player:SpicePlayer):
        roll = self.roll_dice()
        await ctx.send(self.format_message('roll_result', player.user, roll=roll))
        resp = ''
        if roll <= player.spice:
            resp = 'mild_roll_success'
        else:
            player.spice -= 1
            resp = 'mild_roll_fail'
        await ctx.send(self.format_message(msg, player, roll=roll))

    async def roll(self, ctx:commands.Context, type = None):
        if not self.game_state == GameStates.START:
            return
        player = self.players.get(ctx.author, None)
        if not player:
            roll = self.roll_dice()
            await ctx.reply(self.format_message('non_participant_roll', ctx.author, roll=roll))
            return
        if not type:
            roll_msg = await self.send_message(ctx, 'roll_prompt', player)
            reaction = await self.get_reaction(roll_msg, player.user, (emojis['hot_pepper'], emojis['bell_pepper']))
            type = 'spicy' if reaction == emojis['hot_pepper'] else 'mild'
        if type == 'mild':
            await self.mild_roll(ctx, player)
        elif type == 'spicy':
            await self.spicy_roll(ctx, player)


    # utility functions
    def roll_dice(self):
        return random.randint(1, self.config['dice_type'])

    async def send_message(self, ctx, message, member, **kwargs):
        return await ctx.send(self.format_message(message, member, **kwargs))

    async def get_reaction(self, message:Message, author:Member, options):
        def check(reaction, user):
            return reaction.message == message and user==author and reaction.emoji in options
        for o in options:
            await message.add_reaction(o)
        #TODO: proper handling of timeout exception
        timeout = self.config['reaction_timeout'] or None
        reaction,_ = await self.wait_for('reaction_add', timeout=timeout, check=check)
        return reaction.emoji

    def format_message(self, message, member, **kwargs):
        user = member.user if isinstance(member, SpicePlayer) else member
        fmt_args = {
            'name': user.name,
            'mention': "<@{}>".format(user.id),
        }

        if isinstance(member, SpicePlayer):
            fmt_args['spice'] = member.spice

        fmt_string = self.config['messages'][message]
        return fmt_string.format(**fmt_args, **kwargs)
