# Class that stores all bot information of a guild

import time
from difflib import SequenceMatcher
import discord
from random import randint

import classes.person
import workers.files


class Server:
    def __init__(self, guild, commands: list, replies: dict, user: list, prefix: str, timer: list,
                 admin_role, member_role, rule_message, rule_reaction, bot_channel):
        self.guild = guild
        self.commands = commands
        self.replies = replies
        self.user = user
        self.prefix = prefix
        self.__timer = timer
        self.paused = False

        self.bot_channel = bot_channel

        self.admin_role = admin_role  # discord.role object
        self.member_role = member_role  # discord.role object

        self.rule_reaction = rule_reaction
        self.rule_message = rule_message  # discord.message object
                                          # (You need to react with a certain emoji to this message
                                          # in order to get the self.member_role

    def __repr__(self) -> str:
        return '<Server - guild= ' + str(self.guild) + '\ncommands=\n' + str(self.commands) + '\nreplies=\n' + str(
            self.replies) + '\nuser=\n' + str(self.user) + ' >'

    async def send_error(self, channel, error):
        await channel.send(self.get_reply(error))
        return None

    def change_prefix(self, guilds_path: str, config_file: str, new_prefix: str):
        self.prefix = new_prefix
        workers.files.set_server_value(guilds_path, config_file, self.guild, 'prefix', new_prefix)

    # TODO: Add permission commands
    def add_permissions(self, command: str, permissions: list):
        pass

    def del_permissions(self, command: str, permissions: list):
        pass

    def timer(self, nr: int, guild_path, file_name):
        # Timer already running
        if float(self.__timer[nr - 1]) > 0:
            stop = time.time()
            workers.files.set_server_value(guild_path, file_name, self.guild, 'timer' + str(nr), '0')
            answer = 'Timer ' + str(nr) + ' stopped - ' + str(
                "{:.2f}".format((stop - self.__timer[nr - 1]) / 60)) + ' min'
            self.__timer[nr - 1] = 0.0
            return answer
        # Timer not running
        else:
            self.__timer[nr - 1] = time.time()
            workers.files.set_server_value(guild_path, file_name, self.guild, 'timer' + str(nr), str(time.time()))
            return 'Timer ' + str(nr) + ' started'

    def check_cmd(self, possible_cmd: str):
        highest_sim = 0
        highest_cmd = ''

        for cmd in self.commands:
            for name in cmd.aliases:
                similarity = SequenceMatcher(None, name, possible_cmd).ratio()

                if similarity > highest_sim:
                    highest_sim = similarity
                    highest_cmd = name

        return highest_cmd if highest_sim >= 0.7 else None

    def cmd_exists(self, possible_command: str):
        for command in self.commands:
            for name in command.aliases:  # The main name also is in aliases
                if name == possible_command:
                    return True

        return False

    def get_reply(self, key: str, random=True):
        try:
            reply_list = self.replies[key]
        except:
            return 'Reply does not exist'

        if not random:
            return reply_list[0]

        nr = randint(0, len(reply_list) - 1)
        return reply_list[nr]

    def get_command_list(self):
        command_string = ''
        answers = []

        for command in self.commands:
            # Make new list entry if string is too long; Discord has a max message length
            if len(command_string) > 950:  # 1024 is max length for embeds (Heading and description not in the 950)
                answers.append(command_string)
                command_string = ''

            if command.description:
                command_string += '`' + self.prefix + command.name + '`' + '\n' + command.description + '\n'

        if not len(command_string) == 0:
            answers.append(command_string)

        return answers

    def toggle_pause_bot(self):
        if self.paused:
            self.paused = False
        else:
            self.paused = True

    async def offtopic(self, message: discord.Message, channel_mention: str, ref_message: discord.Message, reply: str,
                       author: classes.person.Person):
        channel = None

        if not message.reference:
            return await self.send_error(message.channel, 'no_refering')
        if not channel_mention:
            return await self.send_error(message.channel, 'no_params')

        for chan in self.guild.channels:
            if str(chan.id) == channel_mention[2:-1]:
                channel = chan
                break

        # Channel somehow does not exist or channel is not a text channel
        if not channel or not type(channel) == discord.TextChannel:
            return await message.channel.send('Kanal existiert nicht oder ist ein kein Text-Kanal')

        # Original channel and new channel are the same
        if channel == message.channel:
            await message.channel.send("Du befindest dich bereits in " + message.channel.mention)
            return

        # Send message in specified channel
        content = ref_message.content

        if len(content) is 0:
            content = '-'

        moved_embed = discord.Embed(title="Nachricht verschoben", color=discord.Colour(0x242424))
        moved_embed.add_field(name='Offtopic: ' + author.get_name() + ' schrieb in #' + ref_message.channel.name,
                              value=content, inline=True)

        if ref_message.attachments:
            moved_embed.set_image(url=ref_message.attachments[0])
            reply = '*Media*\n'
        await channel.send(embed=moved_embed)

        # Send notice in original channel
        orig_embed = discord.Embed(title="Nachricht verschoben", color=discord.Colour(0x800000))
        orig_embed.add_field(name='Offtopic von ' + author.get_name(), value=reply,
                             inline=True)
        await message.channel.send(embed=orig_embed)

        # Delete message from wrong channel
        await ref_message.delete()

        # Delete offtopic command message
        await message.delete()
