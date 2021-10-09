import command_logic.music
import discord


async def get_queue(ctx, music: command_logic.music.Music):
    queue = music.get_queue(ctx.guild.id)
    description = ''

    if queue:
        for i, song in enumerate(queue):
            entry = '%d: %s' % (i + 1, song['title'])
            # Indent for numbers below 10
            if i < 9:
                entry = ' ' + entry

            # Highlight currently played song
            if song == music.get_current_song(ctx.guild.id):
                description += f'**{entry}** (currently playing)\n'
            else:
                description += f'{entry}\n'

    if description:
        embed_msg = discord.Embed(
            title='Warteschlange',
            description=description
        )
        return embed_msg
