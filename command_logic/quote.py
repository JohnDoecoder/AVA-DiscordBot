from bs4 import BeautifulSoup as soup
import urllib.request as ul
from helpers import html


def get_quote(url):
    # Fetch site
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    # Get quotes from site
    pagesoup = soup(htmldata, "html.parser")
    raw_quote = pagesoup.findAll('span', {"class": "quote"})[0]
    raw_author = pagesoup.findAll('a', {"class": "quote-btn"})[0]

    # Clean text from <, >, href...
    quote = html.clean_text(str(raw_quote))
    author = html.clean_text(str(raw_author))

    return [quote, author]
