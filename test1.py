import asyncio
import aiohttp
from lxml.html import document_fromstring
import datetime

main_link = 'https://hentai-chan.pro'


async def main(pages_count):
    async with aiohttp.ClientSession() as session:
        pages = await get_pages(session, pages_count)
        tasks = [parse_page(session, page) for page in pages]
        print(await asyncio.gather(*tasks))


async def get_pages(session: aiohttp.ClientSession, count: int):
    tasks = [get_page(session, i) for i in range(1, count + 1)]
    return await asyncio.gather(*tasks)


async def get_page(session: aiohttp.ClientSession, num: int):
    async with session.get(f'{main_link}/tags/bdsm?offset={num * 20}') as page:
        doc = document_fromstring(await page.text())
        return doc.xpath('//a[@class="title_link"]/@href')


async def parse_page(session: aiohttp.ClientSession, page):
    tasks = [parse_title(session, main_link + link) for link in page]
    return await asyncio.gather(*tasks)


async def parse_title(session: aiohttp.ClientSession, link):
    async with session.get(link) as data:
        doc = document_fromstring(await data.text())
        return doc.xpath('//a[@class="title_top_a"]/text()')[0]

start = datetime.datetime.now()
asyncio.run(main())
stop = datetime.datetime.now() - start
print(stop.seconds)
