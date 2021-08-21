import json
from classes import command


def read_command_config():
    command_config = {}

    # Read json
    with open('configuration/commands.json', 'r') as f:
        cmd = json.load(f)

    # dict from json to command object
    for key in cmd:
        command_object = command.Command(
            name=key,
            replies=cmd[key]['replies'],
            help=cmd[key]['help'],
            urls=cmd[key]['urls'],
            permissions=cmd[key]['permissions']
        )
        command_config[key] = command_object

    return command_config


def read_guild_config(guild_id: int):
    with open(f'guilds/{guild_id}/config.json', 'r') as f:
        return json.load(f)


def read_file(path: str):
    with open(path, 'r') as file:
        return file.read()


def read_credentials():
    with open('credentials.json', 'r') as f:
        return json.load(f)
