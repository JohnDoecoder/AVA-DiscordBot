from helpers import write_file, read_file
import discord


def give_award(guild_id: int, member_id: int):
    # Read old award count
    awards = read_file.read_json(f'guilds/{guild_id}/user/{member_id}.json')['awards']
    # Increase award count by 1
    write_file.write_stats(guild_id, member_id, "awards", awards + 1)


def get_awards(guild: discord.Guild, mentions: tuple = None):
    awards = {}
    # Awards from users if defined
    if mentions:
        for mention in mentions:
            try:
                member_id = int(mention[3:-1])  # Extract id from mention
                awards[member_id] = read_file.read_json(f'guilds/{guild.id}/user/{member_id}.json')['awards']
            except:
                return
    # Awards from all users
    else:
        for member in guild.members:
            awards[member.id] = read_file.read_json(f'guilds/{guild.id}/user/{member.id}.json')['awards']

    return awards


def give_idiot(guild_id: int, member_id: int):
    # Read old idiot count
    idiots = read_file.read_json(f'guilds/{guild_id}/user/{member_id}.json')['idiots']
    # Increase idiot count by 1
    write_file.write_stats(guild_id, member_id, "idiots", idiots + 1)


def get_idiots(guild: discord.Guild, mentions: tuple = None):
    idiots = {}
    # Awards from users if defined
    if mentions:
        for mention in mentions:
            try:
                member_id = int(mention[3:-1])  # Extract id from mention
                idiots[member_id] = read_file.read_json(f'guilds/{guild.id}/user/{member_id}.json')['idiots']
            except:
                print(f'> Warning: get_awards - Member with mention {mention} not found.')
    # Awards from all users
    else:
        for member in guild.members:
            idiots[member.id] = read_file.read_json(f'guilds/{guild.id}/user/{member.id}.json')['idiots']

    return idiots
