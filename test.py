import requests

proxy = {'https': 'socks5://D39kgB:SakU2s@176.124.45.90:8000'}
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'}
print(requests.get('https://zakupki.gov.ru/', proxies=proxy).text)