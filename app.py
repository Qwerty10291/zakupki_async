from flask import Flask, url_for, render_template, request, session, abort, redirect
from io import BytesIO
import datetime
from data import db_session
from werkzeug.security import generate_password_hash, check_password_hash
import db_additions
from auth_forms import LoginForm, RegisterForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "qaz2wsx1edc4rfv3"


@app.route('/')
def index():
    if 'user' in session:
        user = db_additions.get_user(session['user'])
        return render_template("index.html", user)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect('/')
    form = LoginForm()
    
    if form.validate_on_submit():
        print(request.form)
        return redirect('/login')
    return render_template('login.html', form=form, url="/login", title='Вход')

@app.route('/register', methods=["GET", "POST"])
def register():
    if 'user' in session:
        return redirect('/')
    
    form = RegisterForm
    if form.validate_on_submit():
        print(request.form)
        return redirect('/login')
    return render_template('login.html', form=form, url='/register', title='Регистрация')




if __name__ == '__main__':
    db_session.global_init('db/db.sqlite')
    db = db_session.create_session()
    app.run('127.0.0.1', port=8080, debug=True)
