from bs4 import BeautifulSoup as soup
import urllib.request as ul
from helpers import html


def get_verse(url):
    # Fetch site
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    # Get verse from site
    pagesoup = soup(htmldata, "html.parser")
    raw_verse = pagesoup.findAll('span', {"class": "v1"})[0]
    source = pagesoup.findAll('a', {"class": "vc"})[0]

    # Clean text from <, >, href...
    verse = html.clean_text(str(raw_verse))
    source = html.clean_text(str(source))

    return [verse, source]
