from flask import Flask, url_for, render_template, request, session, abort, redirect
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title='Никак')

if __name__ == '__main__':
    app.run('127.0.0.1', '8000', debug=True)