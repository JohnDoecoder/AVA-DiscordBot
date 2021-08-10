# Change values in files and get values from files

def write_user(file, member):
    file.write('[%s]\nawards=%s\nidiots=%s\neatingtime=%s\ntimeseaten=%s\ntimer=%s\ncalls=%s\n\n' %
               (member.id, 0, 0, 0.0, 0, 0.0, 0))

    print('Created user ' + member.name + ' from server ' + member.guild.name)


def delete_user(file_path, p):
    with open(file_path, 'r') as file:
        file_text = file.read()  # File in w+ mode
    file_text.replace('[%s]\nawards=%s\nidiots=%s\neat'
                      'ingtime=%s\ntimeseaten=%s\ntimer=%s\ncalls=%s\n\n' %
                      (p.member.id, p.awards, p.idiots, p.eatingtime, p.timeseaten, p.timerstart, p.calls), '')

    with open(file_path, 'w') as file:
        file.write(file_text)

    print('Deleted user ' + p.get_name() + ' in ' + file_path)


# Set userstat function for when changing eg. timer or awards in a user, that it gets changed in file as well
def set_user_value(guilds_path: str, filename: str, guild, person, attribute: str, value: str):
    with open(guilds_path + str(guild.id) + '/' + filename, 'r') as file:
        file_lines = file.read().splitlines()

    user = False

    for i, line in enumerate(file_lines):
        if line == '[' + str(person.member.id) + ']':
            user = True
            continue

        if user and line.split('=')[0] == attribute:
            file_lines[i] = str(attribute) + '=' + str(value)
            break

    file_text = ''
    with open(guilds_path + str(guild.id) + '/' + filename, 'w') as file:
        for line in file_lines:
            file_text += line + '\n'

        file.write(file_text)


# TODO: Needs checking but seems to be working (tested on Server.change_prefix())
def set_server_value(guilds_path: str, filename: str, guild, attribute: str, value: str):
    with open(guilds_path + str(guild.id) + '/' + filename, 'r') as file:
        file_text = file.read()

    for line in file_text.splitlines():
        if line.startswith(attribute):
            file_text = file_text.replace(line, attribute + '=' + value)
            break

    with open(guilds_path + str(guild.id) + '/' + filename, 'w') as file:
        file.write(file_text)
