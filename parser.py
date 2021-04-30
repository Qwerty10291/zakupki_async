import requests
from lxml.html import document_fromstring
import logging
import re
import multiprocessing as mp
import time
import json


class Parser:
    def __init__(self, search_string, logger, tags: dict, pipe, processes=2, timeout=0.1):
        # получаем логгер
        self.logger = logger

        # устанавливаем канал связи с главным процессом
        self.pipe = pipe

        # задаем константы
        self.search_string = search_string
        self.processes = processes
        self.parse_link = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html'
        self.main_link = 'https://zakupki.gov.ru'
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0', }
        self.init_parser()

        # создаем теги для запроса
        self.tags = tags
        self.tags['searchString'] = search_string
        self.tags['pageNumber'] = '1'
        self.tags['morphology'] = 'on'
        self.tags['sortDirection'] = 'false'
        self.tags['recordsPerPage'] = '_500'
        self.tags['sortBy'] = 'UPDATE_DATE'
        self.tags['fz44'] = 'on'

    def init_parser(self):
        self.session.get('https://zakupki.gov.ru/')
        self.logger.info('Парсер инициализирован')

    def start_async(self):
        process = mp.Process(target=self.async_parser)
        process.start()
        self.process = process
        return process

    def async_parser(self):
        links = self.get_links_to_parse()
        self.parse_all(links)

    def get_links_to_parse(self) -> list:
        tags = self.tags
        data = self.session.get(
            'https://zakupki.gov.ru/epz/order/extendedsearch/results.html', params=tags)
        data.raise_for_status()

        links = []
        # получаем количество страниц
        page_num = int(document_fromstring(data.text).xpath(
            '//ul[@class="pages"]/li[last()]/a/span/text()')[0])
        for i in range(1, page_num + 1):
            self.logger.info(f'получениие ссылок: {i}')
            page_data = self.session.get(self.parse_link, params=tags)
            page_data.raise_for_status()
            links += list(map(lambda x: self.main_link + x, document_fromstring(
                page_data.text).xpath('//div[@class="registry-entry__header-mid__number"]/a/@href')))
            tags['pageNumber'] = str(i)
            self.logger.info(f"загрузка ссылок. Страница {tags}")
        return links

    def parse_all(self, links):
        for link in links:
            self.pipe.send(self.parse_ea44(link))
            time.sleep(self.timeout)
        self.pipe.send('end')

    def parse_ea44(self, link):
        inform_request = self.session.get(link)
        inform_request.raise_for_status()

        order_document = document_fromstring(inform_request.text)

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
        condition_container = self._get_cotract_conditions_container(
            order_document.xpath('//div[@id="custReqNoticeTable"]/div'))
        if condition_container:
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
        tender_object_info = self._parse_tender_object_info(order_document)

        # парсинг ссылок документов
        term_document_link = link.replace('common-info', 'documents')
        term_document_data = self.session.get(term_document_link)
        term_document_data.raise_for_status()
        term_document_links = document_fromstring(term_document_data.text).xpath(
            '//span[@class="section__value"]/a[@title]/@href')
        
        # парсинг победителя
        winner = self._parse_tender_winner(link)
        if not winner:
            winner = ['', '', '']

        return {
            'tender_id': tender_id, 'tender_object': tender_object, 'customer': customer,
            'tender_price': tender_price, tender_date: 'tender_date', 'tender_adress': tender_adress, 'tender_delivery': tender_delivery_adress,
            'tender_term': tender_term, 'tender_object_info': tender_object_info, 'tender_winner': winner, 'document_links': term_document_links,
            'type': 'fz44', 'link': link
        }

    def _parse_tender_object_info(self, document):
        # получаем контейнер таблицы
        table = document.xpath(
            '//div[@id]/table[@class="blockInfo__table tableBlock"]')
        if not table:
            return json.dumps([])
        else:
            table = table[0]

        # получаем и обрабатываем заголовки
        headers_raw = table.xpath('./thead/tr[1]/th/text()')
        headers = list(map(self._normalizer, headers_raw))

        # данные таблицы
        data = [list(map(self._normalizer, row.xpath('./t/td/text()')))
                for row in table.xpath('./tbody/tr[@class="tableBlock__body"]')]

        return data
    
    def _parse_tender_winner(self, tender_link):
        winner_link = tender_link.replace('common-info', 'supplier-results')
        data = requests.get(winner_link)
        data.raise_for_status()

        doc = document_fromstring(data.text)
        table = doc.xpath('//div[contains(@id, "participant")]/table')
        winner = list(map(self._normalizer, table.xpath('./tbody/tr[1]/td/text()')))
        return winner


    def _get_cotract_conditions_container(self, containers):
        for element in containers:
            name = element.xpath('.//h2')[0].text_content()
            print(self._normalizer(name))
            if 'Условия' in self._normalizer(name):
                return element
        return False

    def _normalizer(self, text: str) -> str:
        return text.replace('\n', '').replace('\xa0', '').strip()
