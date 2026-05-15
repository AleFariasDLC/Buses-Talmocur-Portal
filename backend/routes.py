from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
import os, sqlite3

routes = Blueprint('routes', __name__)


@routes.route('api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registered successfully'})

