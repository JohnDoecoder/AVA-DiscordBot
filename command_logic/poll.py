import discord


async def create_poll(ctx, args, bot_config):
    # Crete description of embed
    description = ''
    options = {args[1]: '🟠', args[2]: '🔵'}  # Orange, Blue
    if len(args) > 3:
        options[args[3]] = '🟢'  # Green
    if len(args) > 4:
        options[args[4]] = '🟣'  # Purple
    if len(args) > 5:
        options[args[5]] = '🟡'  # Yellow

    for option in options:
        description += f'{options[option]} {option}\n'

    # Create embed
    embed_var = discord.Embed(
        title=args[0],
        color=discord.Colour(int(bot_config['colors']['default'], 16)),
        description=description[:-1])  # Remove last \n
    # Send Poll message
    message = await ctx.send(embed=embed_var)

    # Add poll options (reactions) to message
    for option in options:
        await message.add_reaction(options[option])
