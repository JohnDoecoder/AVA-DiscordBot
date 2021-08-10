# Main program for the discord bot

import discord
import datetime
import sys
import time

import classes.person
import classes.server
import classes.command
import workers
import workers.initialize
import workers.files
import commands.simple as simple
import commands.internal as internal
import commands.media as media
import praw

# Paths of config files
DEFAULT_PATH = 'defaults/'
GUILDS_PATH = 'guilds/'
TMP_DATA_PATH = 'tmp_data/'
COMMANDS_FILE = 'commands.cfg'
PERMISSIONS_FILE = 'permissions.cfg'
REPLIES_FILE = 'replies.cfg'
URLS_FILE = 'urls.cfg'
CONFIG_FILE = 'server.cfg'
USER_STATS_FILE = 'user.stats'
LOGS_FILE = 'messagelog.log'
PERSON_FILE = 'person.jpg'
CAT_FILE = 'cat.jpg'
MEME_URLS_FILE = 'meme_urls.txt'
MEME_IMAGE = 'meme.example'

intents = discord.Intents().all()
client = discord.Client(intents=intents)
reddit = praw.Reddit(client_id='ID',
                     client_secret='SECRET',
                     user_agent='Private Discord bot - meme grabber by /u/USER',
                     check_for_async=False)

ignore_all = False

global servers


# Log to file and print to console
def logprint(guild, author, channel, message):
    time = datetime.datetime.now()
    # 2021-05-21 16:38:27 | (user in channel) - This is a message
    log = str(time)[:-7] + ' | ' + '(' + author + ' in ' + channel + ')' + ' - ' + message + '\n'

    with open(GUILDS_PATH + str(guild.id) + '/' + LOGS_FILE, 'a', encoding='utf-8') as logfile:
        logfile.write(log)

    print(guild.name + ':\n' + log)


def get_person(server: classes.server.Server, user_id: int = None) -> classes.person.Person:
    for person in server.user:
        if person.member.id == user_id:
            return person

    return None  # If there is no user with that id


def get_person_n(server: classes.server.Server, user_name: str = None) -> classes.person.Person:
    for person in server.user:
        if person.member.name.lower() == user_name or person.member.nick.lower() == user_name:
            return person

    return None  # If there is no user with that id


def get_server(guild_id: int) -> classes.server.Server:
    return servers[guild_id]


def get_channel(guild: discord.guild, channel_id: int) -> discord.abc.GuildChannel:
    return guild.get_channel(channel_id)


def get_command(server, cmd_name: str) -> classes.command.Command:
    for command in server.commands:
        if cmd_name in command.aliases:
            return command

    return None


def read_file(file_path) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except OSError:
        logoff('Could not open ' + file_path)


def logoff(reason):
    client.user.setStatus("offline")
    client.user.setActivity('the sleeping game', {type: "PLAYING"})
    client.close()
    sys.exit(reason)


@client.event
async def on_ready():
    global servers
    servers = workers.initialize.servers(DEFAULT_PATH, GUILDS_PATH, '/' + TMP_DATA_PATH, client,
                                         {'commands': COMMANDS_FILE, 'permissions': PERMISSIONS_FILE,
                                          'replies': REPLIES_FILE, 'configuration': CONFIG_FILE,
                                          'users': USER_STATS_FILE, 'urls': URLS_FILE, 'logs': LOGS_FILE,
                                          'meme_urls_file': MEME_URLS_FILE})

    for server in servers:
        logprint(servers[server].guild, 'System', 'Console', 'Logged in as {0.user}'.format(client))

    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                           name='Euren Nachrichten'))

    # await channel_bot.send('Ich bin wieder da!')


@client.event
async def on_message(message):
    global client
    global ignore_all

    # TODO: Create new logfile in main folder for dms
    # Handle DMs from specific person :D
    if type(message.channel) == discord.channel.DMChannel:
        # TODO: No hardcoding!
        if message.author.id == ID:
            # logprint("Bot DM", message.author.name, "DM", message.content)
            try:
                msg_l = message.content.split(' ', 2)
                server = get_server(int(msg_l[0]))
                channel = server.guild.get_channel(int(msg_l[1]))
                
                await channel.send(msg_l[2])
            except:
                await message.channel.send("Error")
        else:
            # Just ignore other DMs for now
            pass
        return

    server = get_server(message.guild.id)

    async def c_send(m='', pFile=None, embed=False, e_name='', e_title='', e_image='', e_color: int = 0x00ff00):
        if pFile:
            await message.channel.send(file=pFile)
        elif embed:
            embed_var = discord.Embed(title=e_title, color=discord.Colour(e_color))
            embed_var.add_field(name=e_name, value=m, inline=True)
            if len(e_image) > 0:
                embed_var.set_image(url=e_image)
            await message.channel.send(embed=embed_var)
        else:
            await message.channel.send(m)

    # Log message
    logprint(server.guild, message.author.name, message.channel.name, message.content)

    # Embeded messages from Groovy
    if message.author.name == 'Groovy' and message.embeds:
        song = message.embeds[0].description.lower()
        # Mute groovie on specific song xD
        if (("gandalf" in song and "sax" in song) or ("epic" in song and "sax" in song)) and "queued" not in song:
            time.sleep(1)

            # Kicking doesn't work that well, Groovy gets confused
            # await internal.kick_person(get_person(server, user_id=message.author.id))

            await message.author.edit(mute=True)
            await c_send('Ich möchte dieses Lied einfach nicht hören!')
            return

        elif "queued" not in song:
            # Unmute Groovy
            try:
                await message.author.edit(mute=False)
                return
            except:
                logprint(server.guild, 'System', 'Console', 'Groovy was not in voice chat, fix this issue Dev!')

    # Ignore own messages
    if message.author.id == client.user.id or message.author.id == BOT_ID:
        return

    # Ignore messages without prefix (no command) and some more
    if not message.content.startswith(server.prefix) or ignore_all or len(message.content) < 2:
        return

    # Get details about message
    person = get_person(server, user_id=message.author.id)
    username = person.get_name()
    msg = message.content.lower()

    if message.reference:
        ref_msg = await message.channel.fetch_message(message.reference.message_id)
        ref_person = get_person(server, ref_msg.author.id)
    else:
        ref_msg = None
        ref_person = None
    possible_cmd = msg.split(' ', 1)[0][1:]

    # Check if command exists
    if not server.cmd_exists(possible_cmd):
        if server.paused:
            return
        # See if command is a typo and return possible right command (else return None)
        possible_cmd = server.check_cmd(possible_cmd)
        if possible_cmd:
            await c_send(server.get_reply('unknown_cmd') +
                         ' Meintest du `' + server.prefix + possible_cmd + '`?')
        else:
            await c_send(server.get_reply('unknown_cmd'))

        return

    # Command exists -> Get command object
    command = get_command(server, possible_cmd)
    # 
    if not command:
        await c_send(simple.answer(server.get_reply('error'), insert='get_command() didn\'t return a command'))

    # Check permissions
    if not server.paused and not command.user_has_permission(message.author):
        await c_send(server.get_reply('no_permission'))
        return

    # Special pause/resume commands
    if command.name == 'pause' and not server.paused:
        server.toggle_pause_bot()
        await c_send(command.get_reply())
        return

    if command.name == 'resume' and server.paused:
        server.toggle_pause_bot()
        await c_send(command.get_reply())
        return

    # Do nothing if bot is paused
    if server.paused:
        return

    # Check if the command has parameters
    if len(msg.split()) > 1:
        params = msg.split(' ', 1)[1]
    else:
        params = None

    # --- Start checking and executing the commands ---
    if command.name == 'quit':
        await c_send(simple.answer(command.get_reply()))
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.custom,
                                                               name='Im Schönheitsschlaf',
                                                               status=discord.Status.offline))

        # Logoff Bot from discord and end async functions, resulting in the last line of this file (quit())
        await client.close()

    elif command.name == 'ping':
        await c_send(internal.ping(client))

    elif command.name == 'debug':
        for entry in internal.debug(server):
            if len(entry) > 1500:
                await c_send(entry[:1500] + '-\n')
                await c_send(entry[1500:] + '\n')
            else:
                await c_send(entry + '\n')

    elif command.name == 'drohanruf':
        await c_send(simple.answer(command.get_reply(), name=username) +
                     ' Drohanruf Nr. **' +
                     str(person.call(GUILDS_PATH, USER_STATS_FILE, server.guild, person)) +
                     '**')

    elif command.name == 'quote':
        await c_send(media.get_quote(command.get_url()))

    elif command.name == 'joke':
        await c_send(media.get_joke(command.get_url()))

    elif command.name == 'test':
        await c_send(command.get_reply())

    elif command.name == 'essen':
        await c_send(await person.timer(GUILDS_PATH, USER_STATS_FILE, server.guild))

    elif command.name == 'langeweile':
        await c_send(command.get_reply() + '\n```' + media.get_idea(command.get_url()) + '```')

    elif command.name == 'essensstats':
        if not params:
            reply = ''
            for user in server.user:
                reply += simple.answer(command.get_reply(), name=user.get_name(), insert=str(user.get_timeseaten()),
                                       insert2="{:.2f}".format(user.get_avg_eatingtime())) + '\n'
            await c_send(reply)
            return

        else:
            try:
                person_mentioned = get_person(server, int(params[3:-1]))  # Extract user id from mention
            except:
                await c_send(simple.answer(server.get_reply('error'),
                                           insert='Bitte eine Person mentionen!'))
                return

            await c_send(simple.answer(command.get_reply(),
                                       name=person_mentioned.get_name(),
                                       insert=str(person_mentioned.get_timeseaten()),
                                       insert2=str("{:.2f}".format(person_mentioned.get_avg_eatingtime()))
                                       ))
            return

    elif command.name == 'würfel':
        await c_send(simple.answer(command.get_reply(), insert=str(simple.dice()), mention=person.member.mention))

    elif command.name == 'Münzwurf':
        await c_send(simple.answer(command.get_reply(), insert=str(simple.cointoss(params[0], params[2])),
                                   mention=person.member.mention),
                     e_image='CoinToss.gif', e_title="Münzwurf", e_name=person.get_name() + "hat eine Münze geworfen!")

    elif command.name == 'timer':
        if not params or params not in ['1', '2', '3']:
            await c_send('Bitte eine gültige Timernummer angeben')
            return

        await c_send(server.timer(int(params), GUILDS_PATH, CONFIG_FILE))

    # Two commands in one - Same function with different params
    elif command.name == 'morgen' or command.name == 'hallo':
        await c_send(simple.answer(command.get_reply(), mention=person.member.mention))
        return

    # Two commands in one - Same function with different params
    elif command.name == 'person' or command.name == 'cat':
        await c_send(simple.answer(command.get_reply()))
        image_file = PERSON_FILE if command.name == 'person' else CAT_FILE
        await c_send(pFile=media.url_image(GUILDS_PATH + str(server.guild.id) + '/' + TMP_DATA_PATH,
                                           image_file, command.get_url()))
        return

    elif command.name == 'commands':
        # await c_send(command.get_reply())

        # Long messages need to be split into multiple
        reply_list = server.get_command_list()
        for msg_nr, part in enumerate(reply_list):
            await c_send(part, embed=True, e_name='Seite ' + str(msg_nr + 1), e_title="Commands")

        return

    elif command.name == 'capecrafter':
        await c_send(simple.answer(command.get_reply() + command.get_url()))
        return

    elif command.name == 'grrr':
        if message.author.id == SPECIAL_USER_ID:
            await c_send('Hast du deinen Kaffee verschüttet, ' + person.get_name() + '?')
        else:
            await c_send(simple.answer(command.get_reply(), addon=command.get_url(), name=person.get_name()))
        return

    elif command.name == 'offtopic':
        tmp_message = ''

        if len(ref_msg.content) > 0:
            tmp_message += ref_msg.content
        tmp_message += '\n' + simple.answer(command.get_reply(), channel=params, ref_mention=ref_msg.author.mention)

        # Move message
        await server.offtopic(message, params, ref_msg, tmp_message, ref_person)
        return

    elif command.name == 'idiot':
        # Not referred to a message
        if not ref_msg:
            await c_send(simple.answer(server.get_reply('no_referring'), mention=person.member.mention))
            return

        await c_send(simple.answer(ref_person.give_idiot(server, person, GUILDS_PATH, USER_STATS_FILE, command),
                                   mention=person.member.mention, ref_mention=ref_person.member.mention))

        logprint(server.guild, 'System', 'Console', '!idiot referred to: \"' +
                 ref_msg.content + '\" from ' + ref_person.get_name())

    elif command.name == 'idiots':
        # No user specified -> return all users
        if not params:
            all_idiots = ''
            for idiot in server.user:
                all_idiots += simple.answer(command.get_reply(), ref_name=idiot.get_name(),
                                            insert=str(idiot.get_idiots())) + '\n'

            await c_send(all_idiots)
            return

        # User specified
        try:
            possible_person = get_person(server, user_id=int(params[3:-1]))
            await c_send(simple.answer(command.get_reply(),
                                       insert=str(possible_person.get_idiots()),
                                       ref_name=possible_person.get_name()))
        except:
            await c_send(simple.answer(server.get_reply('error'), insert='Ich konnte den User nicht finden...'))

        return

    elif command.name == 'wiki':
        if not params:
            await c_send(server.get_reply('no_params'))
            return
        await c_send(simple.answer(command.get_reply(), url=command.get_url(), search=params))
        return

    elif command.name == 'internet':
        await c_send(simple.answer(command.get_reply(), mention=person.member.mention))
        return

    elif command.name == 'help':
        await c_send(simple.answer(command.get_reply(), prefix=server.prefix))
        return

    elif command.name == 'meme':
        meme = media.get_meme(server, reddit, GUILDS_PATH + str(server.guild.id) + '/', MEME_URLS_FILE)

        if type(meme) == str:
            await c_send(meme)
        else:
            await c_send('Subreddit: ' + str(meme.subreddit), embed=True, e_title=meme.title, e_name=meme.author,
                         e_image=meme.url, e_color=0x242424)
        return

    elif command.name == 'award':
        # Not referred to a message
        if not ref_msg:
            await c_send(simple.answer(server.get_reply('no_referring'), mention=person.member.mention))
            return

        await c_send(simple.answer(ref_person.give_award(server, person, GUILDS_PATH, USER_STATS_FILE, command),
                                   mention=person.member.mention, ref_mention=ref_person.member.mention))

        logprint(server.guild, 'System', 'Console', '!award referred to: \"' +
                 ref_msg.content + '\" from ' + ref_person.get_name())

    elif command.name == 'awards':
        # No user specified -> return all users
        if not params:
            all_awards = ''
            for awarded in server.user:
                all_awards += simple.answer(command.get_reply(), ref_name=awarded.get_name(),
                                            insert=str(awarded.get_awards())) + '\n'

            await c_send(all_awards)
            return

        # User specified
        try:
            possible_person = get_person(server, user_id=int(params[3:-1]))
            await c_send(simple.answer(command.get_reply(),
                                       insert=str(possible_person.get_awards()),
                                       ref_name=possible_person.get_name()))
        except:
            await c_send(simple.answer(server.get_reply('error'), insert='Ich konnte den User nicht finden...'))

        return

    elif command.name == 'delete':
        if not message.reference:
            await c_send(simple.answer(server.get_reply('no_referring'), mention=person.member.mention))
            return

        await internal.delete(message)
        return

    elif command.name == 'prefix':
        if params is None:
            await c_send(server.get_reply('no_params'))
        elif len(params) == 1:
            server.change_prefix(GUILDS_PATH, CONFIG_FILE, params)
            await c_send(simple.answer(command.get_reply(), prefix=server.prefix))
        else:
            await c_send(simple.answer(server.get_reply('error'), insert='Bitte nur ein Zeichen als Prefix angeben.'))

    elif command.name == 'geheim':
        await c_send(command.get_reply())

    elif command.name == 'order66':
        reply = await internal.order_66(server)
        await c_send(reply)

    elif command.name == 'kick':
        try:
            person_mentioned = get_person(server, int(params[3:-1]))  # Extract user id from mention
        except:
            await c_send(simple.answer(server.get_reply('error'),
                                       insert='Bitte eine Person mentionen!'))
            return

        await c_send(simple.answer(command.get_reply(),
                                   ref_name='`' + await internal.kick_person(person_mentioned) + '`'))
        return


@client.event
async def on_member_join(member):
    # Write in user.stats TODO: Test
    with open(GUILDS_PATH + str(member.guild.id) + '/' + USER_STATS_FILE, 'a') as file:
        workers.files.write_user(file, member)

    # Create person object and append to person list in server
    tmp_person = {'id': member.id, 'awards': 0, 'idiots': 0, 'eatingtime': 0, 'timeseaten': 0, 'timer': 0, 'calls': 0}
    server = get_server(member.guild.id)
    server.user.append(workers.initialize.create_person(server.guild, tmp_person))


@client.event
async def on_member_remove(member):
    server = get_server(member.guild.id)
    person = get_person(server, member.id)

    # Delete in file
    workers.files.delete_user(GUILDS_PATH + str(member.guild.id) + '/' + USER_STATS_FILE, person)

    # Delete in server object
    for i, u in enumerate(server.user):
        if u.member.id == member.id:
            del server.user[i]
            return


@client.event
async def on_raw_reaction_add(reaction):
    server = get_server(reaction.guild_id)
    channel = client.get_channel(reaction.channel_id)
    message = await channel.get_partial_message(reaction.message_id).fetch()
    member_role = server.guild.get_role(server.member_role)

    if message.id == server.rule_message and reaction.emoji.name == server.rule_reaction:

        if member_role in reaction.member.roles:
            await channel.send(reaction.member.name +
                               ' hat die Serverregeln akzeptiert, hat aber schon die Mitgliederrolle!')
            return

        await reaction.member.add_roles(server.guild.get_role(server.member_role))
        await channel.send(reaction.member.name + ' hat die Serverregeln akzeptiert!')


@client.event
async def on_raw_reaction_remove(reaction):
    server = get_server(reaction.guild_id)
    channel = client.get_channel(reaction.channel_id)
    message = await channel.get_partial_message(reaction.message_id).fetch()
    member_role = server.guild.get_role(server.member_role)

    if message.id == server.rule_message:
        await channel.send(reaction.member.name + ' hat die Serverregeln widerrufen.')

        if member_role in reaction.member.roles:
            # Delete Role
            await reaction.remove_roles(member_role)
            return

        channel.send(reaction.member.name + ' hat die Serverregeln abgelehnt, hatte die Mitgliederrolle aber nicht.')


client.run('TOKEN')
quit(1)
