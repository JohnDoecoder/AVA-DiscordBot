import psutil
import time
import youtube_dl as yt


async def get_health(ctx, bot):
    bot_ping = round(bot.latency * 1000)

    # Testing api ping
    start_time = time.time()
    msg = await ctx.send('Testing')
    await msg.delete()
    end_time = time.time()
    api_ping = round((end_time - start_time) * 500)  # Only *500 because we executet 2 commands and want only 1

    # Cpu usage
    cpu = psutil.cpu_percent()
    # Ram usage
    ram = psutil.virtual_memory().percent

    # CPU
    if cpu < 50:
        cpu_health = 1
    elif cpu < 70:
        cpu_health = 2
    else:
        cpu_health = 3

    # RAM
    if ram < 50:
        ram_health = 1
    elif ram < 70:
        ram_health = 2
    else:
        ram_health = 3

    # Ping
    if bot_ping < 100:
        ping_health = 1
    elif bot_ping < 300:
        ping_health = 2
    else:
        ping_health = 3

    # API ping
    if api_ping < 250:
        api_health = 1
    elif api_ping < 500:
        api_health = 2
    else:
        api_health = 3

    # YouTube access
    ytdl_options = {'format': 'bestaudio', 'quiet': True}
    with yt.YoutubeDL(ytdl_options) as ytdl:
        try:
            info = ytdl.extract_info('https://yewtu.be/watch?v=1Zjwwkzbp-Y', download=False)
            yt_access = True
        except:
            yt_access = False

    # Decide health
    raw_health = cpu_health + ram_health + api_health + ping_health
    if raw_health < 5 and yt_access:
        health = 1
    elif raw_health < 8 and yt_access:
        health = 2
    else:
        health = 3

    return {
        'rating': health,
        'cpu': cpu,
        'ram': ram,
        'ping': bot_ping,
        'api': api_ping,
        'youtube': yt_access,
    }
