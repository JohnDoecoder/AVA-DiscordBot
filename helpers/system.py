import os
import sys


def reboot(reason: str = 'Empty'):
    print(f'Rebooting! Reason: {reason}')
    os.execl(sys.executable, '"{}"'.format(sys.executable), *sys.argv)
