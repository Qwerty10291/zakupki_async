from sqlalchemy.orm import session
from data import db_session
from data.models import User, Auth

def get_user(id):
    session = db_session.create_session()
    return session.query(User).get(id)

def get_auth_data(login):
    session = db_session.create_session()
    user = session.query(Auth).filter(Auth.login)
    if user:
        return user[0]
    else:
        return None

def register_user(login, password, mail, name):
    session = db_session.create_session()
    user = User()
    auth = Auth()
    user.name = name
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

def get_user_history(id):
    session = db_session.create_session()
    user = session.query(User).get(id)
    return user.history