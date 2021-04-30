from flask_login import LoginManager
login_manager = LoginManager()
from data import db_session
from data.models import User
from flask import redirect

@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)

@login_manager.unauthorized_handler
def unathorize():
    return redirect('/login')