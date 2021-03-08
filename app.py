from flask import Flask, url_for, render_template, request, session, abort, redirect
from io import BytesIO
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title='Никак', date=datetime.datetime.now().strftime('%d.%m.%Y'))

@app.route('/start', methods=['GET', 'POST'])
def start_parser():
    if request.method == 'POST':
        print(request.form['tag'])
    return redirect('/')

if __name__ == '__main__':
    app.run('127.0.0.1', '8000', debug=True)