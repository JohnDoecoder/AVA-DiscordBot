# Technical commands

import time


async def delete(message):
    # Delete refered message
    ref_msg = await message.channel.fetch_message(message.reference.message_id)
    await ref_msg.delete()

    # Delete the delete command message
    time.sleep(1)
    await message.delete()


def ping(client):
    bot_ping = "{:.2f}".format(client.latency * 100)
    return 'Pong! ' + str(bot_ping) + 'ms'


def debug(server):
    return [str(server.guild.name), str(server.user), str(server.commands)]


async def order_66(server):
    for user in server.user:
        if not user.member.bot:
            for role in server.guild.roles:
                if role in user.member.roles and role.name != "@everyone" and role.name != 'Admin':
                    print('Removing role ' + str(role) + ' from ' + user.get_name())
                    await user.member.remove_roles(role)

    return 'Copy that!'


async def kick_person(person):
    await person.member.edit(voice_channel=None)
    return person.get_name()
