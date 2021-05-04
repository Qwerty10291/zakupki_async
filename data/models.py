import datetime
from typing import List
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

history_association = sqlalchemy.Table('historyassociations', SqlAlchemyBase.metadata, 
                    sqlalchemy.Column('history_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('history.id')),
                    sqlalchemy.Column('data_id', sqlalchemy.BigInteger, sqlalchemy.ForeignKey('data.id')))



class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'user'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    role = sqlalchemy.Column(sqlalchemy.String, default='user')
    key = sqlalchemy.Column(sqlalchemy.String)
    is_approved = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_banned = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_parsing = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    reg_date = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.now())
    auth = orm.relation('Auth', back_populates="user")
    history = orm.relation('History', back_populates='user')


class Auth(SqlAlchemyBase):
    __tablename__ = 'Auth'
    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    login = sqlalchemy.Column(sqlalchemy.String)
    password = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String)
    user = orm.relation('User')


class History(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'history'

    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    state = sqlalchemy.Column(sqlalchemy.String)
    tenders_count = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    tag = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    min_price = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    max_price = sqlalchemy.Column(sqlalchemy.BigInteger, nullable=True)
    date_from = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    date_to = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.now())
    sort_filter = sqlalchemy.Column(sqlalchemy.String)
    sort_direction = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    date = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.now())
    tenders = orm.relation('Data', secondary=history_association, backref='tenders')
    user = orm.relation('User')


class Applications(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'applications'
    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('user.id'))
    login = sqlalchemy.Column(sqlalchemy.String)
    date = sqlalchemy.Column(
        sqlalchemy.DateTime, default=datetime.datetime.now())
    user = orm.relation('User')


class Data(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'data'

    id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True)
    type = sqlalchemy.Column(sqlalchemy.String)
    tender_price = sqlalchemy.Column(sqlalchemy.Float)
    tender_date = sqlalchemy.Column(sqlalchemy.DateTime)
    tender_object = sqlalchemy.Column(sqlalchemy.String)
    customer = sqlalchemy.Column(sqlalchemy.String)
    tender_adress = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    tender_delivery = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    tender_terms = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    tender_link = sqlalchemy.Column(sqlalchemy.String)
    document_links = orm.relation('TenderLinks', back_populates='data')
    winner = orm.relation('Winners', back_populates='data')
    objects = orm.relation('Objects', back_populates='data')


class Objects(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'object'
    id = sqlalchemy.Column(
        sqlalchemy.Integer, primary_key=True, autoincrement=True)
    tender_id = sqlalchemy.Column(
        sqlalchemy.BigInteger, sqlalchemy.ForeignKey('data.id'))
    position = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    unit = sqlalchemy.Column(sqlalchemy.String)
    quantity = sqlalchemy.Column(sqlalchemy.String)
    unit_price = sqlalchemy.Column(sqlalchemy.String)
    price = sqlalchemy.Column(sqlalchemy.String)
    data = orm.relation('Data')


class Winners(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'winner'
    data_id = sqlalchemy.Column(
        sqlalchemy.BigInteger, sqlalchemy.ForeignKey('data.id'), primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    position = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    data = orm.relation('Data')


class TenderLinks(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'links'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    data_id = sqlalchemy.Column(sqlalchemy.BigInteger, sqlalchemy.ForeignKey('data.id'))
    link = sqlalchemy.Column(sqlalchemy.String)
    data = orm.relation('Data')