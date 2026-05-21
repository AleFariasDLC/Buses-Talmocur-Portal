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

@routes.route('api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({'message': 'Sesion Iniciada'})
    else:
        return jsonify({'message': 'Correo o clave invalido, intente de nuevo'}), 401