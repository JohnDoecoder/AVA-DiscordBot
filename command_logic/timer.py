from helpers import write_file, read_file
import time


def toggle_timer(guid_id: int, timer_number: int):
    config = read_file.read_json(f'guilds/{guid_id}/config.json')
    if config['configuration']['timer'][f'timer{timer_number}'] == 0.0:
        return start_timer(config, timer_number, guid_id)
    else:
        return stop_timer(config, timer_number, guid_id)


def start_timer(config: dict, nr: int, guild_id: int):
    config['configuration']['timer'][f'timer{nr}'] = time.time()
    write_file.write_json(f'guilds/{guild_id}/config.json', config)

    return ['replies', nr]


def stop_timer(config: dict, nr: int, guild_id: int):
    # Calculate time the timer was running
    diff = (time.time() - config['configuration']['timer'][f'timer{nr}']) / 60

    # Set timer to 0
    config['configuration']['timer'][f'timer{nr}'] = 0.0
    write_file.write_json(f'guilds/{guild_id}/config.json', config)

    if diff < 10:
        return ['fast', "{:.2f}".format(diff) + ' min']
    elif diff > 30:
        return ['slow', "{:.2f}".format(diff) + ' min']


