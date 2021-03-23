from flask import Blueprint, render_template, redirect, abort, jsonify, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import json
import db_additions
from utils import check_email
from data.models import *
from data.db_session import create_session

blueprint = Blueprint('admin', __name__, template_folder='templates')


@blueprint.route('/admin')
@login_required
def index():
    if current_user.role != 'admin':
        return 'вы не администратор'
    return render_template('admin.html')


@blueprint.route('/admin/load_users_reg')
@login_required
def load_users():
    if current_user.role != 'admin':
        return 'вы не администратор'
    try:
        page = request.args.get('page')
    except:
        return abort(500)
    users = db_additions.admin_get_users(page)
    data = json.dumps([{'id': user.user_id, 'login': user.login, 'name': user.user.name, 'mail': user.user.auth[0].email,
                        'date': user.date.strftime('%d.%m.%Y')} for user in users])
    return data


@blueprint.route('/admin/accept_user')
@login_required
def accept_user():
    if current_user.role != 'admin':
        return 'вы не администратор'

    try:
        user_id = int(request.args.get('id'))
    except:
        return abort(500)

    if not db_additions.admin_accept_user(user_id):
        return 'пользователя с таким id не существует'
    return 'success'


@blueprint.route('/admin/decline_user')
@login_required
def decline_user():
    if current_user.role != 'admin':
        return 'вы не администратор'

    try:
        user_id = int(request.args.get('id'))
    except:
        return abort(500)

    if not db_additions.admin_decline_user(user_id):
        return 'пользователя с таким id не существует'
    return 'success'


@blueprint.route('/admin/register_admin', methods=['POST'])
@login_required
def register_admin():
    if current_user.role != 'admin':
        return 'вы не администратор'

    name = request.form.get('username')
    login = request.form.get('login')

    if db_additions.check_login(login):
        return 'данный логин занят'
    hashed_password = generate_password_hash(request.form.get('password'))

    email = request.form.get('email')
    if not check_email(email):
        return 'неправильный формат почты'

    if db_additions.check_mail(email):
        return 'Данная почта уже используется.'
    print(name, login, email)
    db_additions.register_admin(login, hashed_password, email, name)

    return 'success'
