# Commands that send media files (pictures, videos, audios, ...)

import requests
import discord
import urllib.request
import urllib.request as ul
from bs4 import BeautifulSoup as soup
import random


def url_image(file_path: str, image_file: str, url: str):
    r = requests.get(url)

    with open(file_path + image_file, 'wb') as outfile:
        outfile.write(r.content)

    return discord.File(file_path + image_file)


def url_text(url):
    uf = urllib.request.urlopen(url)
    html = uf.read()

    split = html.splitlines()
    geschichte = ''

    for line in split:
        if '<p' in str(line):
            geschichte = str(line)
            geschichte.replace('\\\'', '\'')
            break

    return geschichte[44:-5]


def clean_text(text):
    delete = False
    clean = ''

    for char in text:
        if char == '>':
            delete = False
            continue
        elif delete:
            continue
        elif char == '<':
            delete = True
            continue
        else:
            clean += char

    return clean


def get_joke(url):
    joke = 'Error.'

    # Fetch site
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    # Get joke from site
    pagesoup = soup(htmldata, "html.parser")
    raw_jokes = pagesoup.findAll('div', {"class": "witz"})
    if len(raw_jokes) <1:
        raw_jokes = pagesoup.findAll('div', {"class": "panel-body"})

    # Filter raw text from joke div
    for raw_joke in raw_jokes:
        joke_title = str(raw_joke.find_next("h3"))
        joke_text = str(raw_joke.find_next("p"))
        joke = joke_title + '\n' + joke_text

    # Replace line breaks tags
    joke.replace('<br>', '\n')
    joke.replace('<br/>', '\n')

    # Return random joke from site after cleaning (remove links, tags, etc.)
    return '```\n' + clean_text(joke) + '\n```'


def get_quote(url):
    # Fetch site
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    # Get quotes from site
    pagesoup = soup(htmldata, "html.parser")
    raw_quotes = pagesoup.findAll('span', {"class": "quote"})
    raw_authors = pagesoup.findAll('a', {"class": "quote-btn"})

    # Return first quote with author
    quote = '```' + clean_text(str(raw_quotes[0])) + '```'
    quote += '- ' + clean_text(str(raw_authors[0]))

    return quote


def get_idea(url):
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    pagesoup = soup(htmldata, "html.parser")
    raw_idea = pagesoup.findAll('p', {"class": "lead text-dark"})

    return clean_text(str(raw_idea[0])).replace('\\', '')


def get_meme(server, reddit, guild_path: str, meme_urls: str):
    # The subreddits to choose from
    subreddits = [reddit.subreddit('cleanmemes'), reddit.subreddit('deutschememes'),
                  reddit.subreddit('MemeDerWoche/'), reddit.subreddit('memes')]

    # Go through all subreddits in a random order and pull 100 latest posts
    random.shuffle(subreddits)
    for subreddit in subreddits:
        for submission in subreddit.new(limit=100):
            new_meme = check_post(guild_path, meme_urls, submission)

            # Returned an error
            if type(new_meme) == str:
                return new_meme  # new_meme contains error msg
            # Meme wasn't new, continue search
            if not new_meme:
                continue

            # Meme was new
            # Add url to already shown memes
            with open(guild_path + meme_urls, 'a') as urls:
                urls.write(submission.url + '\n')

            return submission

    # No new meme was found
    return server.get_reply('no_memes')


def check_post(guild_path: str, meme_urls: str, post):
    # Open file with all meme urls
    try:
        with open(guild_path + meme_urls, 'r') as urls:
            urls_text = urls.read()
    except FileNotFoundError:
        return 'Error, %s not found' % guild_path + meme_urls

    # Meme has already been shown or Meme is not an image
    if post.url in urls_text or "https://i.redd.it/" not in post.url:
        return False

    return True
