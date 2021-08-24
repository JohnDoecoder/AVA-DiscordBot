import urllib.request as ul
from bs4 import BeautifulSoup as soup
from helpers import html


def get_wiki(url, search: str):
    # No blanks in urls
    search = search.replace(' ', '_')

    # Fetch site
    req = ul.Request(f"{url}/wiki/{search}", headers={'User-Agent': 'Mozilla/5.0'})

    # Check if entry exists
    try:
        with ul.urlopen(req) as client:
            htmldata = client.read()
    except:  # Not clean, I know
        return f"{url}/w/index.php?search={search}"

    # Get site
    pagesoup = soup(htmldata, "html.parser")
    description = pagesoup.findAll('div', {"class": "mw-parser-output"}, limit=1)[0]

    # Get description from html
    passage = False
    answer = ''
    for word in str(description).split():
        if not passage and '<p' in word:
            passage = True

        if passage and 'div' in word:
            break

        if passage:
            answer += ' ' + word + ''

    # Clean up text from html fragments
    answer.replace('<br>', '\n')
    answer.replace('<br/>', '\n')
    answer = html.clean_text(answer)

    # Shorten text
    if len(answer) > 500:
        answer = answer[:500] + '...'

    return f"{url}/wiki/{search}:\n{answer}"
