from flask import Flask, url_for, render_template, request, session, abort, redirect
import request_blueprint
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import db_additions
import utils
from auth_forms import LoginForm, RegisterForm


app = Flask(__name__)
app.register_blueprint(request_blueprint.blueprint)
app.config["SECRET_KEY"] = "qazwsxedcrfv"


@app.route('/')
@utils.login_decorator
def index():
    user = db_additions.get_user(int(session['user']))
    return render_template("index.html", user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect('/')
    form = LoginForm()

    if form.validate_on_submit():
        user = db_additions.get_auth_data(request.form.get('login'))
        if not user:
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        if not check_password_hash(user.password, request.form.get('password')):
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')
        session['user'] = user.id
        session['role'] = user.user.id
        return redirect('/')
    return render_template('login.html', title='Вход', form=form)


@app.route('/register', methods=["GET", "POST"])
def register():
    if 'user' in session:
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
        session['user'] = user.id
        session['role'] = user.role
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@utils.login_decorator
def logout():
    session.pop('user')
    session.pop('role')
    return redirect('/login')


if __name__ == '__main__':
    db_session.global_init('db/db.sqlite')
    db = db_session.create_session()
    app.run('127.0.0.1', port=8080, debug=True)
