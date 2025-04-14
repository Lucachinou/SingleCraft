import json
import os
import random
import subprocess
from threading import Thread

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, flash
import mysql.connector
import shutil
import configparser
from pathlib import Path

app = Flask(__name__)
#app.secret_key("Ko5D8-4cDF3-95DFa-POd91")

running_servers = {}
server_logs = {}

class Database():
    def get_db_connection(Database):
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
        conn = mysql.connector.connect(
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
        conn = mysql.connector.connect(
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
        conn = mysql.connector.connect(
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

    def Setup(self):
        with Database.get_db_connection("Singlecraft") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Accounts (
                    Email TEXT,
                    Username TEXT,
                    Password TEXT,
                    Token TEXT,
                    Rank TEXT,
                    Access JSON,
                    Flags JSON
                );
            """)

            # Table Servers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Servers (
                    Name TEXT,
                    PlayerSlot INT,
                    Version TEXT,
                    MaxMemory INT,
                    ModsPlugins JSON
                );
            """)
            conn.commit()

Setup = Database()

Database.Setup(Setup)

@app.route('/Singlecraft/Auth/Register', methods=['POST', 'GET'])
def AuthRegister():
    print("1")
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        token = request.form['token']


        if not username or username.strip() == "":
            flash("Nom d'utilisateur invalide")
            return redirect(url_for('AuthRegister'))

        conn = Database.get_db_connection("Singlecraft")

        cursor = conn.cursor()


        cursor.execute('SELECT * FROM Accounts WHERE Username = %s OR Email = %s', (username, email))
        account = cursor.fetchone()
        if account:
            flash("Account existant")
            conn.close()
            return redirect(url_for('AuthRegister'))


        cursor.execute('INSERT INTO Accounts (Username, Email, Token, Password, Rank) VALUES (%s, %s, %s, %s, %s)',
                    (username, email, token, password, "Default"))
        conn.commit()

        conn.close()

        response = make_response(redirect(url_for('home')))
        response.set_cookie("token", account[3], max_age=60 * 60 * 24 * 365)
        return response
    return redirect(url_for('AuthRegister'))
    

@app.route('/Singlecraft/Auth/login', methods=['POST'])
def AuthLogin():
    global cursor, conn
    try:
        username = request.form['username']
        password = request.form['password']
        token = request.form['token']

        conn = Database.get_db_connection("Singlecraft")
        if isinstance(conn, tuple):  # Error case
            return conn
        cursor = conn.cursor()
        # Mettre à jour le token
        cursor.execute('UPDATE Accounts SET Token = %s WHERE Username = %s', (token, username))
        conn.commit()
        # Vérifier les credentials
        cursor.execute('SELECT * FROM Accounts WHERE Username = %s', (username,))
        account = cursor.fetchone()
        conn.close()
        if account is None:
            return redirect(url_for('Login'))
        if account[2] == password:  # Assurez-vous que la colonne est nommée correctement
            response = make_response(redirect(url_for('home')))
            response.set_cookie("token", account[3], max_age=60 * 60 * 24 * 365)
            return response

        return redirect(url_for('home'))
    except Exception as e:
        return redirect(url_for('Login'))

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/Register')
def Register():
    return render_template('register.html')
@app.route('/')
def Login():
    token = request.cookies.get('token')
    if token:
        return redirect(url_for('home'))
    else:
        return render_template('login.html')

@app.route('/logout')
def Logout():
    response = make_response(redirect(url_for('Login')))
    response.set_cookie("token", "None", max_age=0)
    return response

@app.route('/API/CreateServer', methods=['POST'])
def CreateServer():
    servername = request.form['servername']
    serverslot = request.form['serverslot']

    with Database.get_db_connection("Singlecraft") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Access, Username FROM Accounts WHERE Token = %s", (request.cookies.get('token'),))
        Account = cursor.fetchone()

        JsonDumpAccess = json.loads(Account[0])
        if isinstance(JsonDumpAccess.get("Access"), list):
            JsonDumpAccess["Access"].append(servername)
        else:
            JsonDumpAccess["Access"] = [JsonDumpAccess.get("Access", "")]
            JsonDumpAccess["Access"].append(servername)
        JsonAccess = json.dumps(JsonDumpAccess)

        cursor.execute("UPDATE Accounts SET Access = %s WHERE Token = %s", (JsonAccess, request.cookies.get('token')))
        conn.commit()

        cursor.execute("INSERT INTO Servers (Name, PlayerSlot) VALUES (%s, %s)", (servername, serverslot))
        conn.commit()

        path = Path.home() / "Documents" / "Script" / "SingleCraft"
        path.mkdir(exist_ok=True)
        FolderPath = path / "Servers" / servername
        try:
            FolderPath.mkdir()
            EulaFile = FolderPath / "eula.txt"
            EulaFile.touch()
            EulaFile.write_text("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Apr 09 11:39:43 CEST 2025\neula=true")
            return redirect(url_for('home'), 300)
        except FileExistsError:
            return redirect(url_for('home'), code=302)

@app.route("/API/DeleteServer", methods=['POST'])
def DeleteServer():
    servername = request.form['servername']
    token = request.cookies.get('token')
    FolderPath = Path.home() / "Documents" / "Script" / "SingleCraft" / "Servers" / servername

    print(FolderPath)
    with Database.get_db_connection("Singlecraft") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Access, Username, Token FROM Accounts WHERE Token = %s", (request.cookies.get('token'),))
        Account = cursor.fetchone()

        JsonDumpAccess = json.loads(Account[0])

        if FolderPath.exists() and servername in JsonDumpAccess.get("Access", []):
            if isinstance(JsonDumpAccess.get("Access"), list):
                try:
                    shutil.rmtree(FolderPath)
                    JsonDumpAccess["Access"].remove(servername)
                except ValueError:
                    return redirect(url_for('home'))
            else:
                try:
                    JsonDumpAccess["Access"] = [JsonDumpAccess.get("Access", "")]
                    JsonDumpAccess["Access"].remove(servername)
                except ValueError:
                    return redirect(url_for('Home'))

            JsonAccess = json.dumps(JsonDumpAccess)
            cursor.execute("UPDATE Accounts SET Access = %s WHERE Token = %s", (JsonAccess, token))
            conn.commit()

            cursor.execute("DELETE FROM Servers WHERE Name = %s", (servername,))
            conn.commit()
            return redirect(url_for('home'), code=300)
        else:
            return redirect(url_for('home'), code=300)

@app.route('/Server-Detail/<servername>')
def Servers(servername):
    if servername is not None:
        with Database.get_db_connection("Singlecraft") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Servers WHERE Name = %s", (servername,))
            Servers = cursor.fetchone()
            server_port = None

            try:
                server_properties = Path.home() / "Documents" / "Script" / "SingleCraft" / "Servers" / servername / "server.properties"
                with open(server_properties, "r") as f:
                    for line in f:
                        if line.startswith("server-port"):
                            server_port = int(line.split("=")[1])
            except:
                server_properties = Path.home() / "Documents" / "Script" / "SingleCraft" / "Servers" / servername / "server.properties"
                server_properties.touch()
                server_properties.write_text(f"server-port=25565")


            if Servers is not None:
                return render_template("server.html", server={"name": Servers[0], "Slot": Servers[1],"Version": Servers[2],"Memory": Servers[3], "Port": server_port})
            else:
                flash("Server not found")
                return redirect(url_for('Home'))

@app.route('/API/UpdatePort/<port>/<servername>', methods=['POST'])
def update_server_settings(port, servername):

    server_path = Path.home() / "Documents" / "Script" / "SingleCraft" / "Servers" / servername
    server_properties = server_path / "server.properties"
    if server_properties.exists():
        lines = server_properties.read_text().splitlines()
        new_lines = []
        for line in lines:
            if line.startswith("server-port="):
                new_lines.append(f"server-port={port}")
            else:
                new_lines.append(line)
        server_properties.write_text("\n".join(new_lines))

    return redirect(url_for("home"))

@app.route('/API/UpdateVersion/<jarfile>/<servername>', methods=['POST'])
def update_server_version_settings(jarfile, servername):
    with Database.get_db_connection("Singlecraft") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE Servers SET Version = %s WHERE Name = %s", (jarfile, servername))
        conn.commit()

    return redirect(url_for("home"))

def start_server(server_name, jar_name):
    if server_name in running_servers:
        return False

    server_dir = Path.home() / "Documents" / "Script" / "SingleCraft" / "Servers" / server_name
    jar_path = Path.home() / "Documents" / "Script" / "SingleCraft" / "Jars" / jar_name

    if not jar_path.exists():
        raise FileNotFoundError("Fichier JAR non trouvé")

    server_dir.mkdir(parents=True, exist_ok=True)

    process = subprocess.Popen(
        ["java", "-Xmx2G", "-Xms1G", "-jar", str(jar_path), "nogui"],
        cwd=server_dir,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    server_logs[server_name] = []
    server_logs[server_name].append("[SingleCraft] Démarrage du serveur demander par l'utilisateur.")
    running_servers[server_name] = process

    def read_output():
        for line in iter(process.stdout.readline, ''):
            server_logs[server_name].append(line)
            if len(server_logs[server_name]) > 100:
                server_logs[server_name] = server_logs[server_name][-100:]

    Thread(target=read_output, daemon=True).start()
    return True

def stop_server(server_name):
    process = running_servers.get(server_name)
    token = request.cookies.get("token")

    if not process:
        return False
    try:
        server_logs[server_name].append(f"[SingleCraft] Arret du serveur demander par l'utilisateur.")
        process.stdin.write("stop\n")
        #process.wait(timeout=10)
    except Exception as e:
        process.kill()
    finally:
        del running_servers[server_name]
    return True

def get_console_output(server_name):
    return server_logs.get(server_name, ["Server not launched!"])

@app.route('/API/Console/<server_name>', methods=['GET'])
def get_console(server_name):
    logs = get_console_output(server_name)
    return jsonify({"logs": logs})

@app.route('/API/SendCommand/<server_name>', methods=['POST'])
def send_command(server_name):
    command = request.json.get("command")

    process = running_servers.get(server_name)
    if process and process.stdin:
        try:
            server_logs[server_name].append(f"[SingleCraft] executing \"{command}\" ")
            process.stdin.write(command + '\n')
            process.stdin.flush()
            return jsonify({"success": True})
        except KeyError:
            server_logs[server_name].append(f"[SingleCraft] Cannot execute \"{command}\" ")
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "Cannot send command."})


@app.route('/API/ClearConsoleHistory', methods=['GET'])
def clear_console_history():
    server_name = request.args.get('servername')
    del server_logs[server_name]
    return 300

@app.route('/API/StartServer/<server_name>/<jar_name>', methods=['POST'])
def start_mc_server(server_name, jar_name):
    success = start_server(server_name, jar_name)
    return jsonify({"success": success})

@app.route('/API/StopServer/<server_name>', methods=['POST'])
def stop_mc_server(server_name):
    success = stop_server(server_name)
    return jsonify({"success": success})

@app.route('/home')
def home():
    token = request.cookies.get('token')
    serversFile = Path.home() / "Documents" / "Script" / "SingleCraft" / "Servers"

    with Database.get_db_connection("Singlecraft") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Accounts WHERE Token = %s", (token,))
        account = cursor.fetchone()
        isonline = None
        if account is None:
            return redirect(url_for('Logout'))


        servers = []
        for folder in serversFile.iterdir():
            if folder.is_dir():
                if running_servers.get(folder.name) is not None:
                    isonline = True
                else:
                    print(folder.name)
                    isonline = False
                cursor.execute("SELECT * FROM Servers WHERE Name = %s", (folder.name,))
                ServerDB = cursor.fetchone()
                server = {
                    "name": folder.name,
                    "PlayerSlot": ServerDB[1],
                    "Memory": ServerDB[3],
                    "Online": isonline,
                }
                servers.append(server)

        return render_template("home.html", user={"name": account[1], "token": account[3], "access": account[5], "flags": account[6]}, servers=servers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)