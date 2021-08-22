import json
import os
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


def read_file(path: str):
    with open(path, 'r') as file:
        return file.read()


def read_json(path: str):
    with open(path, 'r') as f:
        return json.load(f)


def read_stats(path: str):
    # Create stats if file is non existent
    if not os.path.isfile(path):
        stats = {
            "awards": 0,
            "idiots": 0,
            "eating": {
                "timer": 0,
                "amount": 0,
                "time": 0
            },
            "calls": 0,
            "games": {
                "game1": {
                    "wins": 0,
                    "losses": 0,
                    "extra1": 0,
                    "extra2": "",
                },
                "game2": {
                    "wins": 0,
                    "losses": 0,
                    "extra1": 0,
                    "extra2": "",
                },
                "game3": {
                    "wins": 0,
                    "losses": 0,
                    "extra1": 0,
                    "extra2": "",
                }
            }
        }

        with open(path, 'w') as f:
            f.write(json.dumps(stats))

    with open(path, 'r') as f:
        return json.load(f)
