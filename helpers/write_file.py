import os
import shutil
import discord


def write_guild_config(guild: discord.Guild, folders: list):
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


def check_create_file(filepath):
    if not os.path.isfile(filepath):
        f = open(filepath, 'w')
        f.close()
