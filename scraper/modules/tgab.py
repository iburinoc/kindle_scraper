import asyncio
import aiohttp
import bs4
import dateutil.parser

import scraper.util

BASEURL = "https://tiraas.net/"

TITLE = "The Gods are Bastards"
AUTHOR = "D.D. Webb"

async def _scrape_index(session):
    async with session.get(BASEURL + "table-of-contents/", timeout=60) as resp:
        text = await resp.text()
        soup = bs4.BeautifulSoup(text, features="lxml")
        entries = soup.find("div", class_="entry-content")
        hrefs = entries.find_all("a", class_="")
        return [h.attrs["href"] for h in hrefs]

async def _scrape_chapter(session, url):
    async with session.get(url) as resp:
        text = await resp.text()
        soup = bs4.BeautifulSoup(text, features="lxml")
        title = (soup
                .find("h1", class_="entry-title")
                .encode_contents(formatter="html")
                .decode("utf-8"))
        datestr = (soup
                .find("time", class_="entry-date")
                .attrs["datetime"])
        date = dateutil.parser.parse(datestr)
        paragraphs = (soup
                .find("div", "entry-content")
                .find_all("p", recursive=False)[1:-1])
        content = '\n'.join(
                p.prettify(formatter="html") for p in paragraphs)

        return (title, date, content)

async def _get_all():
    async with aiohttp.ClientSession() as session:
        print(f"Getting index")
        chaps = await _scrape_index(session)
        print(f"Downloading {len(chaps)} chapters")
        chaps = await asyncio.gather(*(_scrape_chapter(session, url) for url in chaps))
        chaps = sorted(chaps, key=lambda x: x[1])


        print(f"Combining {len(chaps)} chapters")
        return scraper.util.format_ebook(
                TITLE,
                AUTHOR,
                [(title, content) for (title, date, content) in chaps])

def scrape_ebook():
    return asyncio.run(_get_all())
