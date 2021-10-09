import urllib.request as ul
from bs4 import BeautifulSoup as soup
from helpers import html


def bored(ctx, url):
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    pagesoup = soup(htmldata, "html.parser")
    raw_idea = pagesoup.findAll('p', {"class": "lead text-dark"})

    return html.clean_text((str(raw_idea[0])).replace('\\', ''))
