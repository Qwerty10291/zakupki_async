from flask.globals import session
from data import db_session
from data.models import *
db_session.global_init('1')
session = db_session.create_session()
for i in session.query(User).all():
    print(i.name)