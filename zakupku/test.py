import requests
from lxml import etree
headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
           'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0',}
link = 'https://zakupki.gov.ru/epz/order/notice/printForm/viewXml.html?regNumber=0320100007621000014'
print(requests.get(link, headers=headers).text, file=open('44.xml', 'w'))