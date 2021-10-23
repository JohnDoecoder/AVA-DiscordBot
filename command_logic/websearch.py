import urllib.request as ul
from bs4 import BeautifulSoup as soup
from helpers import html
from random import randint
import re


async def search(searchterm: str):
    # Fetch site
    url = f'https://html.duckduckgo.com/html/?q={searchterm}'.replace(' ', '+')
    req = ul.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with ul.urlopen(req) as client:
        htmldata = client.read()

    # Get results from site
    pagesoup = soup(htmldata, "html.parser")
    raw_results = pagesoup.findAll('div', {"class": "results_links"}, limit=3)

    results = {}
    for result in raw_results:
        link = result.find_next('a', {"class": "result__a"}).text
        results[link] = {}
        d_link = result.find_next('a', {"class": "result__snippet"})['href'].replace(r'//duckduckgo.com/l/?uddg=', '').replace(r'%3A', ':').replace(r'%2F', '/')
        results[link]['link'] = re.sub(r"rut=.*", "", d_link).replace('%2D', ' ').replace('&', '').replace(' ', '-')
        results[link]['text'] = result.find_next('a', {"class": "result__snippet"}).text

    return results
