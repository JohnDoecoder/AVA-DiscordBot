# Main program for the discord bot

import discord
from discord.ext import commands
from discord import guild
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option

import datetime

import command_logic
import helpers.write_file
from helpers import read_file, replies, write_file
from command_logic import dice as dice_logic, cointoss as coin_logic, image, quote, verse, delete

intents = discord.Intents().all()
client = commands.Bot(command_prefix='!', intents=intents)
slash = SlashCommand(client, sync_commands=True)
token = 'TOKEN'

DEF_COLOR = 0x0089a1

# -----------------------------------------------------------------


commands = read_file.read_command_config()
guilds = []

# -----------------------------------------------------------------


def log(author: str, channel: str, message: str, other: str, guild: discord.Guild = None):
    time = datetime.datetime.now()

    # 2021-05-21 16:38:27 | (user in channel) - This is a message
    entry = str(time)[:-7] + ' | ' + '(' + author + ' in ' + channel + ')' + ' - ' + message + other + '\n'

    if guild:
        with open(f'guilds/{guild.id}/logs/messages.log', 'a', encoding='utf-8') as logfile:
            logfile.write(entry)
        print(guild.name + ':\n' + entry)
    else:
        with open('messages.log', 'a', encoding='utf-8') as logfile:
            logfile.write(entry)
        print('Direct Message:\n' + entry)

# -----------------------------------------------------------------


@client.event
async def on_ready():
    global guilds
    guilds = client.guilds
    for guild in guilds:
        helpers.write_file.write_guild_config(guild, ["logs", "temp", "user"])

    print(f'I am logged in ({client.user}) and ready!')

# -----------------------------------------------------------------

'''
@client.event
async def on_message(message):
    o = ''
    if not message.content:
        o = '[media or embed]'

    if message.guild:
        log(message.author.name, message.channel.name, message.content, other=o, guild=message.guild)
    else:
        log(message.author.name, message.channel.name, message.content, other=o)
'''
# -----------------------------------------------------------------


@slash.slash(
    name='hello',
    description='Lets the bot greet you.',
    guild_ids=guilds
)
async def _hello(ctx):
    message = replies.enrich_replies(
        replies.get_reply(commands[ctx.name].replies), mention=ctx.author.mention)
    await ctx.send(message)


@slash.slash(
    name='cointoss',
    description='Throw a coin and see how it lands.',
    guild_ids=guilds
)
async def _cointoss(ctx):
    await cointoss(ctx)


@slash.slash(
    name='dice',
    description='Throw a six sided dice.',
    guild_ids=guilds
)
async def _dice(ctx):
    await dice(ctx)


@slash.slash(
    name='cat',
    description='Shows you a picture of a random cat',
    guild_ids=guilds
)
async def _cat(ctx):
    await cat(ctx)


@slash.slash(
    name='person',
    description='Shows you a picture of a random person',
    guild_ids=guilds
)
async def _person(ctx):
    await person(ctx)


@slash.slash(
    name='verse',
    description='Grabs a random vers from the bible.',
    guild_ids=guilds
)
async def _verse(ctx):
    await verse(ctx)


@slash.slash(
    name='delete',
    description='Delete a message you are referring to.',
    guild_ids=guilds
)
async def _delete(ctx):
    await delete(ctx)


@slash.slash(
    name='quote',
    description='Grabs a random quote from a smart person.',
    guild_ids=guilds
)
async def _quote(ctx):
    await quote(ctx)


@slash.slash(
    name='help',
    description='Shows you how to use a command',
    guild_ids=guilds,
    options=[
        create_option(
            name="command",
            description="The command you want to see the help from",
            required=True,
            option_type=3,
            choices=[
                create_choice(name="Hilfe", value="help"),
                create_choice(name="Hallo", value="hello"),
                create_choice(name="Würfel", value="dice"),
                create_choice(name="Münzwurf", value="cointoss"),
                create_choice(name="Person", value="person"),
                create_choice(name="Katze", value="cat"),
                create_choice(name="Award", value="award"),
                create_choice(name="Awards", value="awards"),
                create_choice(name="Essen", value="eating"),
                create_choice(name="Essensstats", value="eatingstats"),
                create_choice(name="Vers", value="verse"),
                create_choice(name="Löschen", value="delete")
            ]
        )
    ]
)
async def _help(ctx, command=None):
    try:
        message = commands[command].help
    except KeyError:
        message = 'Es existiert keine Hilfe für diesen Befehl'

    await ctx.send(message)


# -----------------------------------------------------------------


@client.command()
async def dice(ctx):
    message = replies.enrich_replies(
        replies.get_reply(commands[ctx.invoked_with].replies),
        insert=dice_logic.dice_toss(),
        mention=ctx.author.mention)
    await ctx.send(message)


@client.command()
async def quote(ctx):
    message = command_logic.quote.get_quote(commands[ctx.invoked_with].urls[0])
    embed_var = discord.Embed(title='Zitat', color=discord.Colour(DEF_COLOR))
    embed_var.add_field(name=message[1], value=message[0], inline=True)
    await ctx.send(embed=embed_var)


@client.command()
async def verse(ctx):
    message = command_logic.verse.get_verse(commands[ctx.invoked_with].urls[0])
    embed_var = discord.Embed(title='Bibelvers', color=discord.Colour(DEF_COLOR))
    embed_var.add_field(name=message[1], value=message[0], inline=True)
    await ctx.send(embed=embed_var)


@client.command()
async def cointoss(ctx):
    message = replies.enrich_replies(
        replies.get_reply(commands[ctx.invoked_with].replies),
        insert=coin_logic.coin_toss(),
        mention=ctx.author.mention)
    await ctx.send(message)


@client.command()
async def cat(ctx):
    # Get the image
    file = image.from_url(f'guilds/{ctx.guild.id}/temp/cat.png', replies.get_reply(commands[ctx.invoked_with].urls))

    message = replies.get_reply(commands[ctx.invoked_with].replies)
    embed_var = discord.Embed(title='Cat', color=discord.Colour(DEF_COLOR), description=message)
    embed_var.set_image(url=f"attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@client.command()
async def person(ctx):
    # Get the image
    file = image.from_url(f'guilds/{ctx.guild.id}/temp/person.png', replies.get_reply(commands[ctx.invoked_with].urls))

    message = replies.get_reply(commands[ctx.invoked_with].replies)
    embed_var = discord.Embed(title='Person', color=discord.Colour(DEF_COLOR), description=message)
    embed_var.set_image(url=f"attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@client.command()
async def delete(ctx):
    await command_logic.delete.delete_message(ctx)


# -----------------------------------------------------------------

client.run(token)
quit(0)