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
from command_logic import meme, award, image, verse, quote, delete, cointoss, dice, wiki

# Constants -------------------------------------------------------

DEF_COLOR = 0x0089a1
RED_COLOR = 0x800000
ORA_COLOR = 0xff5900

ICON_ERROR = 'https://freeiconshop.com/wp-content/uploads/edd/error-flat.png'
ICON_MEDAL = 'https://cdn.discordapp.com/attachments/724745384840396953/879030788723724398/olympic_medal1600.png'
ICON_PERMS = 'https://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/sign-error-icon.png'
ICON_BIBLE = 'https://cdn3.vectorstock.com/i/1000x1000/06/57/bible-icon-vector-5020657.jpg'

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

cmds = read_file.read_command_config()
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


async def no_perms(ctx):
    perms = cmds[ctx.invoked_with]['permissions']
    if perms and ctx.author.id not in perms:
        await send_unauthorised(ctx)
        return True

    return False


async def send_unauthorised(ctx):
    try:
        message = replies.get_reply(cmds[ctx.invoked_with]['unauthorised'])
    except KeyError:
        message = 'Dafür hast du leider nicht die nötigen Berechtigungen.'

    embed_var = discord.Embed(
        color=discord.Colour(RED_COLOR),
        description=message
    )
    embed_var.set_author(
        name='Keine Berechtigung',
        icon_url=ICON_PERMS
    )

    await ctx.send(embed=embed_var)


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
    await hello(ctx)


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
    name='wiki',
    description='Search for something on wikipedia.',
    guild_ids=guilds,
    options=[
        create_option(
            name="term",
            description="The thing you want to know something about.",
            required=True,
            option_type=3
        )
    ]
)
async def _wiki(ctx, term=None):
    await wiki(ctx, term)


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
async def _award(ctx, mention=None):
    await award(ctx, mention)


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
                create_choice(name="Help", value="help"),
                create_choice(name="Hello", value="hello"),
                create_choice(name="Dice", value="dice"),
                create_choice(name="Münzwurf", value="cointoss"),
                create_choice(name="Person", value="person"),
                create_choice(name="Cat", value="cat"),
                create_choice(name="Award", value="award"),
                create_choice(name="Awards", value="awards"),
                create_choice(name="Essen", value="eating"),
                create_choice(name="Essensstats", value="eatingstats"),
                create_choice(name="Vers", value="verse"),
                create_choice(name="Löschen", value="delete"),
                create_choice(name="Wiki", value="wiki"),
                create_choice(name="Offtopic", value="offtopic"),
                create_choice(name="Morgen", value="morning"),
                create_choice(name="Anruf", value="call"),
                create_choice(name="Langeweile", value="bored"),
                create_choice(name="Verlassen", value="quit"),
            ]
        )
    ]
)
async def _help(ctx, command=None):
    try:
        message = cmds[command].help
    except KeyError:
        message = 'Es existiert keine Hilfe für diesen Befehl'

    await ctx.send(message)


# -----------------------------------------------------------------


@client.command()
async def hello(ctx):
    denied = await no_perms(ctx)
    if denied: return

    message = replies.enrich(replies.get_reply(
        cmds[ctx.invoked_with]['replies']),
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        title='Hallo',
        color=discord.Colour(DEF_COLOR),
        description=message)

    await ctx.send(embed=embed_var)


@client.command()
async def quit(ctx):
    denied = await no_perms(ctx)
    if denied: return

    message = replies.enrich(replies.get_reply(cmds[ctx.invoked_with]['replies']))

    # Create embed
    embed_var = discord.Embed(
        title='Quit',
        color=discord.Colour(DEF_COLOR),
        description=message)

    await ctx.send(embed=embed_var)
    await client.close()
    exit(0)


@client.command()
async def dice(ctx):
    denied = await no_perms(ctx)
    if denied: return

    message = replies.enrich(
        replies.get_reply(cmds[ctx.invoked_with]['replies']),
        insert=logic.dice.dice_toss(),
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        title='Dice',
        color=discord.Colour(DEF_COLOR),
        description=message)

    await ctx.send(embed=embed_var)


@client.command()
async def wiki(ctx, arg=None):
    denied = await no_perms(ctx)
    if denied: return

    # Test for params
    if not arg:
        embed_var = discord.Embed(
            color=discord.Colour(RED_COLOR),
            description=replies.get_reply(cmds[ctx.invoked_with]['error'])
        )
        embed_var.set_author(
            name='Error',
            icon_url=ICON_ERROR
        )

        await ctx.send(embed=embed_var)
        return

    link = logic.wiki.get_wiki(cmds[ctx.invoked_with]['urls'][0], arg)

    # Get reply depending on if the site exists
    if 'search' in link:
        message = replies.enrich(replies.get_reply(cmds[ctx.invoked_with]['replies2']))
    else:
        message = replies.enrich(replies.get_reply(cmds[ctx.invoked_with]['replies']))

    # Create embed
    embed_var = discord.Embed(
        title=message,
        color=discord.Colour(DEF_COLOR),
        description=link)
    embed_var.set_author(
        name='Wikipedia',
        icon_url='https://pngimg.com/uploads/wikipedia/wikipedia_PNG16.png')

    await ctx.send(embed=embed_var)


@client.command()
async def award(ctx, *args):
    denied = await no_perms(ctx)
    if denied: return

    if len(args) != 1 or not (args[0].startswith('<@!') and args[0].endswith('>')):
        embed_var = discord.Embed(
            title='Error',
            color=discord.Colour(RED_COLOR),
            description=replies.get_reply(cmds[ctx.invoked_with]['error'])
        )

        await ctx.send(embed=embed_var)
        return

    # Give award
    logic.award.give_award(ctx.channel.guild.id, args[0][3:-1])

    # Get message
    message = replies.enrich(
        replies.get_reply(cmds[ctx.invoked_with]['replies']),
        ref_mention=args[0],
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        color=discord.Colour(DEF_COLOR),
        description=message
    )
    embed_var.set_author(name=f"Award von {get_name(ctx.author)}", icon_url=ICON_MEDAL)

    await ctx.send(embed=embed_var)


@client.command()
async def meme(ctx):
    denied = await no_perms(ctx)
    if denied: return

    meme_object = logic.meme.get_meme(reddit, ctx.channel.guild.id)
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
    denied = await no_perms(ctx)
    if denied: return

    message = logic.quote.get_quote(cmds[ctx.invoked_with]['urls'][0])
    embed_var = discord.Embed(
        description=message['quote'],
        color=discord.Colour(DEF_COLOR))
    embed_var.set_author(
        name=message['author'],
        icon_url=message['image']
    )

    await ctx.send(embed=embed_var)


@client.command()
async def ping(ctx):
    if no_perms(ctx):
        return

    bot_ping = "{:.2f}".format(client.latency * 100)
    reply = replies.enrich(replies.get_reply(ctx.invoked_with['replies']), insert=bot_ping + ' ms')
    embed_var = discord.Embed(title='Ping', colour=discord.Colour(DEF_COLOR), description=reply)
    await ctx.send(embed=embed_var)


@client.command()
async def verse(ctx):
    denied = await no_perms(ctx)
    if denied: return

    message = logic.verse.get_verse(cmds[ctx.invoked_with]['urls'][0])
    embed_var = discord.Embed(color=discord.Colour(DEF_COLOR))
    embed_var.add_field(name=message[1], value=message[0], inline=True)
    embed_var.set_author(
        name="Bibel",
        icon_url=ICON_BIBLE
    )
    await ctx.send(embed=embed_var)


@client.command()
async def cointoss(ctx):
    denied = await no_perms(ctx)
    if denied: return

    message = replies.enrich(
        replies.get_reply(cmds[ctx.invoked_with]['replies']),
        insert=logic.cointoss.coin_toss(),
        mention=ctx.author.mention)
    await ctx.send(message)


@client.command()
async def commands(ctx):
    denied = await no_perms(ctx)
    if denied: return

    message = replies.get_reply(cmds[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(
        color=discord.Colour(ORA_COLOR),
        description=message
    )
    embed_var.set_author(
        name='Error',
        icon_url=ICON_ERROR
    )
    await ctx.send(embed=embed_var)


@client.command()
async def cat(ctx):
    denied = await no_perms(ctx)
    if denied: return

    # Get the image
    file = logic.image.from_url(f'guilds/{ctx.guild.id}/temp/cat.png',
                                replies.get_reply(cmds[ctx.invoked_with]['urls']))

    message = replies.get_reply(cmds[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(title='Cat', color=discord.Colour(DEF_COLOR), description=message)
    embed_var.set_image(url="attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@client.command()
async def person(ctx):
    denied = await no_perms(ctx)
    if denied: return

    # Get the image
    file = logic.image.from_url(f'guilds/{ctx.guild.id}/temp/person.png',
                                replies.get_reply(cmds[ctx.invoked_with]['urls']))

    message = replies.get_reply(cmds[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(title='Person', color=discord.Colour(DEF_COLOR), description=message)
    embed_var.set_image(url=f"attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@client.command()
async def delete(ctx):
    denied = await no_perms(ctx)
    if denied: return

    if not ctx.message.reference:
        embed_var = discord.Embed(
            color=discord.Colour(RED_COLOR),
            description=replies.get_reply(cmds[ctx.invoked_with]['error'])
        )
        embed_var.set_author(
            name='Error',
            icon_url=ICON_ERROR
        )

        await ctx.send(embed=embed_var)
        return

    await logic.delete.delete_message(ctx)


# -----------------------------------------------------------------

client.run(token)
quit(0)
