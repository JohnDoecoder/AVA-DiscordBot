# Class that holds all user stats

import re
import time

import classes
import workers.files


class Person:
    def __init__(self, member, awards, idiots, eatingtime, timeseaten, timerstart, calls):
        self.member = member
        self.awards = int(awards)
        self.idiots = int(idiots)
        self.eatingtime = float(eatingtime)
        self.timeseaten = int(timeseaten)
        self.timerstart = float(timerstart)
        self.calls = int(calls)

    def __repr__(self):
        return '<Person - member: ' + str(self.member) + ', awards: ' + \
               str(self.awards) + ', idiots: ' + str(self.idiots) + ', eatingtime: ' + str(self.eatingtime) + \
               ', timeseaten: ' + str(self.timeseaten) + ', timerstart: ' + str(self.timerstart) + \
               ', counter: ' + str(self.calls) + ' >'

    def get_awards(self):
        return self.awards

    def get_idiots(self):
        return self.idiots

    def get_eatingtime(self):
        return self.eatingtime

    def get_avg_eatingtime(self):
        return (self.eatingtime / self.timeseaten) / 60 if self.timeseaten > 0 else 0

    def get_timeseaten(self):
        return self.timeseaten

    def get_name(self):
        return self.member.nick if self.member.nick else self.member.name

    def call(self, guilds_path: str, user_file: str, guild, person):
        self.calls += 1
        workers.files.set_user_value(guilds_path, user_file, guild, person, 'calls', str(self.calls))

        return self.calls

    def give_idiot(self, server, giving_person, guilds_path: str, file_name: str,
                   command):  # : classes.command.Command):
        reply = ''

        # User giving himself an award
        if self.member.id == giving_person.member.id:
            reply += server.get_reply('self_idiot') + '\n'

        # Increase Idiots
        self.idiots += 1
        workers.files.set_user_value(guilds_path, file_name, server.guild, self, 'idiots', str(self.idiots))

        reply += command.get_reply()
        return reply

    def give_award(self, server, giving_person, guilds_path: str, file_name: str,
                   command):  # : classes.command.Command):

        # User giving himself an award
        if self.member.id == giving_person.member.id:
            return server.get_reply('self_award')

        # Increase awards
        self.awards += 1
        workers.files.set_user_value(guilds_path, file_name, server.guild, self, 'awards', str(self.awards))

        return command.get_reply()

    async def timer(self, guild_path, file_name, guild):
        if self.timerstart > 0:  # Timer already running
            time_sec = time.time() - self.timerstart

            # Reset timer
            self.timerstart = 0.0
            workers.files.set_user_value(guild_path, file_name, guild, self, 'timerstart', '0.0')

            # Calculate average time
            if self.eatingtime == 0.0 or self.timeseaten == 0:
                self.eatingtime = time_sec
            else:
                self.eatingtime += time_sec

            self.timeseaten += 1
            workers.files.set_user_value(guild_path, file_name, guild, self, 'timeseaten', str(self.timeseaten))
            workers.files.set_user_value(guild_path, file_name, guild, self, 'eatingtime', str(self.eatingtime))

            return 'Timer von ' + self.get_name() + ' angehalten. Zeit: ' + str("{:.2f}".format(time_sec / 60)) + ' min'

        else:  # Timer not running
            start_time = time.time()
            workers.files.set_user_value(guild_path, file_name, guild, self, 'timerstart', str(start_time))
            self.timerstart = start_time

            return 'Timer von ' + self.get_name() + ' gestartet.'
