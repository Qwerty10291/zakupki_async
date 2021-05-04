import asyncio
from typing import List
import aiohttp
from aiohttp import ClientConnectionError
from lxml.html import document_fromstring
from copy import deepcopy
import re
import random
import requests

from requests.models import requote_uri

main_link = 'https://zakupki.gov.ru'
parse_link = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html'
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'}
params = {'morphology': 'on',
          'search-filter': 'Дате+размещения',
          'sortDirection': 'false',
          'recordsPerPage': '_50',
          'showLotsInfoHidden': 'false',
          'sortBy': 'UPDATE_DATE',
          'fz44': 'on',
          'pc': 'on',
          'currencyIdGeneral': '-1'}

workers = 5


class Order:
    def __init__(self, id, link) -> None:
        self.id = id
        self.link = link

    def __str__(self) -> str:
        return f'{self.id}: {self.link}'

    def __repr__(self) -> str:
        return f'{self.id}: {self.link}'


async def main():
    data = []
    async with aiohttp.ClientSession(headers=headers) as session:
        orders_links = await get_pages(session)
        for i in range(workers, len(orders_links) + 1, workers):
            print(f'pages: {i - workers + 1}-{i + 1}')
            tasks = [parse_tender_page(session, page)
                     for page in orders_links[i - workers:i]]
            pages = await asyncio.gather(*tasks)
            data += pages
        if len(orders_links) % workers != 0:
            print(f'pages: {len(orders_links) - len(orders_links) % workers}-{len(orders_links)}')
            tasks = [parse_tender_page(session, page) for page in orders_links[len(
                orders_links) - len(orders_links) % workers:]]
            pages = await asyncio.gather(*tasks)
            data += pages
    return data


async def get_pages(session: aiohttp.ClientSession):
    data = []
    async with session.get(parse_link, params=params) as data:
        doc = document_fromstring(await data.text())
        pages_count = int(
            doc.xpath('//ul[@class="pages"]/li[last()]/a/span/text()')[0])
        print(pages_count)
    tasks = [parse_page(session, i) for i in range(1, pages_count + 1)]
    return await asyncio.gather(*tasks)


async def parse_page(session: aiohttp.ClientSession, page_num: int) -> List[Order]:
    param = deepcopy(params)
    param['pageNumber'] = page_num
    orders = []
    async with session.get(parse_link, params=param) as data:
        doc = document_fromstring(await data.text())
        for link in doc.xpath('//div[@class="registry-entry__header-mid__number"]/a'):
            order_id = normalizer(link.xpath('./text()')[0])
            order_link = main_link + link.xpath('./@href')[0]
            orders.append(Order(order_id, order_link))
    return orders


async def parse_tender_page(session: aiohttp.ClientSession, orders: List[Order]) -> List[Order]:
    out = []
    for order in orders:
        out.append(await parse_ea44(session, order))
        await asyncio.sleep(1)
    return out


async def get_request(session: aiohttp.ClientSession, url, params={}, retries=0):
    try:
        async with session.get(url, allow_redirects=True, params=params) as query:
            if query.status != 200:
                if query.status == 503:
                    if retries > 10:
                        raise ClientConnectionError(
                            'Слишком много неудачных попыток')
                    await asyncio.sleep(retries + 2)
                    return await get_request(session, url, params, retries=retries + 1)
                elif query.status == 404:
                    raise ClientConnectionError(f'Страница: {url} не найдена')
            return await query.text()
    except aiohttp.ServerDisconnectedError:
        await asyncio.sleep(5)
        return await get_request(session, url, params)


async def parse_ea44(session: aiohttp.ClientSession, order: Order):
    text = await get_request(session, order.link)

    order_document = document_fromstring(text)
    # парсим главную информацию о закупке - номер цена заказчик дата

    card_info_container = order_document.cssselect('.cardMainInfo')[0]
    print('passed')
    tender_id = card_info_container.cssselect(
        '.cardMainInfo__purchaseLink')

    if not tender_id:
        tender_id = ''
    else:
        tender_id = normalizer(tender_id[0].text_content())

    tender_object = card_info_container.xpath(
        './div[1]/div[2]/div[1]/span[2]')
    if not tender_object:
        tender_object = ''
    else:
        tender_object = normalizer(tender_object[0].text_content())

    customer = card_info_container.xpath('./div[1]/div[2]/div[2]/span[2]')
    if not customer:
        customer = ''
    else:
        customer = normalizer(customer[0].text_content())

    tender_price = card_info_container.cssselect('.cost')
    if not tender_price:
        tender_price = ''
    else:
        tender_price = normalizer(tender_price[0].text_content())

    tender_date = card_info_container.xpath(
        './div[2]/div[2]/div[1]/div[1]/span[2]')
    if not tender_date:
        tender_date = ''
    else:
        tender_date = normalizer(tender_date[0].text_content())

    # общая информация о закупке - адресс электронной площадки и обьект закупки
    general_information_container = order_document.xpath(
        '//div[@class="wrapper"]/div[2]')

    tender_adress = general_information_container[0].xpath(
        './/div[@class="col"]/section[3]/span[2]')
    if not tender_adress:
        tender_adress = ''
    else:
        tender_adress = normalizer(tender_adress[0].text_content())

    # условия контракта
    condition_container = get_cotract_conditions_container(
        order_document.xpath('//div[@id="custReqNoticeTable"]/div'))
    if condition_container is not None:
        tender_delivery_adress = condition_container.xpath(
            './/div[@class="col"]/section[2]/span[2]')
        if not tender_delivery_adress:
            tender_delivery_adress = ''
        else:
            tender_delivery_adress = normalizer(
                tender_delivery_adress[0].text_content())

        tender_term = condition_container.xpath(
            './/div[@class="row"]/section[3]/span[2]')
        if not tender_term:
            tender_term = ''
        else:
            tender_term = normalizer(tender_term[0].text_content())
    else:
        tender_delivery_adress = ''
        tender_term = ''

    # парсинг информации о обьекте закупки
    tender_object_info = parse_tender_object_info(order_document)

    # парсинг победителя
    try:
        winner = await parse_tender_winner(session, order.link)
    except Exception:
        winner = []
    if len(winner) < 3:
        winner = ['', '', '']

    # парсинг ссылок документов
    term_document_link = order.link.replace('common-info', 'documents')
    term_document_data = await get_request(session, term_document_link)
    term_document_links = document_fromstring(term_document_data).xpath(
        '//span[@class="section__value"]/a[@title]/@href')

    order.tender_object = tender_object
    order.customer = customer
    order.tender_price = tender_price
    order.tender_date = tender_date
    order.tender_adress = tender_adress
    order.tender_delivery = tender_delivery_adress
    order.tender_term = tender_term
    order.tender_object_info = tender_object_info
    order.document_links = term_document_links
    order.winner = winner
    order.type = 'fz44'
    return order


def normalizer(text: str) -> str:
    return re.sub(r'\W+', ' ', text).strip()


def get_cotract_conditions_container(containers):
    for element in containers:
        name = element.xpath('.//h2')
        if name:
            name = name[0].text_content()
        else:
            continue
        if 'Условия' in normalizer(name):
            return element
    return None


def parse_tender_object_info(document):
    # получаем контейнер таблицы
    table = document.xpath(
        '//div[@id="positionKTRU"]//table')
    if not table:
        return []
    else:
        table = table[0]

    # получаем и обрабатываем заголовки
    headers_raw = table.xpath('./thead/tr[1]/th/text()')
    headers = list(map(normalizer, headers_raw))

    # данные таблицы
    data_raw = [row.xpath('./td[contains(@class, "tableBlock__col")]/text()')
                for row in table.xpath('./tbody/tr')]
    data = [list(map(normalizer, i)) for i in data_raw]

    return [headers] + data


async def parse_tender_winner(session: aiohttp.ClientSession, tender_link):
    winner_link = tender_link.replace('common-info', 'supplier-results')
    data = await get_request(session, winner_link)
    doc = document_fromstring(await data.text())
    table = doc.xpath('//div[contains(@id, "participant")]/table')
    if table:
        winner = table[0].xpath('./tbody/tr[1]/td/text()')
    else:
        return ['', '', '']
    return list(map(normalizer, winner))



data = asyncio.run(main())
