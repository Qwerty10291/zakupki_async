from flask import Flask, url_for, render_template, request, session, abort, redirect
from io import BytesIO
import datetime
from data import db_session


if __name__ == '__main__':
    db_session.global_init('db/db.sqlite')
