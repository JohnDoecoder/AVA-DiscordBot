from helpers import write_file, read_file
import time


def toggle_timer(ctx):
    config = read_file.read_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json')
    if config['eating']['timer'] in [0, 0.0]:
        return start_timer(ctx, config)
    else:
        return stop_timer(ctx, config)


def start_timer(ctx, config: dict):
    # Get starting time
    config['eating']['timer'] = time.time()
    # Increase times eaten
    config['eating']['amount'] += 1
    write_file.write_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json', config)

    return ['start', 0]


def stop_timer(ctx, config: dict):
    # Calculate time the timer was running
    diff = round((time.time() - config['eating']['timer']) / 60, 2)

    # Set timer to 0
    config['eating']['timer'] = 0
    # Add time to total eating time
    config['eating']['time'] += diff
    write_file.write_json(f'guilds/{ctx.guild.id}/user/{ctx.author.id}.json', config)

    if diff < 16:
        return ['fast', diff]
    elif diff < 40:
        return ['reasonable', diff]
    else:
        return ['slow']


def get_stats(guild_id: int, member_id: int):
    config = read_file.read_json(f'guilds/{guild_id}/user/{member_id}.json')
    return config['eating']


