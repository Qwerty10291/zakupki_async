from sqlalchemy.orm import session
from data import db_session
from data.models import User, Auth
from utils import geherate_key


def get_user(id) -> User:
    session = db_session.create_session()
    return session.query(User).get(id)


def check_user(id) -> bool:
    session = db_session.create_session()
    return bool(session.query(User).filter(User.id == id).count())


def get_auth_data(login: str) -> Auth:
    session = db_session.create_session()
    user = session.query(Auth).filter(Auth.login == login)
    if user:
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
    user.name = name
    user.key = geherate_key()
    auth.login = login
    auth.password = password
    auth.email = mail
    user.auth.append(auth)
    session.add(user)
    session.commit()
    return user


def delete_user(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    session.delete(user)
    session.commit()


def get_user_history(id) -> list:
    session = db_session.create_session()
    user = session.query(User).get(id)
    return user.history
