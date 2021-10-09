import discord
import time


member = None


async def delete(ctx, message_id):
    # Delete referred message
    ref_msg = await ctx.message.channel.fetch_message(message_id)
    await ref_msg.delete()

    # Delete the delete command message
    time.sleep(1)
    await ctx.message.delete()


async def purge(channel, author):
    amount = 0
    global member
    member = author

    messages = await channel.purge(limit=6000, check=purge_check)
    member = None
    return len(messages)


def purge_check(message):
    return message.author == member


async def offtopic(ctx, message_id: str, channel_mention: str, color):
    # Get destination channel
    if channel_mention.startswith('<#') and channel_mention.endswith('>'):
        possible_channel = channel_mention[2:-1]
    else:
        possible_channel = channel_mention

    dest_channel = None
    for channel in ctx.guild.channels:
        if str(channel.id) == possible_channel:
            dest_channel = channel
            break

    # Get source channel
    source_channel = ctx.channel

    # Channel does not exist or channel is not a text channel
    if not dest_channel or type(dest_channel) is not discord.TextChannel:
        return 1

    # Original channel and new channel are the same
    if dest_channel == source_channel:
        return 1

    # Get message
    try:
        message = await source_channel.fetch_message(int(message_id))
    except:
        return 1

    moved_embed = discord.Embed(title="Nachricht verschoben", color=color)
    moved_embed.add_field(name=f'Offtopic: {ctx.author} schrieb in #{message.channel.name}',
                          value=message.content, inline=True)

    # TODO: Can u have multiple attachments?
    if message.attachments:
        moved_embed.set_image(url=message.attachments[0])
        reply = '*Media*\n'
    await dest_channel.send(embed=moved_embed)

    # Send notice in original channel
    orig_embed = discord.Embed(title="Nachricht verschoben", color=discord.Colour(0x800000))
    orig_embed.add_field(name=f'Offtopic von {message.author}', value=message.content,
                         inline=True)
    await message.channel.send(embed=orig_embed, delete_after=60.0)

    # Delete message from wrong channel
    await message.delete()
