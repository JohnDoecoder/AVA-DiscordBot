# All the functions to manage the bot (changing prefix, accept commands from other bots, ...)
# And reading/changing the config

import os
import shutil

from classes.server import Server
from classes.person import Person
from classes.command import Command
import workers.files as files


# --- Helper functions ---

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except OSError:
        print('Could not open ' + file_path)

# --- Helper functions ---


def server_configuration(guilds_path, guild, config_file: str):
    config_text = read_file(guilds_path + str(guild.id) + '/' + config_file)
    config = {}

    for line in config_text.splitlines():
        if not line or line.startswith('#'):
            continue

        split = line.split('=', 1)
        config[split[0]] = split[1]

    return config


def servers(defaults_path: str, guilds_path: str, tmp_path: str, client, files: dict):
    server = {}

    print('Initializing servers...')
    for guild in client.guilds:
        # Create guild folder if it does not exist
        if not os.path.isdir(guilds_path + str(guild.id)):
            os.mkdir(guilds_path + str(guild.id))
            print('Created folder for guild ' + str(guild.name))

        if not os.path.isdir(guilds_path + str(guild.id) + tmp_path):
            os.mkdir(guilds_path + str(guild.id) + tmp_path[:-1])
            print('Created tmp folder in ' + str(guild.name))

        # Copy files if they don't exist
        for file in files.values():
            print('Checking file ' + guilds_path + str(guild.id) + '/' + file)

            if not os.path.isfile(guilds_path + str(guild.id) + '/' + file):
                shutil.copyfile(defaults_path + file, guilds_path + str(guild.id) + '/' + file)
                print('copied file ' + file + ' to folder ' + str(guild.id))

        # Get server configuration
        server_config = server_configuration(guilds_path, guild, files['configuration'])
        print('\nServer configuration is:\n' + str(server_config) + '\n')

        # Initialize user stats if there are none
        user_stats(guilds_path, files['users'], guild)

        # Create server objects
        persons = person_objects(guilds_path, files['users'], guild)
        cmds = commands(guilds_path, files['commands'], files['permissions'], files['urls'], files['replies'], guild)
        server[guild.id] = (Server(guild,
                                   cmds[0],  # Command replies
                                   cmds[1],  # Server replies
                                   persons,
                                   server_config['prefix'],
                                   [server_config['timer1'], server_config['timer2'], server_config['timer3']],
                                   server_config['admin_role'],
                                   server_config['member_role'],
                                   server_config['rule_message'],
                                   server_config['rule_reaction'],
                                   server_config['bot_channel']))

    # Just for possible debug
    try:
        print('\nCreated serverlist:\n' + str(server[guild.id].guild))
    except:
        print('\nERROR: Serverlist could not be printed - Guild object missing')

    return server


def commands(guilds_path: str, cmd_filename: str, perm_filename: str, url_filename: str, replies_filename: str, guild):
    cmd_text = read_file(guilds_path + str(guild.id) + '/' + cmd_filename)
    perm_text = read_file(guilds_path + str(guild.id) + '/' + perm_filename)
    replies_text = read_file(guilds_path + str(guild.id) + '/' + replies_filename)
    urls_text = read_file(guilds_path + str(guild.id) + '/' + url_filename)
    tmp_commands = {}
    server_replies = {}

    # Get command names and description
    for line in cmd_text.splitlines():
        if not line or line.startswith('#'):
            continue

        command = line.split('=', 1)  # command: ping, latency = This is a description

        tmp_names = command[0].replace(' ', '').split(',')
        tmp_commands[tmp_names[0]] = {'names': tmp_names, 'description': command[1], 'permissions': None, 'urls': None, 'replies': None}

    # Get permissions for the commands
    for line in perm_text.splitlines():
        if not line or line.startswith('#'):
            continue

        permission = line.split('=', 1)
        if permission[0] in tmp_commands:
            tmp_commands[permission[0]]['permissions'] = permission[1].replace(' ', '').split(',')
        else:
            tmp_commands[permission[0]] = {'names': [permission[0]], 'description': None, 'permissions': permission[1].replace(' ', '').split(','),
                                           'urls': None, 'replies': None}

        # Creating name for command if it is not commands.cfg and therefore has none so far,
        # because it's a secret command
        if not 'names' in tmp_commands[permission[0]]:
            tmp_commands[permission[0]]['names'] = permission[0].replace(' ', '').split(',')

    # Get replies for command
    for line in replies_text.splitlines():
        if not line or line.startswith('#'):
            continue

        reply = line.split('=', 1)
        # Command for replies exists
        if reply[0] in tmp_commands:
            if len(reply) == 1:
                tmp_commands[reply[0]]['replies'] = None
            else:
                tmp_commands[reply[0]]['replies'] = reply[1].split('|')
        # No command for replies -> is server reply
        else:
            server_replies[reply[0]] = reply[1].split('|')

    # Get possible urls of command
    for line in urls_text.splitlines():
        if not line or line.startswith('#') or not '=' in line:
            continue

        url = line.split('=', 1)
        if url[0] in tmp_commands:
            tmp_commands[url[0]]['urls'] = url[1].replace(' ', '').split('|')
        else:
            print('Kein Command für die url ' + url[0] + ': ' + url[1] + ' gefunden.')

    # Create secret geheim command
    tmp_commands['geheim'] = {'names': ['geheim'], 'description': None, 'permissions': None, 'urls': None,
                              'replies': ['Hilfe, ich wurde entdeckt!!!']}

    # Create command objects
    command_list = []
    for cmd in tmp_commands:
        print('Initializing command ' + str(tmp_commands[cmd]['names'][0]))
        command_list.append(Command(cmd, tmp_commands[cmd]['names'],
                                    tmp_commands[cmd]['description'],
                                    tmp_commands[cmd]['permissions'],
                                    tmp_commands[cmd]['replies'],
                                    tmp_commands[cmd]['urls']))

    print('\n')
    return [command_list, server_replies]


def create_person(guild, p):
    return Person(guild.get_member(int(p['id'])), p['awards'], p['idiots'], p['eatingtime'], p['timeseaten'],
           p['timer'], p['calls'])


def person_objects(guilds_path: str, person_file: str, guild) -> list:
    file = open(guilds_path + str(guild.id) + '/' + person_file, 'r')
    p = {}
    person_list = []

    for line in file.read().splitlines():
        if line.startswith('#') or not line:
            continue

        if line.startswith('[') and line.endswith(']'):
            # Create new person if next user entry is starting
            if len(p) > 0 or not p == {}:
                person_list.append(create_person(guild, p))
                print('Created person ' + str(p))
                p = {}

            p['id'] = line[1:-1]
            continue

        # Write entry to temp person
        split = line.split('=')
        p[split[0]] = split[1]

    print('Created person ' + str(p) + '\n')
    person_list.append(create_person(guild, p))
    return person_list


def user_stats(guilds_path: str, filename: str, guild):
    # Check if file exists / is empty
    file = open(guilds_path + str(guild.id) + '/' + filename, 'a+')
    file.seek(0)  # Read file from beginning
    file_text = file.read()

    if len(file_text) != 0:
        user_list = []

        # Grab users from file
        for line in file_text.splitlines():
            if line.startswith('[') and line.endswith(']'):
                user_list.append(line[1:-1])

        # Write user if id is not in file
        for member in guild.members:
            if str(member.id) not in user_list:
                files.write_user(file, member)

    else:
        for member in guild.members:
            files.write_user(file, member)

    # No return, since values are getting written directly into person objects
