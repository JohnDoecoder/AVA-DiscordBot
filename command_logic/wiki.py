import urllib.request as ul
from bs4 import BeautifulSoup as soup
from helpers import html


def get_wiki(url, search: str):
    search = search.replace(' ', '_')  # No blanks in urls
    wiki_url = f"{url}/wiki/{search}"

    # Check if special random was used
    if search.lower() == 'random':
        wiki_url = f'{url}/wiki/Spezial:Zuf%C3%A4llige_Seite'

    req = ul.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})

    # Check if entry exists
    try:
        with ul.urlopen(req) as client:
            htmldata = client.read()
    except:  # Not clean, I know
        return f"{url}/w/index.php?search={search}"

    # Get site
    pagesoup = soup(htmldata, "html.parser")
    description = pagesoup.findAll('div', {"class": "mw-parser-output"}, limit=1)[0]

    if 'steht für:' in str(pagesoup):
        return f"{url}/w/index.php?search={search}"

    # Get link of article if it was chosen randomly
    if search == 'random':
        title = html.clean_text(str(pagesoup.findAll('h1', {"class": "firstHeading"}, limit=1)[0]))
        title = title.replace(' ', '_')
        wiki_url = f'{url}/wiki/{title}'

    # Get description from html
    passage = False
    answer = ''
    for word in str(description).replace('<div class="mw-parser-output">', '').split():
        if not passage and '<p' in word:
            passage = True
        if passage and ('div' in word or '</p' in word):
            break
        if passage:
            answer += ' ' + word + ''

    # Clean up text from html fragments
    answer = html.clean_text(answer)

    # Shorten text at blank
    if len(answer) > 500:
        for i, char in enumerate(answer[500:]):
            if char == ' ':
                answer = answer[:i+499] + '...'
                break

    return f"{wiki_url}:\n{answer}"
