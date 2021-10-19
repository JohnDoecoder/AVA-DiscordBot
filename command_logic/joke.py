import urllib.request as ul
from bs4 import BeautifulSoup as soup
from helpers import html
from random import randint
import re


def get_joke(ctx, cmds) -> str:
    success = False
    joke = 'Error.'
    raw_jokes = 'Error'

    while not success:
        success = True

        # Choose url
        url = cmds[ctx.invoked_with]['urls'][randint(0, len(cmds[ctx.invoked_with]['urls'])-1)]

        # Fetch site
        req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with ul.urlopen(req) as client:
            htmldata = client.read()

        # Get joke from site
        pagesoup = soup(htmldata, "html.parser")
        raw_jokes = pagesoup.findAll('div', {"class": "witz"}, limit=1)
        if not raw_jokes:
            raw_jokes = pagesoup.findAll('div', {"class": "panel-body"}, limit=1)

        # Filter raw text from joke div
        for raw_joke in raw_jokes:
            joke_title = str(raw_joke.find_next("h3"))
            joke_text = str(raw_joke.find_next("p"))
            joke = joke_title + joke_text

        # Filter: Mark bad words as spoiler
        for word in joke.split():
            f_word = re.sub(r'[^\w\s]', '', word.lower())
            if f_word in cmds[ctx.invoked_with]['filter']:
                joke = joke.replace(word, f'||{word}||')

        # Get new joke if too long for Discord
        if len(joke) > 1500:
            print('Joke too long, getting another joke')
            success = False

    # Clean joke
    joke = html.clean_text(joke)
    joke = joke.replace('\n', ' ')
    joke = joke.replace('...', '')
    while '  ' in joke:
        joke = joke.replace('  ', ' ')

    return joke
