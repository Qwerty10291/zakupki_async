import asyncio
from typing import List

import aiohttp
from aiohttp import ClientConnectionError
from aiohttp.client import ClientSession
from aiohttp_proxy import ProxyConnector, ProxyType

from lxml.html import document_fromstring
import re

from sqlalchemy.sql.functions import user
from data.db_session import create_session, global_init
from data.models import History, Data, Objects, TenderLinks, Winners
from datetime import datetime


class AsyncParser:
    def __init__(self, history: History, tags: dict, workers: int, on_done, connector=False) -> None:
        self.workers = workers
        self.on_done = on_done

        self.params = {'morphology': 'on',
                       'search-filter': 'Дате+размещения',
                       'sortDirection': 'false',
                       'recordsPerPage': '_10',
                       'showLotsInfoHidden': 'false',
                       'sortBy': 'UPDATE_DATE',
                       'fz44': 'on',
                       'pc': 'on',
                       'currencyIdGeneral': '-1'}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0',
        }

        self.search_link = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html'
        self.main_link = 'https://zakupki.gov.ru'
        self.tags = tags
        self.params.update(self.tags)
        self.history = history

        self.is_proxy = False
        self.proxy_data = ''

        self.db_session = create_session()
        self.db_session.add(history)

    def start(self):
        loop = asyncio.new_event_loop()
        loop.run_in_executor(None, self.init_parser)

    def init_parser(self):
        asyncio.run(self.parse())

    async def parse(self):
        self._change_history_state('searching')
        if self.is_proxy:
            proxy = await self.create_proxy_connection(self.proxy_data)
            async with aiohttp.ClientSession(headers=self.headers, connector=proxy) as session:
                print('init')
                try:
                    pages_count = await self.get_pages_count(session)
                    pages_tasks = [self.parse_page(session, i)
                                for i in range(1, pages_count + 1)]
                    tenders_links = await asyncio.gather(*pages_tasks)
                    self.history.tenders_count = sum(map(len, tenders_links))
                    print('ссылки загружены', self.history.tenders_count)
                    self._change_history_state('downloading')

                    for i in range(self.workers, len(tenders_links), self.workers):
                        print(f'page: {i - self.workers + 1}-{i + 1}')
                        tasks = [self.parse_tender_page(
                            session, page) for page in tenders_links[i - self.workers:i]]
                        tenders = await asyncio.gather(*tasks, return_exceptions=False)
                        for tender_page in tenders:
                            for tender in tender_page:
                                self.history.tenders.append(tender)
                        self.db_session.commit()

                    if len(tenders_links) % self.workers != 0:
                        tasks = [self.parse_tender_page(session, page) for page in tenders_links[len(
                            tenders_links) - len(tenders_links) % self.workers:]]
                        tenders = await asyncio.gather(*tasks, return_exceptions=False)
                        for tender_page in tenders:
                            for tender in tender_page:
                                self.history.tenders.append(tender)
                        self.db_session.commit()

                    self._change_history_state('done')
                    self.on_done(self.history.id)
                except Exception as msg:
                    print(msg)
        else:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                print('init')
                pages_count = await self.get_pages_count(session)
                pages_tasks = [self.parse_page(session, i)
                            for i in range(1, int(pages_count / 10) + 2)]
                tenders_links = await asyncio.gather(*pages_tasks)
                self.history.tenders_count = sum(map(len, tenders_links))
                print('ссылки загружены', self.history.tenders_count)
                self._change_history_state('downloading')

                for i in range(self.workers, len(tenders_links), self.workers):
                    print(f'page: {i - self.workers + 1}-{i + 1}')
                    tasks = [self.parse_tender_page(
                        session, page) for page in tenders_links[i - self.workers:i]]
                    tenders = await asyncio.gather(*tasks, return_exceptions=False)
                    for tender_page in tenders:
                        for tender in tender_page:
                            self.history.tenders.append(tender)
                    self.db_session.commit()

                if len(tenders_links) % self.workers != 0:
                    tasks = [self.parse_tender_page(session, page) for page in tenders_links[len(
                        tenders_links) - len(tenders_links) % self.workers:]]
                    tenders = await asyncio.gather(*tasks, return_exceptions=False)
                    for tender_page in tenders:
                        for tender in tender_page:
                            self.history.tenders.append(tender)
                    self.db_session.commit()

                self._change_history_state('done')
                self.on_done(self.history.id)

    async def get_pages_count(self, session: aiohttp.ClientSession) -> int:
        """ возвращает количество страниц с записями о тендерах """
        data = await self._get_request(session, self.search_link, self.params)
        doc = document_fromstring(data)
        pages_count = int(
            doc.xpath('//ul[@class="pages"]/li[last()]/a/span/text()')[0])
        return pages_count

    async def parse_page(self, session: aiohttp.ClientSession, page_num: int) -> List[Data]:
        """ парсит отдельную страницу вытаскивая id и ссылку на закупку """

        param = self.params.copy()
        param['pageNumber'] = page_num
        orders = []

        data = await self._get_request(session, self.search_link, params=param)
        doc = document_fromstring(data)
        for link in doc.xpath('//div[@class="registry-entry__header-mid__number"]/a'):
            order_id = self._tender_id_handler(
                self._normalizer(link.xpath('./text()')[0]))
            order_link = self.main_link + link.xpath('./@href')[0]
            tender = Data()
            tender.id = order_id
            tender.tender_link = order_link
            orders.append(tender)
        return orders

    async def parse_tender_page(self, session: aiohttp.ClientSession, orders: list) -> List[Data]:
        """ парсит данные одной стрпницы записей закупок """
        out = []
        for order in orders:
            out.append(await self.parse_ea44(session, order))
            await asyncio.sleep(1)
        return out

    async def parse_ea44(self, session: aiohttp.ClientSession, order: Data) -> Data:
        """ парсит данные одной закупки """

        # проверка на наличие записи в базе
        data = self.db_session.query(Data).filter(Data.id == order.id).all()
        if data:
            return data[0]

        text = await self._get_request(session, order.tender_link)

        order_document = document_fromstring(text)
        # парсим главную информацию о закупке - номер цена заказчик дата

        card_info_container = order_document.cssselect('.cardMainInfo')[0]
        tender_id = card_info_container.cssselect(
            '.cardMainInfo__purchaseLink')

        if not tender_id:
            tender_id = ''
        else:
            tender_id = self._normalizer(tender_id[0].text_content())

        tender_object = card_info_container.xpath(
            './div[1]/div[2]/div[1]/span[2]')
        if not tender_object:
            tender_object = ''
        else:
            tender_object = self._normalizer(tender_object[0].text_content())

        customer = card_info_container.xpath('./div[1]/div[2]/div[2]/span[2]')
        if not customer:
            customer = ''
        else:
            customer = self._normalizer(customer[0].text_content())

        tender_price = card_info_container.cssselect('.cost')
        if not tender_price:
            tender_price = ''
        else:
            tender_price = self._normalizer(tender_price[0].text_content())

        tender_date = card_info_container.xpath(
            './div[2]/div[2]/div[1]/div[1]/span[2]')
        if not tender_date:
            tender_date = ''
        else:
            tender_date = self._normalizer(tender_date[0].text_content())

        # общая информация о закупке - адресс электронной площадки и обьект закупки
        general_information_container = order_document.xpath(
            '//div[@class="wrapper"]/div[2]')

        tender_adress = general_information_container[0].xpath(
            './/div[@class="col"]/section[3]/span[2]')
        if not tender_adress:
            tender_adress = ''
        else:
            tender_adress = self._normalizer(tender_adress[0].text_content())

        # условия контракта
        condition_container = self.get_cotract_conditions_container(
            order_document.xpath('//div[@id="custReqNoticeTable"]/div'))
        if condition_container is not None:
            tender_delivery_adress = condition_container.xpath(
                './/div[@class="col"]/section[2]/span[2]')
            if not tender_delivery_adress:
                tender_delivery_adress = ''
            else:
                tender_delivery_adress = self._normalizer(
                    tender_delivery_adress[0].text_content())

            tender_term = condition_container.xpath(
                './/div[@class="row"]/section[3]/span[2]')
            if not tender_term:
                tender_term = ''
            else:
                tender_term = self._normalizer(tender_term[0].text_content())
        else:
            tender_delivery_adress = ''
            tender_term = ''

        # парсинг информации о обьекте закупки
        tender_object_info = self.parse_tender_object_info(order_document)

        # парсинг победителя
        try:
            winner = await self.parse_tender_winner(session, order.tender_link)
        except Exception:
            winner = []
        if len(winner) < 3:
            winner = ['', '', '']

        # парсинг ссылок документов
        term_document_link = order.tender_link.replace(
            'common-info', 'documents')
        term_document_data = await self._get_request(session, term_document_link)
        term_document_links = document_fromstring(term_document_data).xpath(
            '//span[@class="section__value"]/a[@title]/@href')
        order.tender_object = tender_object
        order.customer = customer
        order.tender_price = self._tender_price_handler(tender_price)
        order.tender_date = self._tender_date_handler(tender_date)
        order.tender_adress = tender_adress
        order.tender_delivery = tender_delivery_adress
        order.tender_term = tender_term
        for object_info in self._handle_tender_objects(tender_object_info):
            order.objects.append(object_info)
        for document_link_data in term_document_links:
            tender_link = TenderLinks()
            tender_link.link = document_link_data
            tender_link.data_id = order.id
            order.document_links.append(tender_link)
        order.winner.append(
            Winners(name=winner[0], position=winner[1], price=winner[2]))
        order.type = 'fz44'
        return order

    def get_cotract_conditions_container(self, containers):
        for element in containers:
            name = element.xpath('.//h2')
            if name:
                name = name[0].text_content()
            else:
                continue
            if 'Условия' in self._normalizer(name):
                return element
        return None

    def parse_tender_object_info(self, document) -> List[List[str]]:
        # получаем контейнер таблицы
        table = document.xpath(
            '//div[@id="positionKTRU"]//table')
        if not table:
            return []
        else:
            table = table[0]

        # получаем и обрабатываем заголовки
        headers_raw = table.xpath('./thead/tr[1]/th/text()')
        headers = list(map(self._normalizer, headers_raw))

        # данные таблицы
        data_raw = [row.xpath('./td[contains(@class, "tableBlock__col")]/text()')
                    for row in table.xpath('./tbody/tr')]
        data = [list(map(self._normalizer, i)) for i in data_raw]

        return [headers] + data

    async def parse_tender_winner(self, session: aiohttp.ClientSession, tender_link):
        winner_link = tender_link.replace('common-info', 'supplier-results')
        data = await self._get_request(session, winner_link)
        doc = document_fromstring(await data.text())
        table = doc.xpath('//div[contains(@id, "participant")]/table')
        if table:
            winner = table[0].xpath('./tbody/tr[1]/td/text()')
        else:
            return ['', '', '']
        return list(map(self._normalizer, winner))

    async def _get_request(self, session: aiohttp.ClientSession, url, params={}, retries=0) -> str:
        try:
            async with session.get(url, allow_redirects=True, params=params) as query:
                if query.status != 200:
                    print(f'try: {retries}')
                    if query.status == 503:
                        if retries > 10:
                            raise ClientConnectionError(
                                'Слишком много неудачных попыток')
                        await asyncio.sleep(retries + 1)
                        return await self._get_request(session, url, params, retries=retries + 1)
                    elif query.status == 404:
                        raise ClientConnectionError(
                            f'Страница: {url} не найдена')
                    else:
                        return ClientConnectionError(f'{url}: code {query.status}')
                return await query.text()
        except aiohttp.ServerDisconnectedError:
            await asyncio.sleep(1)
            print(f'tryd: {retries}')
            if retries > 10:
                raise ClientConnectionError(
                                'Слишком много неудачных попыток')
            return await self._get_request(session, url, params, retries=retries + 1)
    
    async def create_proxy_connection(self, data: str):
        host, port, login, password = data.split(';')
        return ProxyConnector(proxy_type=ProxyType.HTTPS, host=host, port=int(port), username=login, password=password)

    def _normalizer(self, text: str) -> str:
        return text.replace('\n', '').replace('\xa0', '').strip()

    def _tender_id_handler(self, tender_id: str) -> int:
        return int(re.findall(r'\d+', tender_id)[0])

    def _change_history_state(self, state: str) -> None:
        self.history.state = state
        self.db_session.commit()

    def _tender_price_handler(self, tender_price: str) -> float:
        tender_price = tender_price.replace(' ', '').replace(',', '.')
        return float(re.findall(r'[\d\,]+', tender_price)[0])

    def _tender_date_handler(self, tender_date: str):
        return datetime.strptime(tender_date, '%d.%m.%Y')

    def _handle_tender_objects(self, objects: list) -> List[Objects]:
        tender_objects = []
        for i in objects[1:]:
            if len(i) == 6:
                data = Objects()
                data.position = i[0]
                data.name = i[1]
                data.unit = i[2]
                data.quantity = i[3]
                data.unit_price = i[4]
                data.price = i[5]
                tender_objects.append(data)
        return tender_objects
    


class AsyncParserController:
    def __init__(self, workers: int, pages_per_iter: int) -> None:
        """
        :param int workers: максимальное количество запущенных парсеров
        :param int pages_per_iter: количество загружаемых парсером страниц за одну итерацию цикла
        """
        self.is_proxy = False
        self.check_proxies()
        self.workers = workers
        self.pages_per_iter = pages_per_iter
        self.running = 0
        self.queue: List[AsyncParser] = []
        self.parsers: List[AsyncParser] = []

    def create_parser(self, user_id, parameters):
        session = create_session()
        if len(self.parsers) > self.workers:
            history = self._create_history(user_id, 'queue', parameters)
            session.add(history)
            session.commit()
            session.expunge(history)
            parser = AsyncParser(history, parameters,
                                 self.pages_per_iter, self.remove_parser)
            self.queue.append(parser)
        else:
            history = self._create_history(user_id, 'started', parameters)
            session.add(history)
            session.commit()
            session.expunge(history)
            parser = AsyncParser(history, parameters,
                                 self.pages_per_iter, self.remove_parser)
            self.start_parser(parser)
            self.parsers.append(parser)

    def start_parser(self, parser: AsyncParser):
        print(self.is_proxy)
        if self.is_proxy:
            proxy = min(self.proxies.items(), key=lambda x: x[1])
            if proxy[0] == 'self':
                self.proxies['self'] += 1
                print('proxy: self')
                parser.is_proxy = False
                parser.start()
            else:
                self.proxies[proxy[0]] += 1
                print('proxy:', proxy[0])
                parser.is_proxy = True
                parser.proxy_data = proxy[0]
                parser.start()
        else:
            parser.is_proxy = False
            parser.start()



    def move_queue(self):
        print('move')
        if len(self.queue) > 0:
            parser = self.queue.pop(0)
            self.start_parser(parser)
            self.parsers.append(parser)

    def remove_parser(self, history_id: int):
        print('removed', history_id)
        for i in range(len(self.parsers)):
            if self.parsers[i].history.id == history_id:
                del self.parsers[i]
                self.move_queue()
                break

    def check_proxies(self, filename='proxies.txt'):
        """ проверяет наличие файла proxies.txt и прокси в нем """
        data = [proxy.replace('\n', '')
                for proxy in open(filename, 'r').readlines()]
        if data:
            self.is_proxy = True
            self.proxy_count = len(data)
            self.proxies = dict((proxy, 0) for proxy in data)
            self.proxies['self'] = -1
    

    def _create_history(self, user_id: int, state: str, parameters: dict):
        history = History()
        history.user_id = user_id
        history.tag = parameters.get('searchString')
        history.state = state
        if 'priceFromGeneral' in parameters:
            history.min_price = int(parameters['priceFromGeneral'])
        if 'priceToGeneral' in parameters:
            history.max_price = int(parameters['priceToGeneral'])
        if 'publishDateFrom' in parameters:
            history.date_from = datetime.strptime(
                parameters['publishDateFrom'], '%d.%m.%Y')
        if 'publishDateTo' in parameters:
            history.date_to = datetime.strptime(
                parameters['publishDateTo'], '%d.%m.%Y')
        history.sort_filter = parameters['search-filter']
        if parameters['sortDirection'] == 'false':
            history.sort_direction = False
        else:
            history.sort_direction = True
        return history
