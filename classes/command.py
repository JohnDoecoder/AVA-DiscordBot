# A command and its permissions

from random import randint


class Command:
    def __init__(self, name: str, help: str, permissions: list, replies: list, urls: list):
        self.name = name
        self.help = help
        self.permissions = permissions
        self.replies = replies
        self.urls = urls

    def __repr__(self):
        return f'name: {self.name}; help: {self.help}; replies: {self.replies}; urls: {self.urls}'

    def add_permission(self, permissions: list):
        print('Adding permissions ' + str(permissions) + ' to ' + self.name)
        self.permissions.extend(permissions)
        print('New permissions from ' + self.name + ': ' + str(self.permissions))

    def del_permission(self, permissions: list):
        for permission in permissions:
            if permission in self.permissions:
                print('Removing permission ' + permission + ' from ' + self.name)
                self.permissions.remove(permission)
            else:
                print('Tried to remove not existent permission ' + permission + ' from command ' + self.name)

    def user_has_permission(self, member):
        # Check if permissions are not restricted
        if not self.permissions:
            return True

        # Check if the member (id) is allowed
        if str(member.id) in self.permissions:
            return True

        # Check if a role of the member is allowed
        for role in member.roles:
            if '(' + str(role.id) + ')' in self.permissions:
                return True

        return False

    def get_reply(self):
        nr = randint(0, len(self.replies) - 1)
        return self.replies[nr]

    def get_url(self, random=True):
        if not random:
            return self.urls[0]  # Urls is a list, even if there is only one url

        nr = randint(0, len(self.urls) - 1)
        return self.urls[nr]
