# Main program for the discord bot

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord_slash import SlashCommand

import praw
import datetime
import time
from difflib import SequenceMatcher
import shutil

import helpers.system
from command_logic.music import Music
from helpers import read_file, replies, write_file
import command_logic as clogic
from command_logic import joke, meme, audio, award, cointoss, dice, image, messages, poll, quote, timer, verse, \
    wiki, health, bored, eat
from helpers.system import *

# Credentials -----------------------------------------------------
credentials = read_file.read_json('configuration/credentials.json')
token = credentials["discord"]["token"]
reddit = praw.Reddit(client_id=credentials["reddit"]["id"],
                     client_secret=credentials["reddit"]["secret"],
                     user_agent=credentials["reddit"]["agent"],
                     check_for_async=False)

# Initialize ------------------------------------------------------

bot_config = read_file.read_json('configuration/bot.json')
prefix = bot_config['prefix']
guilds_config = {}
guild_commands = {}

# Discord init
intents = discord.Intents().all()
bot = commands.Bot(command_prefix=prefix, intents=intents)
bot.remove_command("help")
slash = SlashCommand(bot, sync_commands=True)


# -----------------------------------------------------------------


def log(author: str, channel: str, message_text: str, other: str = '', guild=None, deleted=False):
    logtime = datetime.datetime.now()
    if not message_text:
        message_text = '[media or embed]'

    # 2021-05-21 16:38:27 | (user in channel) - This is a message
    if not deleted:
        entry = f'{str(logtime)[:-7]} | ({author} in {channel} ) - {message_text} {other}\n'
    else:
        entry = f'{str(logtime)[:-7]} | ({author} DELETED in {channel} ) - {message_text} {other}\n'

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


async def send_unauthorised(command: str, channel):
    try:
        message = replies.get_reply(guild_commands[command]['unauthorised'])
    except KeyError:
        message = replies.get_reply(bot_config['errors']['unauthorised'])

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['red'], 16)),
        description=message
    )
    embed_var.set_author(
        name='Keine Berechtigung',
        icon_url=bot_config['icons']['perms']
    )

    return await channel.send(embed=embed_var, delete_after=30.0)


async def send_warning(ctx, description=None, delete=True):
    if not description:
        try:
            description = replies.get_reply(guilds_config[ctx.guild.id][ctx.invoked_with]['warning'])
        except Exception as ex:
            await send_error(ctx, f'Error in `send_warning`: {ex}')

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['orange'], 16)),
        description=description
    )
    embed_var.set_author(
        name='Warnung',
        icon_url=bot_config['icons']['warning']
    )

    if delete:
        return await ctx.send(embed=embed_var, delete_after=60.0)
    else:
        return await ctx.send(embed=embed_var)


async def send_error(ctx, description=None, insert=None):
    if description:
        message = description
    else:
        try:
            message = replies.get_reply(guild_commands[ctx.invoked_with]['error'])
        except KeyError:
            message = replies.get_reply(bot_config['errors']['error'])

    if insert:
        message = replies.enrich(message, insert=insert)

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['red'], 16)),
        description=message
    )
    embed_var.set_author(
        name='Error',
        icon_url=bot_config['icons']['error']
    )

    return await ctx.send(embed=embed_var)


async def send_wrong_args(ctx):
    try:
        message = replies.get_reply(guild_commands[ctx.invoked_with]['no_args'])
    except KeyError:
        message = replies.get_reply(bot_config['errors']['wrong_args'])

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['orange'], 16)),
        description=message
    )
    embed_var.set_author(
        name='Warnung',
        icon_url=bot_config['icons']['warning']
    )

    return await ctx.send(embed=embed_var)


async def send_no_command(channel, alternative=None):
    message = replies.get_reply(bot_config['errors']['command_not_found'])

    if alternative:
        message += f' Meintest du `{alternative}`?'

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['orange'], 16)),
        description=message
    )
    embed_var.set_author(
        name='Kein Befehl',
        icon_url=bot_config['icons']['warning']
    )

    return await channel.send(embed=embed_var)


def voice_connected(ctx):
    for voice in bot.voice_clients:
        if voice.channel == ctx.author.voice.channel:
            return voice
    return None


def get_voice(ctx):
    for voice in bot.voice_clients:
        if voice.guild.id == ctx.guild.id:
            return voice


def command_exists(possible_command):
    if possible_command in guild_commands:
        return possible_command


def check_cmd(possible_cmd: str):
    highest_sim = 0
    highest_cmd = ''

    for cmd in guild_commands:
        similarity = SequenceMatcher(None, cmd, possible_cmd).ratio()

        if similarity > highest_sim:
            highest_sim = similarity
            highest_cmd = cmd

    return highest_cmd if highest_sim >= 0.7 else None


async def no_perms(command: str, author: discord.Member, channel):
    perms = guild_commands[command]['permissions']
    if perms != ['*'] and author.id not in perms:
        await send_unauthorised(command, channel)
        return True

    return False


async def correct_command(message):
    # Check if command exists
    if message.content.startswith(prefix):
        possible_command = message.content[1:].split()[0]
        command = command_exists(possible_command)

        # Cmd exists -> Check permissions
        if command:
            denied = await no_perms(command, message.author, message.channel)
            if denied: return False
        # Cmd does not exist -> Find possible right one
        else:
            typo = check_cmd(possible_command)
            if typo:
                await send_no_command(message.channel, typo)
            else:
                await send_no_command(message.channel)
            return False

    return True


# -----------------------------------------------------------------


@bot.event
async def on_ready():
    print('Logged in.')
    global guilds_config
    global music
    music = Music(bot, int(bot_config['colors']['default'], 16))

    # Init Servers / Guilds
    for guild in bot.guilds:
        write_file.init_guild_config(guild, ["logs", "temp", "user"])

    # Read configs for guilds
    reboot = None
    print('\nInitializing...')
    async for guild in bot.fetch_guilds():
        guilds_config[guild.id] = read_file.read_json(f'guilds/{guild.id}/config.json')
        print(f'- {guild.name} ({guild.id})')
        # Check if bot was rebooted
        if not reboot and guilds_config[guild.id]['configuration']['reboot'] != '-':
            reboot = guilds_config[guild.id]['configuration']['reboot']
            guilds_config[guild.id]['configuration']['reboot'] = '-'  # Clear marker
            helpers.write_file.write_json(f'guilds/{guild.id}/config.json', guilds_config[guild.id])

    print(f'\nI am logged in ({bot.user}) and ready!')

    # If rebooted edit message to show reboot was successful
    if reboot:
        g = bot.get_guild(reboot['guild_id'])
        c = g.get_channel(reboot['channel_id'])
        m = c.get_partial_message(reboot['message_id'])
        await m.edit(content='Rebootig... Done!')  # , delete_after=30?


# -----------------------------------------------------------------


@bot.event
async def on_message(message: discord.Message):
    # Emergency command
    if message.author.id == 675076564085637132 and message.content.lower() == '!emergency':
        await message.channel.send('Emergency - Shutting down!')
        await bot.close()
        exit(0)

    # Log message
    if message.guild:
        log(message.author.name, message.channel.name, message.content, guild=message.guild)
    else:
        log(message.author.name, message.channel.id, message.content)

    # Ignore own messages
    if message.author.id == bot.user.id:
        return

    # Direct messages
    if type(message.channel) == discord.DMChannel:
        if message.author.id in guilds_config[message.guild.id]['configuration']['managers']:
            msg_l = message.content.split(' ', 2)
            try:
                guild = bot.get_guild(int(msg_l[0]))
            except:
                return await message.channel.send("Guild not found.")
            try:
                channel = guild.get_channel(int(msg_l[1]))
            except:
                return await message.channel.send("Channel mpt found.")

            await channel.send(msg_l[2])

    # Shortcuts - Get command config of guild and author of message
    global guild_commands
    guild_commands = guilds_config[message.guild.id]['commands']

    # Special sleep command
    if message.content == guilds_config[message.guild.id]['configuration']['prefix'] + 'sleep':
        if await correct_command(message):  # TODO: Maybe separate permission checking
            return await sleep(message=message)

    # Ignore if bot is asleep
    try:
        if guilds_config[message.guild.id]['configuration']['sleep']:
            return
    except KeyError:
        pass  # Key not found -> sleep never called -> bot awake

    # Check if it is a command (or typo) and if user has permission
    if not await correct_command(message):
        return

    # Beta Phase: Block all messages from not permittet users
    msg = message.content
    if message.guild.id == 597531092127449099:
        if message.content.startswith('?') and message.author.id not in [675076564085637132,
                                                                         509706417251549184] and not (
                'play' in msg or 'stop' in msg or 'leave' in msg or 'pause' in msg or 'resume' in msg or 'jump' in msg or 'skip' in msg or 'person' in msg or 'cat' in msg or 'meme' in msg or 'quote' in msg or 'loop' in msg or 'queue' in msg or 'joke' in msg or 'verse' in msg or 'poll' in msg):
            await message.channel.send('Diese Befehle sind momentan noch nicht freigeschaltet!')
            return

    # Purge confirmation
    if message.content.lower() == 'yes' and message.reference:
        try:
            purging = read_file.read_json(f'guilds/{message.guild.id}/user/{message.author.id}.json')['purging']
        except:
            purging = None

        # Purging confirmed
        if purging and type(purging) == dict:
            # Get original bot message
            g = bot.get_guild(purging['guild_id'])
            c = g.get_channel(purging['channel_id'])
            m = c.get_partial_message(purging['message_id'])

            if purging['message_id'] == message.reference.message_id:
                await message.channel.send('Purging messages. This may take a long time...', delete_after=30.0)
                amount = await clogic.messages.purge(message.channel, message.author)
                # Mark that purging was completed
                helpers.write_file.write_stats(message.guild.id, message.author.id, 'purging', '-')
                await message.channel.send(f'{message.author.mention} Purging completet! Purged messages: {amount}',
                                           delete_after=60.0)

    # Ignore non command messages
    if message.content.startswith('?'):
        #  Try catch to get around error when using quit command - Continue with command execution
        try:
            await bot.process_commands(message)
        except Exception as ex:
            print(ex)


# Slash commands --------------------------------------------------

"""
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
    name='timer',
    description='Start one of the global timers',
    guild_ids=guilds,
    options=[
        create_option(
            name='timer',
            description='The timer you want to start',
            option_type=4,  # Int
            required=True,
            choices=[
                create_choice(
                    name='timer1',
                    value=1
                ),
                create_choice(
                    name='timer2',
                    value=2
                ),
                create_choice(
                    name='timer3',
                    value=3
                )
            ]
        )
    ]
)
async def _timer(ctx, timer=None):
    await timer(ctx, timer)


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
    name='joke',
    description='Gets a random joke to make you laugh',
    guild_ids=guilds
)
async def _joke(ctx):
    await joke(ctx)


@slash.slash(
    name='wiki',
    description='Search for something on wikipedia.',
    guild_ids=guilds,
    options=[
        create_option(
            name="term",
            description="The thing you want to know something about. (Or random for a random page)",
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
        message = guild_commands[command].help
    except KeyError:
        message = 'Es existiert keine Hilfe für diesen Befehl'

    await ctx.send(message)
"""


# -----------------------------------------------------------------


@bot.command()
async def authorize(ctx, *args):
    # Not enough args
    if len(args) != 2:
        await send_error(ctx)
        return

    users = args[0].split(',')
    commands = args[1].split(',')

    # Apply to all users
    if len(users) == 1 and users[0] == '*':
        userlist = None
    # Get selected users
    else:
        # Convert ids to users
        userlist = []
        for user in users:
            try:
                u = int(user)
                userlist.append(ctx.guild.get_member(u))
            except:
                pass
                # TODO: Just ignore?

    # Apply to all commands
    if len(commands) == 1 and commands[0] == '*':
        commands = guild_commands

    # Add permissions
    for c in commands:
        # Command does not exist
        if c not in guild_commands:
            continue
            # TODO: Just ignore?

        # All users
        if not userlist:
            guild_commands[c]['permissions'] = ['*']  # Adds perms for all users
            await ctx.send(f'`Alle dürfen `{c}` nun ausführen.')
        # Add for specified users
        else:
            # Clear * if all users were permittet
            if len(guild_commands[c]['permissions']) == 1 and guild_commands[c]['permissions'][0] == '*':
                guild_commands[c]['permissions'] = []
            # Give users permission
            for user in userlist:
                # Nutzer hat bereits die Rechte
                if user.id in guild_commands[c]['permissions']:
                    await ctx.send(f'`{user.name}` darf `{c}` bereits ausführen.')

                guild_commands[c]['permissions'].append(user.id)  # Add perm
                await ctx.send(f'`{user.name}` darf nun `{c}` ausführen.')

            # Check if all members have permission and if so, replace entry with *
            all_user_ids = []
            for member in ctx.guild.members:
                all_user_ids.append(member.id)
            if set(guild_commands[c]['permissions']) == set(all_user_ids):
                guild_commands[c]['permissions'] = ['*']

    # Write changes
    guilds_config[ctx.guild.id]['commands'] = guild_commands  # To config
    write_file.write_json(f'guilds/{ctx.guild.id}/config.json', guilds_config[ctx.guild.id])  # To file


@bot.command()
async def permissions(ctx, *args):
    if len(args) != 1:
        await send_wrong_args(ctx)
        return
    arg = args[0]

    # All users that have permission to use specified command
    if command_exists(arg):
        title = f'Permissions for /{arg}'
        description = ''
        for user_id in guild_commands[arg]['permissions']:
            if user_id == '*':
                user = 'Das Ausführen dieses Befehls ist nicht eingeschränkt.'
            else:
                user = bot.get_user(int(user_id))
            description += f'{user}\n'
    # All commands the specified user has permission for
    else:
        try:
            user = bot.get_user(int(arg))
        except:
            await send_wrong_args(ctx)
            return

        title = f'{user} has permissions for'
        description = ''
        for command in guild_commands:
            if user.id in guild_commands[command]['permissions'] or guild_commands[command]['permissions'] == ['*']:
                description += f'{command}\n'

    if not description:
        description = 'Nichts gefunden...'

    embed_msg = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        title=title,
        description=description
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def managers(ctx, *args):
    if len(args) < 2:
        return await send_wrong_args(ctx)
    pass
    # TODO: Add logic to add/remove managers (can copy from authorize/forbid)


@bot.command()
async def forbid(ctx, *args):
    # Not enough args
    if len(args) != 2:
        await send_error(ctx)
        return

    users = args[0].split(',')
    commands = args[1].split(',')

    # Apply to all users
    if len(users) == 1 and users[0] == '*':
        userlist = None
    # Get selected users
    else:
        # Convert ids to users
        userlist = []
        for user in users:
            try:
                u = int(user)
                userlist.append(ctx.guild.get_member(u))
            except:
                pass
                # TODO: Just ignore?

    # Apply to all commands
    if len(commands) == 1 and commands[0] == '*':
        commands = guild_commands

    # Remove permissions
    for c in commands:
        # Command does not exist
        if c not in guild_commands:
            continue
            # TODO: Just ignore?

        # All users
        if not userlist:
            guild_commands[c]['permissions'] = []  # Removes perms for all users
            embed_msg = discord.Embed(
                title='Verweigert',
                description=f'Niemand darf `{c}` mehr ausführen.'
            )
            await ctx.send(embed=embed_msg)
        # Add for specified users
        else:
            # Remove * and all all users so that the denied users can be excluded from that list
            if guild_commands[c]['permissions'] == ['*']:
                guild_commands[c]['permissions'] = []
                for user in ctx.guild.members:
                    guild_commands[c]['permissions'].append(user.id)
            # Remove specified users
            for user in userlist:
                guild_commands[c]['permissions'].remove(user.id)  # Remove perm
                embed_msg = discord.Embed(
                    title='Verweigert',
                    description=f'`{user.name}` darf `{c}` nicht mehr ausführen.'
                )
                await ctx.send(embed=embed_msg)

    # Write changes
    guilds_config[ctx.guild.id]['commands'] = guild_commands  # To config
    write_file.write_json(f'guilds/{ctx.guild.id}/config.json', guilds_config[ctx.guild.id])  # To file


@bot.command()
async def poll(ctx, *args):
    if len(args) > 6 or len(args) < 3:
        await ctx.send('Not less than 2 and not more than 5 options.')
        return

    await clogic.poll.create_poll(ctx, args, bot_config)


@bot.command()
async def hello(ctx):
    message = replies.enrich(replies.get_reply(
        guild_commands[ctx.invoked_with]['replies']),
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        title='Hallo',
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=message)

    await ctx.send(embed=embed_var)


@bot.command()
async def kick(ctx, *args):
    if len(args) != 1:
        return await send_wrong_args(ctx)

    try:
        member = ctx.guild.get_member(int(args[0][3:-1]))
    except:
        return await send_wrong_args(ctx)

    # Member not connected
    if not member.voice:
        return await send_warning(ctx, description=replies.get_reply(guild_commands[ctx.invoked_with]['not_connected']))
    # Self kick
    if member.id == ctx.message.author.id:
        return await send_warning(ctx, description=replies.get_reply(guild_commands[ctx.invoked_with]['self_kick']))
    # Bot kick
    if member.id == bot.user.id:
        return await send_warning(ctx, description=replies.get_reply(guild_commands[ctx.invoked_with]['bot_kick']))

    # Kick user from VoiceChannel
    await member.edit(voice_channel=None)

    embed_msg = discord.Embed(
        title='Gekickt',
        description=replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
                                   ref_mention=member.mention)
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def buh(ctx, arg):
    if not voice_connected(ctx):
        try:
            channel = ctx.guild.get_channel(int(arg))
        except:
            await send_wrong_args(ctx)
            return

        voice = await channel.connect()

    else:
        # Bot is currently connected
        voice = get_voice(ctx)
        if voice:
            try:
                voice.stop()
            except:
                pass

    source = FFmpegPCMAudio(f'guilds/buh.mp3')
    player = voice.play(source)
    time.sleep(2)
    await leave(ctx, ignore_not_connected=True)


@bot.command()
async def fileplay(ctx, arg):
    if not ctx.author.voice:
        await ctx.send('Not connected to channel.')
        return

    if not voice_connected(ctx):
        channel = ctx.author.voice.channel
        voice = await channel.connect()
    else:
        voice = voice_connected(ctx)

    if voice.is_playing:
        voice.stop()

    try:
        source = FFmpegPCMAudio(f'Testing/SoundBridge/{arg}')
        player = voice.play(source)
    except:
        await ctx.send(f'Audio `{arg}` not found.')
        return

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['gray'], 16)),
        description=f'Ich spiele: `{arg}`.'
    )

    await ctx.send(embed=embed_var, delete_after=60.0)


@bot.command()
async def order66(ctx):
    async def play_order(voice):
        source = FFmpegPCMAudio(f'guilds/order66.mp3')
        player = voice.play(source)
        time.sleep(9)
        await leave(ctx, ignore_not_connected=True)

    async def kill_members(members: list):
        for member in members:
            # Spare special people
            if member.id in [bot.user.id, ctx.author.id, ctx.guild.owner_id]:
                continue

            # Kill the rest
            for role in member.roles:
                try:
                    await member.remove_roles(role)
                except:
                    pass
            try:
                await member.add_roles(executed_role)
            except:
                pass

            embed_var = discord.Embed(
                color=discord.Colour(int(bot_config['colors']['red'], 16)),
                title='Order66 - Kill',
                description=replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['on_death']),
                                           ref_mention=member.mention)
            )
            await ctx.send(embed=embed_var)

    # Create special role
    executed_role = None
    for role in ctx.guild.roles:
        if role.name == 'Executed Jedi':
            executed_role = role

    if not executed_role:
        executed_role = await ctx.guild.create_role(
            name='Executed Jedi',
            color=discord.Colour(int(bot_config['colors']['red'], 16)),
            hoist=True,
            mentionable=True,
            reason='To show what the Empire is capable of.'
        )

    # Send reply
    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['red'], 16)),
        title='Order66',
        description='Yes Sir!'
    )
    await ctx.send(embed=embed_var)

    # Bot is currently connected
    voice = get_voice(ctx)
    if voice:
        try:
            voice.stop()
        except:
            pass
        await play_order(voice)
        await kill_members(voice.members)

    # Join all channels with members in it and play audio
    for channel in ctx.guild.voice_channels:
        if channel.members:
            voice = await channel.connect()
            await play_order(voice)
            await kill_members(channel.members)

    # Kill all other members who were not in a voice channel
    await kill_members(ctx.guild.members)


@bot.command()
async def play(ctx, *args):
    # User not connected to voice
    if not ctx.author.voice:
        return await send_error(ctx, description=replies.get_reply(guild_commands[ctx.invoked_with]['no_voice']))
    # No Songs provided
    if not args:
        return await send_error(ctx, description=replies.get_reply(guild_commands[ctx.invoked_with]['no_args']))

    # Song title with blanks: Eqach word is seperate arg -> Combine to one
    url = ' '.join(args)

    # Connect to voice channel if not already connected
    if not voice_connected(ctx):
        channel = ctx.author.voice.channel
        voice = await channel.connect()
    else:
        voice = voice_connected(ctx)
    # Play audio(s)
    await music.play_song(ctx, voice, url, guilds_config[ctx.guild.id]['commands']['play'])


@bot.command()
async def bored(ctx):
    try:
        description = clogic.bored.bored(ctx, replies.get_reply(guild_commands[ctx.invoked_with]['urls']))
    except:
        return await send_error(ctx)

    embed_msg = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=description
    )
    embed_msg.set_author(
        name='Idee',
        icon_url=bot_config['icons']['drawing']
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def owner(ctx):
    urls = guild_commands[ctx.invoked_with]['urls']

    # No information
    if len(urls) == 0:
        return await send_warning(ctx, replies.get_reply(guild_commands[ctx.invoked_with]['no_urls']))

    description = ''
    for url in urls:
        description += url + '\n'

    try:
        color = discord.Colour(int(guild_commands['owner']['color'], 16))
    except:
        color = discord.Colour(int(bot_config['colors']['default'], 16))

    embed_msg = discord.Embed(
        color=color,
        description=description
    )
    embed_msg.set_author(
        name=ctx.guild.owner,
        icon_url=ctx.guild.owner.avatar_url
    )

    await ctx.send(embed=embed_msg)


@bot.command()
async def owneredit(ctx, *args):
    if not args or len(args) < 2:
        return await send_wrong_args(ctx)

    if args[0] == 'add':
        for arg in args[1:]:
            guilds_config[ctx.guild.id]['commands']['owner']['urls'].append(arg)
    elif args[0] == 'del':
        try:
            del guilds_config[ctx.guild.id]['commands']['owner']['urls'][int(args[1]) - 1]
        except:
            return await send_wrong_args(ctx)
    elif args[0] == 'color':
        try:
            dummy = discord.Colour(int(args[1], 16))

            if args[1].startswith('0x'):
                color = args[1]
            else:
                color = '0x' + args[1]

            guilds_config[ctx.guild.id]['commands']['owner']['color'] = color
        except:
            return await send_wrong_args(ctx)
    else:
        return await send_wrong_args(ctx)

    helpers.write_file.write_json(f'guilds/{ctx.guild.id}/config.json', guilds_config[ctx.guild.id])


@bot.command()
async def sleep(ctx=None, message=None):
    if ctx:
        channel = ctx.message.channel
    else:
        channel = message.channel

    try:
        asleep = guilds_config[channel.guild.id]['configuration']['sleep']
    except KeyError:
        asleep = False

    if asleep:
        guilds_config[channel.guild.id]['configuration']['sleep'] = False
        embed_msg = discord.Embed(
            title='Einschlafen',
            description=replies.get_reply(guild_commands['sleep']['resumed'])
        )
    else:
        guilds_config[channel.guild.id]['configuration']['sleep'] = True
        embed_msg = discord.Embed(
            title='Aufgewacht',
            description=replies.get_reply(guild_commands['sleep']['paused'])
        )

    await channel.send(embed=embed_msg)


@bot.command()
async def stop(ctx):
    # Check if user is in a voice channel
    if not ctx.author.voice:
        return await send_error(ctx)
    else:
        if voice_connected(ctx):
            voice_connected(ctx).stop()
            await music.stop(ctx)


@bot.command()
async def leave(ctx, ignore_not_connected: bool = True):
    channels = bot.voice_clients
    voice = None
    for channel in channels:
        if channel.guild.id == ctx.guild.id:
            voice = channel
            break

    if not ignore_not_connected and not ctx.author.voice or not voice:
        return await send_error(ctx)

    if voice:
        try:
            voice.stop()
            await music.stop(ctx)
        except:
            pass

    await voice.disconnect()


@bot.command()
async def pause(ctx):
    voice = voice_connected(ctx)

    if not ctx.author.voice or not voice:
        return await send_error(ctx)

    voice.pause()


@bot.command()
async def loop(ctx):
    voice = voice_connected(ctx)
    if not ctx.author.voice or not voice:
        return await send_error(ctx)

    await music.toggle_loop(ctx)


@bot.command()
async def skip(ctx):
    voice = voice_connected(ctx)
    if not ctx.author.voice or not voice:
        return await send_error(ctx)

    await music.skip_song(ctx)


@bot.command()
async def jump(ctx, arg):
    voice = voice_connected(ctx)

    try:
        arg = int(arg)
    except:
        return await send_error(ctx)

    if not ctx.author.voice or not voice:
        return await send_error(ctx)

    if await music.jump_to_song(ctx, arg - 1) == 1:
        await send_error(ctx)


@bot.command()
async def queue(ctx):
    voice = voice_connected(ctx)
    if not ctx.author.voice or not voice:
        return await send_error(ctx)

    embed_msg = await clogic.audio.get_queue(ctx, music)
    if not embed_msg:
        return await send_warning(ctx)

    await ctx.send(embed=embed_msg, delete_after=60.0)


@bot.command()
async def resume(ctx):
    voice = voice_connected(ctx)
    if not ctx.author.voice or not voice:
        await send_error(ctx)
        return

    voice.resume()


@bot.command()
async def timer(ctx, arg=None):
    # Test for params
    if not arg or arg not in ['1', '2', '3']:
        await send_error(ctx)
        return

    answer = clogic.timer.toggle_timer(ctx.guild.id, arg)

    message = replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with][answer[0]]), insert=answer[1])

    # Create embed
    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=message)
    embed_var.set_author(
        name=f'Timer{arg}',
        icon_url=bot_config['icons']['timer']
    )

    await ctx.send(embed=embed_var)


@bot.command()
async def quit(ctx):
    message = replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['replies']))

    # Create embed
    embed_var = discord.Embed(
        title='Quit',
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=message)

    await ctx.send(embed=embed_var)
    await bot.close()
    exit(0)


@bot.command()
async def reboot(ctx, arg=''):
    # Remember message
    message = await ctx.send('Rebooting...')
    guilds_config[ctx.guild.id]['configuration']['reboot'] = {
        'message_id': message.id,
        'channel_id': message.channel.id,
        'guild_id': message.guild.id,
        'author_id': message.author.id
    }
    helpers.write_file.write_json(f'guilds/{ctx.guild.id}/config.json', guilds_config[ctx.guild.id])

    # Reboot
    await bot.close()
    helpers.system.reboot(arg)


@bot.command()
async def internet(ctx):
    description = replies.get_reply(guild_commands[ctx.invoked_with]['replies'])

    embed_msg = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        title='Internet',
        description=description
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def dice(ctx):
    message = replies.enrich(
        replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
        insert=clogic.dice.dice_toss(),
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        title='Dice',
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=message)

    await ctx.send(embed=embed_var)


@bot.command()
async def wiki(ctx, arg=None):
    # Test for params
    if not arg:
        await send_error(ctx)
        return

    link = clogic.wiki.get_wiki(guild_commands[ctx.invoked_with]['urls'][0], arg)

    # Get reply depending on if the site exists
    if 'search' in link:
        message = replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['replies2']))
    else:
        message = replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['replies']))

    # Create embed
    embed_var = discord.Embed(
        title=message,
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=link)
    embed_var.set_author(
        name='Wikipedia',
        icon_url='https://pngimg.com/uploads/wikipedia/wikipedia_PNG16.png')

    await ctx.send(embed=embed_var)


@bot.command()
async def award(ctx, *args):
    if len(args) != 1 or not (args[0].startswith('<@!') and args[0].endswith('>')):
        await send_wrong_args(ctx)
        return

    try:
        member_id = int(args[0][3:-1])
    except:
        await send_wrong_args(ctx)
        return

    # Self award
    if member_id == ctx.author.id:
        await send_warning(ctx, replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['self_award']),
                                               mention=ctx.author.mention))
        return

    # Give award
    try:
        clogic.award.give_award(ctx.channel.guild.id, member_id)  # Extract id from mention
    except:
        await send_wrong_args(ctx)
        return

    # Get message
    message = replies.enrich(
        replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
        ref_mention=args[0],
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=message
    )
    embed_var.set_author(name=f"Award von {get_name(ctx.author)}", icon_url=bot_config['icons']['medal'])

    await ctx.send(embed=embed_var)


@bot.command()
async def awards(ctx, *args):
    # No user specified -> All users
    if not args:
        user = clogic.award.get_awards(ctx.guild)
    # User specified
    else:
        user = clogic.award.get_awards(ctx.guild, args)
        if not user:
            await send_wrong_args(ctx)

    description = ''
    for u in user:
        description += f'`{bot.get_user(u)}` hat `{user[u]}` Awards.\n'

    embed_msg = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        title='Awards',
        description=description[:-1]  # Remove last \n
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def idiot(ctx, *args):
    if len(args) != 1 or not (args[0].startswith('<@!') and args[0].endswith('>')):
        await send_wrong_args(ctx)
        return

    # Give idiot
    try:
        member_id = int(args[0][3:-1])
    except:
        await send_wrong_args(ctx)
        return

    # Self award
    if member_id == ctx.author.id:
        await send_warning(ctx, replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['self_idiot']),
                                               mention=ctx.author.mention))
        return
    try:
        clogic.award.give_idiot(ctx.channel.guild.id, args[0][3:-1])
    except:
        await send_wrong_args(ctx)
        return

    # Get message
    message = replies.enrich(
        replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
        ref_mention=args[0],
        mention=ctx.author.mention
    )

    # Create embed
    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=message
    )
    embed_var.set_author(name=f"Idiot von {get_name(ctx.author)}", icon_url=bot_config['icons']['idiot'])

    await ctx.send(embed=embed_var)


@bot.command()
async def idiots(ctx, *args):
    # No user specified -> All users
    if not args:
        user = clogic.award.get_idiots(ctx.guild)
    # User specified
    else:
        user = clogic.award.get_idiots(ctx.guild, args)

    description = ''
    for u in user:
        description += f'`{bot.get_user(u)}` hat `{user[u]}` Idiots.\n'

    embed_msg = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        title='Idiots',
        description=description[:-1]  # Remove last \n
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def meme(ctx):
    meme_object = clogic.meme.get_meme(reddit, ctx.channel.guild.id)
    embed_var = discord.Embed(title='Meme', color=discord.Colour(int(bot_config['colors']['default'], 16)))
    embed_var.set_image(url=meme_object.url)
    embed_var.add_field(
        name=meme_object.title,
        value=f'{meme_object.author} in {meme_object.subreddit}',
        inline=True
    )
    await ctx.send(embed=embed_var)


@bot.command()
async def quote(ctx):
    message = clogic.quote.get_quote(guild_commands[ctx.invoked_with]['urls'][0])
    embed_var = discord.Embed(
        description=message['quote'],
        color=discord.Colour(int(bot_config['colors']['default'], 16)))
    embed_var.set_author(
        name=message['author'],
        icon_url=message['image']
    )

    await ctx.send(embed=embed_var)


@bot.command()
async def ping(ctx):
    bot_ping = round(bot.latency * 1000)

    # Testing api ping
    start_time = time.time()
    msg = await ctx.send('Testing')
    await msg.delete()
    end_time = time.time()
    api_ping = round((end_time - start_time) * 500)  # Only *500 because we executet 2 commands and want only 1
    reply = replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
                           insert=f'Bot: {bot_ping}ms - API: {api_ping}ms')
    embed_var = discord.Embed(title='Ping', colour=discord.Colour(int(bot_config['colors']['default'], 16)),
                              description=reply)
    await ctx.send(embed=embed_var)


@bot.command()
async def health(ctx):
    health = await clogic.health.get_health(ctx, bot)

    if health['rating'] == 1:
        reply = replies.get_reply(guild_commands[ctx.invoked_with]['healthy'])
    elif health['rating'] == 2:
        reply = replies.get_reply(guild_commands[ctx.invoked_with]['okay'])
    else:
        reply = replies.get_reply(guild_commands[ctx.invoked_with]['ill'])

    description = '{0}\n`CPU: {1}%`\n`RAM: {2}%`\n`PING: {3}ms`\n`API: {4}ms`\n`Music available: {5}`'.format(
        reply, health['cpu'], health['ram'], health['ping'], health['api'], health['youtube'])

    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['green'], 16)),
        description=description
    )
    embed_var.set_author(
        name="Health",
        icon_url=bot_config['icons']['health']
    )
    await ctx.send(embed=embed_var)


@bot.command()
async def grrr(ctx):
    embed_msg = discord.Embed(
        title='Aggressionen?',
        description=replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
        color=discord.Colour(int(bot_config['colors']['default'], 16))
    )
    embed_msg.add_field(
        name='Selbsttest',
        value=guild_commands[ctx.invoked_with]['description'] + '\n' +
              replies.get_reply(guild_commands[ctx.invoked_with]['urls']),
        inline=False
    )
    await ctx.send(embed=embed_msg)


@bot.command()
async def eating(ctx):
    result = clogic.eat.toggle_timer(ctx)

    embed_msg = discord.Embed(
        title='Essenstimer',
        description=replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with][result[0]]),
                                   insert=result[1],
                                   mention=ctx.author.mention),
        color=discord.Colour(int(bot_config['colors']['default'], 16))
    )
    await ctx.send(embed=embed_msg, delete_after=30.0)


@bot.command()
async def eatingstats(ctx, *args):
    if len(args) > 2:
        return await send_wrong_args(ctx)

    # For all members
    if not args:
        description = ''
        for member in ctx.guild.members:
            # Skip bot entry
            if member.id == bot.user.id:
                continue
            stats = clogic.eat.get_stats(ctx.guild.id, member.id)
            if stats['amount'] > 0:
                time = round(stats['time'] / stats['amount'], 2)
            else:
                time = 0
            description += '`{}` hat `{}` mal gegessen und dafür durchschnittlich `{} min` gebraucht.\n'
            description = description.format(member, stats['amount'], time)
    # For specific member
    else:
        # Get member from mention
        try:
            member = ctx.guild.get_member(int(args[0][3:-1]))
        except:
            member = None
        if not member:
            return await send_wrong_args(ctx)
        stats = clogic.eat.get_stats(ctx.guild.id, member.id)
        if stats['amount'] > 0:
            time = round(stats['time'] / stats['amount'], 2)
        else:
            time = 0
        description = '`{}` hat `{}` mal gegessen und dafür durchschnittlich `{} min` gebraucht.'
        description = description.format(member, stats['amount'], time)

    embed_msg = discord.Embed(
        title='Essensstats',
        description=description,
        color=discord.Colour(int(bot_config['colors']['default'], 16))
    )
    await ctx.send(embed=embed_msg, delete_after=60.0)


@bot.command()
async def verse(ctx):
    message = clogic.verse.get_verse(guild_commands[ctx.invoked_with]['urls'][0])
    embed_var = discord.Embed(color=discord.Colour(int(bot_config['colors']['default'], 16)))
    embed_var.add_field(name=message[1], value=message[0], inline=True)
    embed_var.set_author(
        name="Bibel",
        icon_url=bot_config['icons']['bible']
    )
    await ctx.send(embed=embed_var)


@bot.command()
async def call(ctx):
    config = read_file.read_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json')
    config['calls'] += 1
    write_file.write_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json', config)

    embed_var = discord.Embed(
        title='Drohanruf',
        description=replies.enrich(replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
                                   name=str(ctx.author),
                                   mention=ctx.author.mention),
        color=discord.Colour(int(bot_config['colors']['default'], 16)))
    await ctx.send(embed=embed_var, delete_after=60.0)


@bot.command()
async def calls(ctx, *args):
    if len(args) > 2:
        return await send_wrong_args(ctx)

    # For all members
    if not args:
        description = ''
        for member in ctx.guild.members:
            config = read_file.read_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json')
            description += '`{}` hat bereits `{}` Anrufe erhalten.\n'.format(member, config['calls'])
    # For specific member
    else:
        # Get member from mention
        try:
            member = ctx.guild.get_member(int(args[0][3:-1]))
        except:
            member = None
        if not member:
            return await send_wrong_args(ctx)

        config = read_file.read_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json')
        description = '`{}` hat `{}` Anrufe erhalten.'.format(member, config['calls'])

    embed_msg = discord.Embed(
        title='Anrufe',
        description=description,
        color=discord.Colour(int(bot_config['colors']['default'], 16))
    )
    await ctx.send(embed=embed_msg, delete_after=60.0)


@bot.command()
async def cointoss(ctx):
    message = replies.enrich(
        replies.get_reply(guild_commands[ctx.invoked_with]['replies']),
        insert=clogic.cointoss.coin_toss(),
        mention=ctx.author.mention)
    await ctx.send(message)


@bot.command()
async def joke(ctx):
    message = replies.get_reply(guild_commands[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(
        colour=discord.Colour(int(bot_config['colors']['default'], 16)),
        title='Joke',
        description=message + '\n\n' + clogic.joke.get_joke(ctx, guild_commands)
    )

    await ctx.send(embed=embed_var)


@bot.command()
async def help(ctx, *args):
    if len(args) != 1:
        command_name = 'help'
    else:
        command_name = args[0]

    try:
        embed_msg = discord.Embed(
            description=guild_commands[command_name]['help']
        )
        embed_msg.set_author(
            name='Hilfe',
            icon_url=bot_config['icons']['help']
        )
        await ctx.send(embed=embed_msg)
    except KeyError:
        await send_error(ctx, insert=command_name)


@bot.command()
async def commands(ctx):
    message = replies.get_reply(guild_commands[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(
        color=discord.Colour(int(bot_config['colors']['orange'], 16)),
        description=message
    )
    embed_var.set_author(
        name='Error',
        icon_url=bot_config['icons']['error']
    )
    await ctx.send(embed=embed_var)


@bot.command()
async def offtopic(ctx, *args):
    if len(args) != 2:
        return await send_wrong_args(ctx)

    try:
        error = await clogic.messages.offtopic(ctx, args[0], args[1],
                                               discord.Colour(int(bot_config['colors']['gray'], 16)))
    except:
        return await send_wrong_args(ctx)

    if error == 1:
        # Return key for dict instead of just one for more precise error messages
        return await send_wrong_args(ctx)


@bot.command()
async def cat(ctx):
    # Get the image
    file = clogic.image.from_url(f'guilds/{ctx.guild.id}/temp/cat.png',
                                 replies.get_reply(guild_commands[ctx.invoked_with]['urls']))

    message = replies.get_reply(guild_commands[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(title='Cat', color=discord.Colour(int(bot_config['colors']['default'], 16)),
                              description=message)
    embed_var.set_image(url="attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@bot.command()
async def person(ctx):
    # Get the image
    file = clogic.image.from_url(f'guilds/{ctx.guild.id}/temp/person.png',
                                 replies.get_reply(guild_commands[ctx.invoked_with]['urls']))

    message = replies.get_reply(guild_commands[ctx.invoked_with]['replies'])
    embed_var = discord.Embed(title='Person', color=discord.Colour(int(bot_config['colors']['default'], 16)),
                              description=message)
    embed_var.set_image(url=f"attachment://image.png")
    await ctx.send(file=file, embed=embed_var)


@bot.command()
async def delete(ctx, *args):
    if not args or len(args) != 1:
        return await send_wrong_args(ctx)

    try:
        await clogic.messages.delete(ctx, int(args[0]))
    except:
        await send_wrong_args(ctx)


@bot.command()
async def purge(ctx):
    purge_message = await send_warning(ctx,
                                       'All your messages in this channel will be deleted. If you wish to continue, '
                                       'reply to this message with `yes`.')
    try:
        purging = {
            'message_id': purge_message.id,
            'channel_id': purge_message.channel.id,
            'guild_id': purge_message.guild.id,
            'author_id': purge_message.author.id
        }
        helpers.write_file.write_stats(ctx.guild.id, ctx.author.id, 'purging', purging)
    except:
        await send_error(ctx)


@bot.command()
async def rules(ctx, *args):
    # Args: message id, reaction (emoji), roles
    if len(args) != 3:
        return await send_wrong_args(ctx)

    # Get message
    message = None
    for channel in ctx.guild.channels:
        if type(channel) == discord.TextChannel:
            try:
                message = await channel.fetch_message(int(args[0]))
                break
            except:
                pass
    if not message:
        return await send_wrong_args(ctx)

    try:
        rules = {
            "id": message.id,
            "reaction": args[1],
            "roles": [int(i) for i in args[2].split()]
        }
    except:
        return await send_wrong_args(ctx)

    # Add specified reaction to message
    try:
        await message.add_reaction(args[1])
    except:
        return await send_wrong_args(ctx)

    # Write changes
    guilds_config[ctx.guild.id]['configuration']['rules'] = rules
    write_file.write_json(f'guilds/{ctx.guild.id}/config.json', guilds_config[ctx.guild.id])

    embed_msg = discord.Embed(
        title='Regeln festgelegt',
        description=replies.get_reply(guild_commands[ctx.invoked_with]['replies']) + '\n' + message.content,
        color=discord.Colour(int(bot_config['colors']['default'], 16))
    )
    await ctx.send(embed=embed_msg)


# -----------------------------------------------------------------


@bot.event
async def on_guild_join(guild):
    global guilds_config

    print(f'Bot was invited to server {guild.id} ({guild.name}) - Initialising...')
    # Init guild
    write_file.init_guild_config(guild, ["logs", "temp", "user"])

    # Restrict some command permissions to guild owner (who can change them afterwards)
    commands = guilds_config[guild.id]['commands']
    for c in bot_config['owner_commands']:
        commands[c]['permissions'] = [guild.owner.id]

    # Write changes
    guild_commands[guild.id] = guild_commands  # To config
    write_file.write_json(f'guilds/{guild.id}/configuration/config.json', guild_commands)  # To file

    # Read config for guild
    guilds_config[guild.id] = read_file.read_json(f'guilds/{guild.id}/config.json')

    print(f'Initialisation of guild {guild.id} ({guild.name}) completed.')


@bot.event
async def on_guild_remove(guild):
    print(f'Bot was removed from server {guild.id} ({guild.name}) - Archiving...')
    # Archive
    os.rename(f'guilds/{guild.id}', f'guilds/archived_{guild.id}')


@bot.event
async def on_member_join(member):
    filepath = f'guilds/{member.guild.id}/user/{member.id}.json'
    if not os.path.isfile(filepath):
        shutil.copyfile(f'guilds/defaults/userconfig.json', filepath)


"""
@bot.event
async def on_member_remove(member):
    os.rename(f'guilds/{member.guild.id}/user/{member.id}.json', f'guilds/{member.guild.id}/user/a_{member.id}.json')
"""


@bot.event
async def on_message_delete(message):
    if message.author.id != bot.user.id:
        log(message.author, message.channel, message.content, guild=message.guild, deleted=True)


# Clear queue if bot leaves voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id and not after.channel:
        music.clear_queue(member.guild.id)


@bot.event
async def on_raw_reaction_add(event: discord.RawReactionActionEvent):
    # Give user roles if he accepted the rules of the server by reacting to a specified message
    # Ignore bot reactions
    if event.member.id == bot.user.id:
        return

    # Get rule config
    rules = guilds_config[event.guild_id]['configuration']['rules']

    # Rule message not set up
    if rules['id'] == 0 or rules['roles'] == []:
        return

    # Reacted to rule message
    if event.message_id == rules['id']:
        # Reacted with right emoji
        if event.emoji.name == rules['reaction']:
            for role in rules['roles']:
                try:
                    await event.member.add_roles(bot.get_guild(event.guild_id).get_role(role))
                except Exception as ex:
                    print('Error adding role:\n' + str(ex))


@bot.event
async def on_raw_reaction_remove(event: discord.RawReactionActionEvent):
    # Give user roles if he accepted the rules of the server by reacting to a specified message
    # Ignore bot reactions
    if event.user_id == bot.user.id:
        return

    guild = bot.get_guild(event.guild_id)
    member = guild.get_member(event.user_id)

    # Get rule config
    rules = guilds_config[event.guild_id]['configuration']['rules']

    # Rule message not set up
    if rules['id'] == 0 or rules['roles'] == []:
        return

    # Reaction removed from rule message
    if event.message_id == rules['id']:
        # Removed reaction was right emoji
        if event.emoji.name == rules['reaction']:
            for role in rules['roles']:
                try:
                    await member.remove_roles(guild.get_role(role))
                except Exception as ex:
                    print('Error removing role:\n' + str(ex))


if __name__ == '__main__':
    try:
        # START BOT
        bot.run(token)
    except KeyboardInterrupt:
        print('Keyboard interrupt\n')
        try:
            sys.exit(0)
        except SystemExit:
            exit(0)
