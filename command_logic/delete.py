import time


async def delete_message(ctx):
    # Delete referred message
    ref_msg = await ctx.message.channel.fetch_message(ctx.message.reference.message_id)
    await ref_msg.delete()

    # Delete the delete command message
    time.sleep(1)
    await ctx.message.delete()
