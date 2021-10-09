import json
import os
import shutil
import discord


def init_guild_config(guild: discord.Guild, folders: list):
    # Create guild root directory
    if not os.path.isdir(f'guilds/{guild.id}/'):
        os.mkdir(f'guilds/{guild.id}/')

    # Create subfolders
    for folder in folders:
        if not os.path.isdir(f'guilds/{guild.id}/{folder}'):
            os.mkdir(f'guilds/{guild.id}/{folder}')

    # Create files
    check_create_file(f'guilds/{guild.id}/logs/memes.txt')
    check_create_file(f'guilds/{guild.id}/logs/messages.log')

    # Copy default config
    if not os.path.isfile(f'guilds/{guild.id}/config.json'):
        shutil.copyfile(f'guilds/defaults/config.json', f'guilds/{guild.id}/config.json')

    # Create user profiles
    for member in guild.members:
        filepath = f'guilds/{guild.id}/user/{member.id}.json'
        if not os.path.isfile(filepath):
            shutil.copyfile(f'guilds/defaults/userconfig.json', filepath)


def check_create_file(filepath):
    if not os.path.isfile(filepath):
        f = open(filepath, 'w')
        f.close()


def write_json(path: str, d: dict):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=4))


def write_stats(guild_id: int, member_id: int, stat: str = None, value=None):
    path = f'guilds/{guild_id}/user/{member_id}.json'

    # Read stats from file if it exists
    with open(path, 'r') as f:
        try:
            stats = json.load(f)
        except Exception as ex:
            print(ex)
            return

    # Change stats if there are new values
    if stat and value:
        stats[stat] = value

    # Write new stats to file
    write_json(path, stats)
