from helpers import write_file, read_file
import discord


def give_award(guild_id: int, member_id: int):
    # Read old award count
    awards = read_file.read_stats(f'guilds/{guild_id}/user/{member_id}.json')['awards']
    # Increase award count by 1
    write_file.write_stats(guild_id, member_id, "awards", awards + 1)


def get_awards(guild: discord.Guild, member_id: int = None):
    # Return awards from one user if defined
    if member_id:
        return read_file.read_stats(f'guilds/{guild.id}/user/{member_id}.json')['awards']

    # Return awards from all users
    else:
        awards = {}
        for member in guild.members:
            awards[member.id] = read_file.read_stats(f'guilds/{guild.id}/user/{member.id}.json')['awards']

        return awards
