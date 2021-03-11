from data import db_session
from data.models import Data, Winners
from datetime import datetime

db_session.global_init('db/db.sqlite')
session = db_session.create_session()

data = Data()
data.id = 1
data.type = 'fz 44'
data.tender_price = 1.2
data.tender_date = datetime.now()
data.tender_object = 'qwd'
data.customer = 'qwdqw'
data.tender_adress = ''
data.tender_delivery = ''
data.tender_terms = ''
data.tender_object_info = ''
data.document_links = ''
data.tender_link = ''

winner = Winners()
winner.data_id = 1
winner.name = ''
winner.position = ''
winner.price = ''

data.winner.append(winner)
session.add(data)
session.commit()