import youtube_dl as yt
import discord
import helpers.replies as replies


async def upgrade_url(url):
    # Add or upgrade to https
    if 'http' not in url:
        url = 'https://' + url
    elif 'https' not in url:
        url.replace('http', 'https')
    return url


async def search_song(ytdl, term):
    return ytdl.extract_info(f"ytsearch:{term}", download=False)['entries'][0]


class Music:
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    ytdl_options = {
        'format': 'bestaudio',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '96'
        }]
    }
    guilds = {}

    def __init__(self, bot, message_color: hex):
        self.bot = bot
        self.message_color = message_color
        self.jumped = False

        for guild in bot.guilds:
            self.guilds[guild.id] = {
                'loop_queue': False,
                'loop_song': False,
                'current': None,
                'voice': None,
                'stopped': False,
                'queue': []
            }

    def is_playing(self, guild_id: int):
        return True if self.get_current_song(guild_id) else False

    def get_current_song(self, guild_id: int):
        if song := self.guilds[guild_id]['current']:
            return song

    def get_queue(self, guild_id: int):
        return self.guilds[guild_id]['queue']

    def clear_queue(self, guild_id: int):
        self.guilds[guild_id]['queue'] = []

    async def toggle_loop(self, ctx):
        guild_id = ctx.guild.id
        # Loop current song
        if not self.guilds[guild_id]['loop_song'] and not self.guilds[guild_id]['loop_queue']:
            self.guilds[guild_id]['loop_song'] = True
            description = 'Ein Song wird geloopt.'
        # Loop queue
        elif self.guilds[guild_id]['loop_song']:
            self.guilds[guild_id]['loop_song'] = False
            self.guilds[guild_id]['loop_queue'] = True
            description = 'Die Warteschlange wird geloopt.'
        # Stop looping
        else:
            self.guilds[guild_id]['loop_song'] = False
            self.guilds[guild_id]['loop_queue'] = False
            description = 'Loop deaktiviert.'

        await self.send_embed(
            ctx,
            title='Loop',
            description=description
        )

    async def send_embed(self, ctx, title: str = None, description: str = '', color: hex = None):
        if not color:
            color = self.message_color
        if title:
            embed_msg = discord.Embed(
                color=discord.Colour(color),
                title=title,
                description=description
            )
        else:
            embed_msg = discord.Embed(
                color=discord.Colour(color),
                description=description
            )
        await ctx.send(embed=embed_msg, delete_after=60.0)

    async def get_stream(self, arg, filter: list):
        # Create audio stream from url
        with yt.YoutubeDL(self.ytdl_options) as ytdl:
            # Direct YT-Link
            if 'yewtu.be' in arg or 'youtube.com' in arg or 'youtu.be' in arg:
                # Get video info
                try:
                    url = await upgrade_url(arg)
                    info = ytdl.extract_info(url, download=False)
                # Looked link link but does not exist
                except:
                    print(f'WARNING: Failed to open a stream from \"{url}\". Searching instead')
                    info = await search_song(ytdl, arg)
            # No Link -> Search
            else:
                info = await search_song(ytdl, arg)

        player = await discord.FFmpegOpusAudio.from_probe(info['formats'][0]['url'], **self.ffmpeg_options)
        stream = {
            'player': player,
            'url': info['formats'][0]['url'],
            'title': info['title'],
            'id': info['id'],
            'duration': info['duration'] / 60
        }

        # Block song if id is in filter list
        if filter and stream['id'] in filter:
            return None

        return stream

    async def add_song(self, ctx, arg, filter):
        # Get video stream with youtube_dl
        stream = await self.get_stream(arg, filter)

        # Add player to queue
        if stream:
            self.guilds[ctx.guild.id]['queue'].append(stream)
            # Return title of added song
            return stream['title']

    async def remove_song(self, ctx, index):
        # Remove song
        removed = self.guilds[ctx.guild.id]['queue'].pop(index)

        # Confirm removal
        await self.send_embed(ctx, title='Titel entfernt',
                              description=removed['title'])

    async def jump_to_song(self, ctx, index):
        # Return error if invalid index
        if index >= len(self.guilds[ctx.guild.id]['queue']) or index < 0:
            return 1

        self.jumped = True
        voice = self.guilds[ctx.guild.id]['voice']
        voice.stop()

        # Set new current song
        self.guilds[ctx.guild.id]['current'] = self.guilds[ctx.guild.id]['queue'][index]
        self.guilds[ctx.guild.id]['current']['index'] = index
        current = self.guilds[ctx.guild.id]['current']

        # Play new song
        await self.start_playing(ctx, voice, current)

    async def start_playing(self, ctx, voice, current):
        # Check if still connected to a voice channel
        connected = False
        for voice in self.bot.voice_clients:
            if voice.guild.id == ctx.guild.id:
                connected = True
                break
        if not connected:
            return

        index = current['index']

        # Get stream again to avoid bugs
        current = await self.get_stream('https://yewtu.be/watch?v=' + current['id'], [])  # No filter, was already filt.
        current['index'] = index
        self.guilds[ctx.guild.id]['queue'][index] = current
        self.guilds[ctx.guild.id]['current'] = current

        print('> Playing: ' + current['title'] + '\n')
        try:
            voice.play(current['player'], after=lambda x=None: self.bot.loop.create_task(self.play_next(ctx, voice)))
        except:
            print(f'WARNING: Could not play next song in {ctx.guild.name} queue.')
        await self.send_embed(
            ctx,
            title='Spielt...',
            description='%s (%s min)' % (current['title'], round(current['duration'], 2)))

    async def skip_song(self, ctx):
        voice = self.guilds[ctx.guild.id]['voice']
        voice.stop()  # Just stop audio. 'after' will play next song automatically

    async def play_song(self, ctx, voice, url, play_config: dict):
        self.guilds[ctx.guild.id]['stopped'] = False
        filter = play_config['filter']

        # Queue song
        try:
            queued = await self.add_song(ctx, url, filter)
        except Exception as ex:
            if str(ex).startswith('ERROR: No video formats found'):
                ex = 'YouTube blocked this IP-Adress. Use a VPN or a Proxy to access YouTube again.'
            await self.send_embed(ctx, title='Error', description=str(ex), color=0x800000)
            return

        # Song was blocked from filter list
        if not queued:
            return await self.send_embed(
                ctx,
                title='Song blockiert!',
                description=replies.get_reply(play_config['blocked']))

        await self.send_embed(ctx, title='Hinzugefügt', description=queued)

        # Play instantaneously if there is no current song playing
        if not self.is_playing(ctx.guild.id):
            await self.play_next(ctx, voice)

        return queued

    async def play_next(self, ctx, voice: discord.VoiceClient):
        index = None

        if self.jumped:
            self.jumped = False
            return

        current = self.guilds[ctx.guild.id]['current']
        self.guilds[ctx.guild.id]['voice'] = voice

        # Stopped or Queue empty
        if self.guilds[ctx.guild.id]['stopped'] or not self.guilds[ctx.guild.id]['queue']:
            next_song = None
        # Music was stopped or first song was just added -> pick latest song
        if not current:
            next_song = self.guilds[ctx.guild.id]['queue'][len(self.guilds[ctx.guild.id]['queue']) - 1]
            index = len(self.guilds[ctx.guild.id]['queue']) - 1
        # Song looped
        elif self.guilds[ctx.guild.id]['loop_song']:
            index = current['index']
            # Get new stream from same song
            # self.guilds[ctx.guild.id]['queue'][index] = await self.get_stream(current['id'])
            next_song = self.guilds[ctx.guild.id]['queue'][index]
        # At end of queue
        elif len(self.guilds[ctx.guild.id]['queue']) == current['index'] + 1:
            # Loop
            if self.guilds[ctx.guild.id]['loop_queue']:
                # Reinitialize Queue
                # for i, stream in enumerate(self.guilds[ctx.guild.id]['queue']):
                    # self.guilds[ctx.guild.id]['queue'][i] = await self.get_stream(stream['id'])

                next_song = self.guilds[ctx.guild.id]['queue'][0]  # Start again at first song in queue
                index = 0
            # No loop
            else:
                next_song = None
        # Play next song if there is one
        elif current['index'] + 1 < len(self.guilds[ctx.guild.id]['queue']):
            next_song = self.guilds[ctx.guild.id]['queue'][current['index'] + 1]
            index = current['index'] + 1
        else:
            print('No more audio to play')
            next_song = None

        # Mark current song
        self.guilds[ctx.guild.id]['current'] = next_song
        if index is not None:
            self.guilds[ctx.guild.id]['current']['index'] = index
        current = self.guilds[ctx.guild.id]['current']

        if current:
            await self.start_playing(ctx, voice, current)

    async def stop(self, ctx):
        self.guilds[ctx.guild.id]['current'] = None
        self.guilds[ctx.guild.id]['stopped'] = True
