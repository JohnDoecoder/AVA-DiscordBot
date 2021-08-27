from bs4 import BeautifulSoup as soup
import urllib.request as ul
from helpers import html
import re


def get_quote(url):
    # Fetch site
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    # Get quotes from site
    pagesoup = soup(htmldata, "html.parser")
    raw_quote = pagesoup.findAll('span', {"class": "quote"}, limit=1)
    raw_author = pagesoup.findAll('a', {"class": "quote-btn"}, limit=1)
    raw_image = pagesoup.findAll('img', {"class": "quote-pp"}, limit=1)

    # get image url
    raw_image_url = re.findall('src=\"\/[a-z|\-|0-9|\.]+\"', str(raw_image))
    image_url = 'http://zitate.net' + raw_image_url[0][5:-1]

    # Clean text from <, >, href...
    quote = html.clean_text(str(raw_quote[0]))
    author = html.clean_text(str(raw_author[0]))

    return {'quote': quote, 'author': author, 'image': image_url}
