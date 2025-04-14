import json
import random

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
import mysql.connector

app = Flask(__name__)


class Database():
    def get_db_connection(Database):
        chance = random.random()
        try:
            dbconnection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database=Database
            )
            return dbconnection
        except Exception as e:
            return e, 503

    def GetUserFlags(email):
        conn = mysql.connect(
            host="localhost",
            user="root",
            password="",
            database="test"
        )
        cursor = conn.cursor()
        cursor.execute('SELECT Flags FROM Account WHERE Email = %s', (email,))
        flags = cursor.fetchone()
        conn.close()

        if flags is None or flags[0] is None:
            return {}

        try:
            return json.loads(flags)
        except json.JSONDecodeError:
            return {}

    def GetUserEmailByUsername(username):
        conn = mysql.connect(
            host="localhost",
            user="root",
            password="",
            database=Database
        )
        cursor = conn.cursor()
        cursor.execute('SELECT Email FROM Account WHERE Username = %s', (username,))
        email = cursor.fetchone()
        conn.close()
        return email

    def GetUsernameByToken(token=None):
        if token is None:
            return "No token provided."
        conn = mysql.connect(
            host="localhost",
            user="root",
            password="",
            database=Database
        )
        cursor = conn.cursor()
        cursor.execute('SELECT Username FROM Account WHERE Token = %s', (token,))
        username = cursor.fetchone()
        conn.close()
        return username


@app.route('/Singlecraft/Auth/login', methods=['POST'])
def AuthLogin():
    global cursor, conn
    try:
        username = request.form['username']
        password = request.form['password']
        token = request.form['token']

        conn = Database.get_db_connection("test")
        if isinstance(conn, tuple):  # Error case
            return conn

        cursor = conn.cursor(dictionary=True)
        # Mettre à jour le token
        cursor.execute('UPDATE Account SET Token = %s WHERE Username = %s', (token, username))
        conn.commit()

        # Vérifier les credentials
        cursor.execute('SELECT * FROM Account WHERE Username = %s', (username,))
        account = cursor.fetchone()

        if account is None:
            return redirect(url_for('index'))

        if account['password'] == password:  # Assurez-vous que la colonne est nommée correctement
            response = make_response(redirect(url_for('home')))
            response.set_cookie("token", account['Token'], max_age=60 * 60 * 24 * 365)
            return response

        return redirect(url_for('index'))
    except Exception as e:
        print(f"Login error: {e}")
        return redirect(url_for('index'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/home')
def home():
    token = request.cookies.get('token')

    conn = Database.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Account WHERE Token = %s", (token,))
    account = cursor.fetchone()
    conn.close()

    return render_template("home.html", user=jsonify(name=account[1]))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)