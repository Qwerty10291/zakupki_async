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
def load_reg():
    if current_user.role != 'admin':
        return 'вы не администратор'
    try:
        page = int(request.args.get('page'))
    except:
        return abort(500)
    data = db_additions.admin_get_reg(page)
    users = [{'id': user.user_id, 'login': user.login, 'name': user.user.name, 'mail': user.user.auth[0].email,
              'date': user.date.strftime('%d.%m.%Y')} for user in data['users']]
    max_page = data['max']
    return json.dumps({'data': users, 'page_max': max_page})


@blueprint.route('/admin/load_users')
@login_required
def load_users():
    if current_user.role != 'admin':
        return 'вы не администратор'
    try:
        page = int(request.args.get('page'))
    except:
        return abort(500)
    data = db_additions.admin_get_users(page)
    users = [{'id': user.id, 'role': user.role, 'name': user.name, 'login': user.auth[0].login,
              'mail': user.auth[0].email, 'date': user.reg_date.strftime('%d.%m.%Y')} for user in data['users']]
    max_page = data['max']
    return json.dumps({'data': users, 'page_max': max_page})


@blueprint.route('/admin/load_pars')
@login_required
def load_pars():
    if current_user.role != 'admin':
        return 'вы не админимтратор'
    try:
        page = int(request.args.get('page'))
    except:
        return abort(500)
    data = db_additions.admin_get_pars(page)
    pars = [{'id': pars.id, 'user_id': pars.user_id, 'tag': pars.tag, 'state': pars.state,
             'date': pars.date.strftime('%d.%m.%Y')} for pars in data['pars']]
    max_page = data['max']
    return json.dumps({'data': pars, 'page_max': max_page})


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


@blueprint.route('/admin/delete_user')
@login_required
def delete_user():
    if current_user.role != 'admin':
        return 'вы не администратор'

    try:
        user_id = int(request.args.get('id'))
    except:
        return abort(500)

    if not db_additions.delete_user(user_id):
        return 'ошибка удаления пользователя'
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
