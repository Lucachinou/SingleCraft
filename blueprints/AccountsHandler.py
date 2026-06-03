import os
import secrets
import flask
import re

from modules import database

try:
    from argon2 import PasswordHasher
except ModuleNotFoundError:
    argon2 = None
    import hashlib

bp = flask.Blueprint("Accounts", __name__, url_prefix="/API/Auth")
try:
    hasher = PasswordHasher(
        time_cost=2,
        memory_cost=19456,
        parallelism=1,
        hash_len=32,
        salt_len=16,
    )
except:
    hasher = None

@bp.post("/Login")
def login():
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    if username is None or username.strip() == "" or password is None or password.strip() == "":
        return flask.jsonify({"message": "INVALID_CREDENTIALS"}), 401

    username = username.lower()
    if hasher is None: password = hashlib.sha256(password.encode()).hexdigest()

    conn = database.get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute("SELECT Password, Token FROM Accounts WHERE Username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is None:
        return flask.jsonify({"message": "INVALID_CREDENTIALS"}), 401

    try:
        is_password_valid = hasher.verify(result[0], password) if hasher else result[0] == password
    except:
        return flask.jsonify({"message": "INVALID_CREDENTIALS"}), 401
    if is_password_valid:
        response = flask.redirect(flask.url_for("BaseRoute.home"))
        response.set_cookie("token", result[1], max_age=60 * 60 * 24 * 365)
        return response
    else:
        return flask.jsonify({"message": "INVALID_CREDENTIALS"}), 401

@bp.post("/Register")
def register():
    username = flask.request.form.get("username")
    email = flask.request.form.get("username")
    password = flask.request.form.get("password")
    if username is None or username.strip() == "" or password is None or password.strip() == "":
        return flask.jsonify({"message": "MISSING_ARGUMENTS"}), 401

    if re.findall(r"(\w+@\w+.\w{3})", email):
        return flask.jsonify({"message": "INVALID_EMAIL"}), 401

    token = secrets.token_urlsafe(32)

    username = username.lower()
    password = hasher.hash(password) if hasher else hashlib.sha256(password.encode()).hexdigest()

    conn = database.get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute("SELECT ID FROM Accounts WHERE Username = %s OR Email = %s", (username, email,))
    result = cursor.fetchone()
    if result is not None:
        cursor.close()
        conn.close()
        return flask.redirect(flask.url_for("BaseRoute.index"))

    cursor.execute("INSERT INTO Accounts (ID, Email, Username, Password, Token, Access, `Rank`) VALUES (DEFAULT, %s, %s, %s, %s, DEFAULT, DEFAULT)", (email, username, password, token))
    conn.commit()
    cursor.close()
    conn.close()
    response = flask.make_response(flask.redirect(flask.url_for("BaseRoute.home")))
    response.set_cookie("token", token, max_age=60 * 60 * 24 * 365)
    return response

@bp.get("/Logout")
def logout():
    response = flask.Response(flask.url_for("BaseRoute.index"))
    response.set_cookie("token", "", max_age=0)
    return response