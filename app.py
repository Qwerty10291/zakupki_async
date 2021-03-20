from flask import Flask, url_for, render_template, request, session, abort, redirect
from flask_login import login_required, login_user, logout_user, current_user
import request_blueprint
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import db_additions
import utils
from auth_forms import LoginForm, RegisterForm
from login import login_manager

app = Flask(__name__)
login_manager.init_app(app)
app.register_blueprint(request_blueprint.blueprint)
app.config["SECRET_KEY"] = "qazwsxedcrfv"


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
        user = db_additions.get_auth_data(request.form.get('login'))
        if not user:
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        if not check_password_hash(user.password, request.form.get('password')):
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        login_user(db_additions.get_user(user.id))
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
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)
    


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect('/login')


if __name__ == '__main__':
    db_session.global_init('db/db.sqlite')
    request_blueprint.controller.start_loop()
    app.run('127.0.0.1', port=8080, debug=True)
