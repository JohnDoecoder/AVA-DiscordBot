# Main program for the discord bot

import discord
from discord.ext import commands
from discord import guild
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option

import praw
import datetime

from helpers import read_file, replies, write_file
import command_logic as logic
from command_logic import meme, award, image, verse, quote, delete, cointoss, dice


# Constants -------------------------------------------------------

DEF_COLOR = 0x0089a1
PREFIX = '!'

# Credentials -----------------------------------------------------
credentials = read_file.read_json('configuration/credentials.json')
token = credentials["discord"]["token"]
reddit = praw.Reddit(client_id=credentials["reddit"]["id"],
                     client_secret=credentials["reddit"]["secret"],
                     user_agent=credentials["reddit"]["agent"],
                     check_for_async=False)

# Initialize ------------------------------------------------------

intents = discord.Intents().all()
client = commands.Bot(command_prefix=PREFIX, intents=intents)
slash = SlashCommand(client, sync_commands=True)

commands = read_file.read_command_config()
guilds = []
author = ""

# -----------------------------------------------------------------


def log(author: str, channel: str, message: str, other: str, guild=None):
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


def get_name(member: discord.member):
    if member.nick:
        return member.nick
    else:
        return member.name

# -----------------------------------------------------------------


@client.event
async def on_ready():
    global guilds
    guilds = client.guilds
    for guild in guilds:
        write_file.write_guild_config(guild, ["logs", "temp", "user"])

    print(f'I am logged in ({client.user}) and ready!')

# -----------------------------------------------------------------


@client.event
async def on_message(message: discord.Message):
    o = ''
    if not message.content:
        o = '[media or embed]'

    if message.guild:
        log(message.author.name, message.channel.name, message.content, other=o, guild=message.guild)
    else:
        log(message.author.name, message.channel.name, message.content, other=o)

    global author
    author = get_name(message.author)

    await client.process_commands(message)

# Slash commands --------------------------------------------------


@slash.slash(
    name='hello',
    description='Lets the bot greet you.',
    guild_ids=guilds
)
async def _hello(ctx):
    message = replies.enrich(
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
    name='meme',
    description='Shows you a meme from reddit',
    guild_ids=guilds
)
async def _meme(ctx):
    await meme(ctx)


@slash.slash(
    name='award',
    description='Reward somebody with an award',
    guild_ids=guilds,
    options=[
        create_option(
            name="mention",
            description="Mention somebody with @Name",
            required=True,
            option_type=3
        )
    ]
)
async def _award(ctx, command=None):
    await award(ctx, command)


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
    message = replies.enrich(
        replies.get_reply(commands[ctx.invoked_with].replies),
        insert=logic.dice.dice_toss(),
        mention=ctx.author.mention
    )
    await ctx.send(message)


@client.command()
async def award(ctx, *args):
    if len(args) != 1 or not (args[0].startswith('<@!') and args[0].endswith('>')):
        await ctx.send('Error')  # TODO: Read reply from bot.json
        return

    medal = "https://cdn.discordapp.com/attachments/724745384840396953/879030788723724398/olympic_medal1600.png"

    # Give award
    logic.award.give_award(ctx.message.guild.id, args[0][3:-1])

    # Get message
    message = replies.enrich(
        replies.get_reply(commands[ctx.invoked_with].replies),
        ref_mention=args[0],
        mention=ctx.message.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        color=discord.Colour(DEF_COLOR),
        description=message
    )
    embed_var.set_author(name=f"Award für {get_name(ctx.message.author)}", icon_url=medal)

    await ctx.send(embed=embed_var)


@client.command()
async def meme(ctx):
    meme_object = logic.meme.get_meme(reddit, ctx.message.guild.id)
    embed_var = discord.Embed(title='Meme', color=discord.Colour(DEF_COLOR))
    embed_var.set_image(url=meme_object.url)
    embed_var.add_field(
        name=meme_object.title,
        value=f'{meme_object.author} in {meme_object.subreddit}',
        inline=True
    )
    await ctx.send(embed=embed_var)


@client.command()
async def quote(ctx):
    message = logic.quote.get_quote(commands[ctx.invoked_with].urls[0])
    embed_var = discord.Embed(title='Zitat', color=discord.Colour(DEF_COLOR))
    embed_var.add_field(name=message[1], value=message[0], inline=True)
    await ctx.send(embed=embed_var)


@client.command()
async def verse(ctx):
    message = logic.verse.get_verse(commands[ctx.invoked_with].urls[0])
    embed_var = discord.Embed(title='Bibelvers', color=discord.Colour(DEF_COLOR))
    embed_var.add_field(name=message[1], value=message[0], inline=True)
    await ctx.send(embed=embed_var)


@client.command()
async def cointoss(ctx):
    message = replies.enrich(
        replies.get_reply(commands[ctx.invoked_with].replies),
        insert=logic.cointoss.coin_toss(),
        mention=ctx.author.mention)
    await ctx.send(message)


@client.command()
async def cat(ctx):
    # Get the image
    file = logic.image.from_url(f'guilds/{ctx.guild.id}/temp/cat.png',
                                replies.get_reply(commands[ctx.invoked_with].urls))

    message = replies.get_reply(commands[ctx.invoked_with].replies)
    embed_var = discord.Embed(title='Cat', color=discord.Colour(DEF_COLOR), description=message)
    embed_var.set_image(url="attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@client.command()
async def person(ctx):
    # Get the image
    file = logic.image.from_url(f'guilds/{ctx.guild.id}/temp/person.png',
                                replies.get_reply(commands[ctx.invoked_with].urls))

    message = replies.get_reply(commands[ctx.invoked_with].replies)
    embed_var = discord.Embed(title='Person', color=discord.Colour(DEF_COLOR), description=message)
    embed_var.set_image(url=f"attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@client.command()
async def delete(ctx):
    await logic.delete.delete_message(ctx)


# -----------------------------------------------------------------

client.run(token)
quit(0)
