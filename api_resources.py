from flask.globals import session
from data.db_session import create_session
from flask import abort, jsonify
from data.models import *
from flask_restful import Resource, reqparse
from sqlalchemy.orm import Session
import json


def get_user_by_api_key(key) -> User:
    session = create_session()
    user = session.query(User).filter(User.key == key).all()
    if not user:
        return False
    return user[0]


history_parser = reqparse.RequestParser()
history_parser.add_argument(
    'key', required=True, type=str, help='Для доступа к API необходим ключ')

tedner_parser = reqparse.RequestParser()
tedner_parser.add_argument(
    'key', required=True, type=str, help='Для доступа к API необходим ключ')


class HistoryResource(Resource):
    def get(self, history_id: int):
        session = create_session()
        args = history_parser.parse_args()
        user = get_user_by_api_key(args['key'])
        if not user:
            return abort(401, 'Пользователя с таким ключом не существует')

        history: History = session.query(History).get(history_id)
        if not history:
            return abort(404, 'Запроса с таким id не существует')
        session.add(history)

        if history.user_id != user.id or user.role != 'admin':
            return abort(403, f'Этот запрос произведен не вами, ваш id: {user.id}')
        return jsonify({
            'history': history.to_dict(only=('id', 'state', 'tenders_count', 'tag', 'min_price', 'max_price', 'date_from', 'date_to', 'sort_filter', 'sort_direction', 'date')),
            'tenders': [tender.to_dict(only=('id', 'type', 'tender_date', 'tender_price', 'tender_date', 'tender_object', 'customer', 'tender_link')) for tender in history.tenders]
        })

    def delete(self, history_id: int):
        session = create_session()
        args = history_parser.parse_args()
        user = get_user_by_api_key(args['key'])
        if not user:
            return abort(401, 'Пользователя с таким ключом не существует')

        history = session.query(History).get(history_id)

        if not history:
            return abort(404, 'Запроса с таким id не существует')

        if history.user_id != user.id or user.role != 'admin':
            return abort(403, 'Этот запрос произведен не вами')

        session.delete(history)
        session.commit()
        return jsonify({'success': 'OK'})


class TenderResource(Resource):
    def get(self, tender_id: int):
        session = create_session()
        args = tedner_parser.parse_args()
        user = get_user_by_api_key(args['key'])
        if not user:
            return abort(401, 'Пользователя с таким ключом не существует')

        tender = session.query(Data).get(tender_id)
        if not tender:
            return abort(404, 'Тендера с таким id не существует')

        return jsonify({'tender': tender.to_dict(only=('id', 'type', 'tender_date', 'tender_price', 'tender_date', 'tender_object', 'customer', 'tender_link')),
                        'winner': tender.winner[0].to_dict(only=('name', 'position', 'price')),
                        'objects': [tender_object.to_dict(only=('position', 'name', 'unit', 'quantity', 'unit_price', 'price')) for tender_object in tender.objects]})
