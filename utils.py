import re
from flask import session, redirect
import string
import random

sort_parameters = {'update_date': ['+Дате+обновления', 'UPDATE_DATE'], 'place_date': [
    '+Дате+размещения', 'PUBLISH_DATE'], 'price': ['+Цене', 'PRICE']}


def check_email(mail: str) -> bool:
    return re.match(r'\w+@\w+\.\w{1,10}', mail)


def geherate_key() -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(32))
