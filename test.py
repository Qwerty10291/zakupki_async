from db_additions import register_user
from data import db_session
db_session.global_init('db/db.sqlite')

for i in range(20):
    register_user(f'test{i}', f'test{i}', f'test{i}@test.ru', f'test{i}')