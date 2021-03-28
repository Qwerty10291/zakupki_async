from flask.globals import session
from sqlalchemy.orm import query
from sqlalchemy.sql.expression import true
from data import db_session
from data.models import Applications, Data, User, Auth, History
from paginate_sqlalchemy import SqlalchemyOrmPage
from utils import geherate_key


def get_user(id) -> User:
    session = db_session.create_session()
    data = session.query(User).get(id)
    session.close()
    return data


def check_user(id) -> bool:
    session = db_session.create_session()
    data = bool(session.query(User).filter(User.id == id).count())
    session.close()
    return data


def get_history(id):
    session = db_session.create_session()
    history = session.query(History).filter(History.id == id)
    session.close()
    if history:
        return history[0]
    else:
        return None


def load_histories(user_id) -> list:
    session = db_session.create_session()
    histories = session.query(History).filter(History.user_id == user_id).all()
    session.close()
    return sorted(histories, key=lambda x: x.id, reverse=True)


def get_auth_data(login: str) -> Auth:
    session = db_session.create_session()
    user = session.query(Auth).filter(Auth.login == login).all()
    session.close()
    if len(user) > 0:
        return user[0]
    else:
        return None


def check_login(login: str) -> bool:
    session = db_session.create_session()
    data = bool(session.query(Auth).filter(Auth.login == login).count())
    session.close()
    return data


def check_mail(mail: str) -> bool:
    session = db_session.create_session()
    data = bool(session.query(Auth).filter(Auth.email == mail).count())
    session.close()
    return data


def register_user(login, password, mail, name) -> User:
    session = db_session.create_session()
    user = User()
    auth = Auth()

    user.is_approved = False
    user.name = name
    user.role = 'user'
    user.key = geherate_key()
    auth.login = login
    auth.password = password
    auth.email = mail
    user.auth.append(auth)

    session.add(user)
    session.flush()

    application = Applications()
    print(user.id)
    application.user_id = user.id
    application.login = login
    session.add(application)

    session.commit()
    session.close()
    return user


def register_admin(login, password, mail, name) -> User:
    session = db_session.create_session()
    user = User()
    auth = Auth()
    user.is_approved = True
    user.name = name
    user.role = 'admin'
    user.key = geherate_key()
    auth.login = login
    auth.password = password
    auth.email = mail
    user.auth.append(auth)
    session.add(user)
    session.commit()
    session.close()


def delete_user(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    auth = user.auth[0]
    session.delete(user)
    session.delete(auth)
    session.commit()
    session.close()


def get_user_history(id) -> list:
    session = db_session.create_session()
    user = session.query(User).get(id)
    session.close()
    return user.history


def admin_get_reg(page_num: int) -> dict:
    session = db_session.create_session()
    query = session.query(Applications)
    page = SqlalchemyOrmPage(query, page=page_num, items_per_page=10)
    users = sorted(page.items, key=lambda x: x.date)
    for application in users:
        user = application.user
        auth = user.auth
        user.auth = auth
        application.user = user
    max_page = query.count() // 10 + 1
    session.close()
    return {'users': users, 'max': max_page}


def admin_get_users(page_num: int) -> dict:
    session = db_session.create_session()
    query = session.query(User).filter(User.is_approved == True)
    page = SqlalchemyOrmPage(query, page=page_num, items_per_page=10)
    users = sorted(page.items, key=lambda x: x.id, reverse=True)
    max_page = query.count() // 10 + 1
    for user in users:
        auth = user.auth
        user.auth = auth
    session.close()
    return {'users': users, 'max': max_page}


def admin_get_pars(page_num: int) -> dict:
    session = db_session.create_session()
    query = session.query(History)
    page = SqlalchemyOrmPage(query, page=page_num, items_per_page=10)
    pars = sorted(page.items, key=lambda x: x.id, reverse=True)
    max_page = query.count() // 10 + 1
    session.close()
    return {'pars': pars, 'max': max_page}


def admin_accept_user(id):
    if check_user(id):
        session = db_session.create_session()
        user = session.query(User).get(id)
        user.is_approved = True
        application = session.query(Applications).filter(
            Applications.user_id == id).first()
        session.delete(application)
        session.commit()
        session.close()
        return True


def admin_decline_user(id):
    if check_user(id):
        session = db_session.create_session()
        user = session.query(User).get(id)
        session.delete(user)
        session.delete(session.query(Applications).filter(
            Applications.user_id == id).first())
        session.commit()
        session.close()
        return True


def admin_delete_user(user_id):
    if check_user(user_id):
        delete_user(user_id)
        return True
