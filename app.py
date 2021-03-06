from flask import Flask, url_for, render_template, request, session, abort, redirect
from flask_login import login_required, login_user, logout_user, current_user
from flask_restful import Api
import request_blueprint
import admin_blueprint
import api_blueprint
from api_resources import HistoryResource, TenderResource
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import db_additions
import utils
from auth_forms import LoginForm, RegisterForm
from login import login_manager
import asyncio

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
login_manager.init_app(app)
app.register_blueprint(request_blueprint.blueprint)
app.register_blueprint(admin_blueprint.blueprint)
app.register_blueprint(api_blueprint.blueprint)
app.config["SECRET_KEY"] = "qazwsxedcrfv"

api = Api(app)
api.add_resource(HistoryResource, '/api/queries/<int:history_id>')
api.add_resource(TenderResource, '/api/tenders/<int:tender_id>')
api.app.config['RESTFUL_JSON'] = {'ensure_ascii': False}

@app.route('/')
@login_required
def index():
    return render_template("index.html", user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()

    if form.validate_on_submit():
        auth = db_additions.get_auth_data(request.form.get('login'))
        if not auth:
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        if not check_password_hash(auth.password, request.form.get('password')):
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        user = db_additions.get_user(auth.id)
        if not user.is_approved:
            return render_template('login.html', title='Вход', form=form, errors='Администратор не подтвердил заявку на регистрацию')

        login_user(db_additions.get_user(auth.id))
        return redirect('/')
    return render_template('login.html', title='Вход', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        name = request.form.get('username')
        login = request.form.get('login')

        if db_additions.check_login(login):
            return render_template('register.html', title='Регистрация', form=form, errors="Данный логин занят.")
        hashed_password = generate_password_hash(request.form.get('password'))

        if not utils.check_email(request.form['email']):
            return render_template('register.html', title='Регистрация', form=form, errors="Неправильный формат почты.")
        email = request.form.get('email')
        if db_additions.check_mail(email):
            return render_template('register.html', title='Регистрация', form=form, errors='Данная почта уже используется.')
        user = db_additions.register_user(login, hashed_password, email, name)
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect('/login')


if __name__ == '__main__':
    db_session.global_init('db/db.sqlite')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run('127.0.0.1', port=8000, debug=False)
