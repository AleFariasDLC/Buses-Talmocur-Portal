from flask import Flask, render_template
import os
#import db_utils
from dotenv import load_dotenv
from pathlib import Path

import routes

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.getenv('SECRET_KEY')

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)
