import urllib.request as ul
from bs4 import BeautifulSoup as soup
from helpers import html
from random import randint


def get_joke(ctx, cmds) -> str:
    success = False
    joke = 'Error.'
    raw_jokes = 'Error'

    while not success:
        success = True

        # Choose url
        url = cmds[ctx.invoked_with]['urls'][randint(0, len(cmds[ctx.invoked_with]['urls']))]

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

        # Filter: Get new joke if bad word in it
        for word in cmds[ctx.invoked_with]['filter']:
            if word in joke:
                print('Bad word detected getting another joke. Joke was: ' + str(joke))
                success = False

            # Get new joke if too long for Discord
            if len(joke) > 1500:
                print('Joke too long, getting another joke')
                success = False

    # Clean joke
    joke = html.clean_text(joke)
    joke = joke.replace('\n', '')
    joke = joke.replace('...', '')
    while '  ' in joke:
        joke = joke.replace('  ', ' ')

    return joke
