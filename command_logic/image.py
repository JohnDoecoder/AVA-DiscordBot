import requests
import discord


def from_url(file_path: str, url: str) -> discord.file:
    r = requests.get(url)
    with open(file_path, 'wb') as outfile:
        outfile.write(r.content)

    return discord.File(file_path, filename='image.png')
