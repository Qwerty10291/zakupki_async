import re


def check_email(mail:str) -> bool:
    return re.match(r'\w+@\w+\.\w{1,10}', mail)