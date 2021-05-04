from data.models import *
from data.db_session import *

global_init('1')
session = create_session()

data = session.query(History).all()
for user in data:
    if len(user.tenders) > 0:
        for i in user.tenders:
            print(i.objects)