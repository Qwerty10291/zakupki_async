from flask.globals import session
from data import db_session
from data.models import Applications, User, Auth, History
from paginate_sqlalchemy import SqlalchemyOrmPage
from utils import geherate_key


def get_user(id) -> User:
    session = db_session.create_session()
    return session.query(User).get(id)


def check_user(id) -> bool:
    session = db_session.create_session()
    return bool(session.query(User).filter(User.id == id).count())


def get_history(id):
    session = db_session.create_session()
    history = session.query(History).filter(History.id == id)
    if history:
        return history[0]
    else:
        return None

def load_histories(user_id) -> list:
    session = db_session.create_session()
    histories = session.query(History).filter(History.user_id == user_id).all()
    return reversed(histories)


def get_auth_data(login: str) -> Auth:
    session = db_session.create_session()
    user = session.query(Auth).filter(Auth.login == login).all()
    if len(user) > 0:
        return user[0]
    else:
        return None


def check_login(login: str) -> bool:
    session = db_session.create_session()
    return bool(session.query(Auth).filter(Auth.login == login).count())


def check_mail(mail: str) -> bool:
    session = db_session.create_session()
    return bool(session.query(Auth).filter(Auth.email == mail).count())


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


def delete_user(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    session.delete(user)
    session.commit()


def get_user_history(id) -> list:
    session = db_session.create_session()
    user = session.query(User).get(id)
    return user.history


def admin_get_users(page_num: int) -> list:
    session = db_session.create_session()
    query = session.query(Applications)
    page = SqlalchemyOrmPage(query, page=page_num, items_per_page=10)
    users = sorted(page.items, key=lambda x: x.date)
    return users


def admin_accept_user(id):
    if check_user(id):
        session = db_session.create_session()
        user = session.query(User).get(id)
        user.is_approved = True
        application = session.query(Applications).filter(
            Applications.user_id == id).first()
        session.delete(application)
        session.commit()
        return True


def admin_decline_user(id):
    if check_user(id):
        session = db_session.create_session()
        user = session.query(User).get(id)
        session.delete(user)
        session.delete(session.query(Applications).filter(
            Applications.user_id == id).first())
        session.commit()
        return True
