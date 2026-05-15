from flask import Flask, render_template
import os
#import db_utils
from dotenv import load_dotenv
from pathlib import Path

import routes

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
