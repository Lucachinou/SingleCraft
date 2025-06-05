import datetime
import json
import os
import random
import subprocess
import time
from threading import Thread

from MCProperties import Properties
from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, flash
import mysql.connector
import nbtlib
import shutil
import configparser
from pathlib import Path

app = Flask(__name__)
app.secret_key = "Ko5D8-4cDF3-95DFa-POd91"

date = datetime.datetime.now()

running_servers = {}
server_logs = {}

class Database():
    def get_db_connection(self, Database: str):
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

    def GetUserFlags(self, email):
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

    def GetUserEmailByUsername(self, username):
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

    def GetUsernameByToken(self, token=None):
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
    def SetupDatabase(self):
        conn = self.get_db_connection("Singlecraft")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Accounts (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    Email TEXT NULL,
                    Username TEXT NULL,
                    Password TEXT NULL,
                    Token TEXT NULL,
                    Access JSON DEFAULT '{}',
                    Rank TEXT DEFAULT 'Default' 
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Servers (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    Name TEXT NULL,
                    Owner TEXT NULL,
                    Jar TEXT DEFAULT 'Default.jar',
                    Memory INT DEFAULT 1024,
                    UsersAccess JSON NULL
        )''')
        print("#---------- DATABASE SETUP COMPLETE ----------#")

DatabaseManager = Database()

def GetUsers():
    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute('SELECT Username FROM accounts')
    users = cursor.fetchall()
    if users is not None:
        return [item for user in users for item in user]
    return []

@app.route('/Singlecraft/Auth/Register', methods=['POST', 'GET'])
def AuthRegister():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        token = request.form['token']


        if not username or username.strip() == "":
            flash("Nom d'utilisateur invalide")
            return redirect(url_for('AuthRegister'))

        conn = DatabaseManager.get_db_connection("Singlecraft")

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
        time.sleep(1)

        if account[3]:
            response = make_response(redirect(url_for('home')))
            response.set_cookie("token", account[3], max_age=60 * 60 * 24 * 365)
            return response
        else:
            return render_template(url_for('AuthLogin'))
    return redirect(url_for('AuthRegister'))
    

@app.route('/Singlecraft/Auth/login', methods=['POST'])
def AuthLogin():
    global cursor, conn
    try:
        username = request.form['username']
        password = request.form['password']
        token = request.form['token']

        conn = DatabaseManager.get_db_connection("Singlecraft")
        if isinstance(conn, tuple):  # Error case
            return conn
        cursor = conn.cursor()
        cursor.execute('UPDATE Accounts SET Token = %s WHERE Username = %s', (token, username))
        conn.commit()

        cursor.execute('SELECT * FROM Accounts WHERE Username = %s', (username,))
        account = cursor.fetchone()
        conn.close()
        if account is None:
            return redirect(url_for('Login'))
        if account[3] == password:
            response = make_response(redirect(url_for('home')))
            response.set_cookie("token", account[4], max_age=60 * 60 * 24 * 365)
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

    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("SELECT Access, Username FROM Accounts WHERE Token = %s", (request.cookies.get('token'),))
    Account = cursor.fetchone()

    """
    JsonDumpAccess = json.loads(Account[0])
    if isinstance(JsonDumpAccess.get("Access"), list):
        JsonDumpAccess["Access"].append(servername)
    else:
        JsonDumpAccess["Access"] = [JsonDumpAccess.get("Access", "")]
        JsonDumpAccess["Access"].append(servername)
    JsonAccess = json.dumps(JsonDumpAccess)
    """

    cursor.execute("SELECT Username FROM Accounts WHERE Token = %s", (request.cookies.get('token'),))
    Username = cursor.fetchone()

    cursor.execute("INSERT INTO Servers (Name, Owner) VALUES (%s, %s)", (servername, Username[0]))
    conn.commit()

    cursor.execute("SELECT ID FROM Servers WHERE Name = %s", (servername,))
    ServerID = cursor.fetchone()

    path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft"
    path.mkdir(exist_ok=True)
    FolderPath = path / "Servers" / f"Server-{ServerID[0]}"
    try:
        FolderPath.mkdir()
        EulaFile = FolderPath / "eula.txt"
        EulaFile.touch()
        EulaFile.write_text("#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).\n#Wed Apr 09 11:39:43 CEST 2025\neula=true")

        propertiesFile = FolderPath / "server.properties"
        propertiesFile.touch(exist_ok=True)
        propertiesFile.write_text(f"server-port=25565")
        return redirect(url_for('home'), 300)
    except FileExistsError:
        return redirect(url_for('home'), code=302)

@app.route("/API/DeleteServer", methods=['POST'])
def DeleteServer():
    servername = request.form['servername']
    token = request.cookies.get('token')

    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("SELECT Access, Username, Token FROM Accounts WHERE Token = %s", (request.cookies.get('token'),))
    Account = cursor.fetchone()

    cursor.execute("SELECT ID, Owner FROM Servers WHERE Name = %s", (servername,))
    ServerID = cursor.fetchone()

    if ServerID[1] == Account[1]:
        FolderPath = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{ServerID[0]}"

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
            return redirect(url_for('home'), code=200)
        else:
            return redirect(url_for('home'), code=200)
    return redirect(url_for('Home'), 200)


@app.route('/Server-Detail/<serverid>')
def Servers(serverid):
    if serverid is not None:
        token = request.args.get('token')

        conn = DatabaseManager.get_db_connection("Singlecraft")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Servers WHERE ID = %s", (serverid,))
        Servers = cursor.fetchone()
        server_port = None
        playerSlot = None

        cursor.execute("SELECT * FROM Accounts WHERE Token = %s", (token,))
        Account = cursor.fetchone()

        server_properties = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{serverid}" / "server.properties"
        if server_properties.exists():
            with open(server_properties, "r") as f:
                for line in f:
                    if line.startswith("server-port"):
                        server_port = int(line.split("=")[1])
                    if line.startswith("max-players"):
                        playerSlot = int(line.split("=")[1])
        else:
            server_properties = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{Servers[0]}" / "server.properties"
            server_properties.touch()
            server_properties.write_text(f"server-port=25565")

        if Servers is not None:
            return render_template("server.html", server={"id": Servers[0], "name": Servers[1], "Slot": playerSlot,"Version": Servers[3],"Memory": Servers[4], "Port": server_port})
        else:
            flash("Server not found")
            return redirect(url_for('Home'))
    return None

@app.route('/Server-Detail/Datapack/<server_id>')
def ServersDatapack(server_id):
    if server_id is not None:
        conn = DatabaseManager.get_db_connection("Singlecraft")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Servers WHERE ID = %s", (server_id,))
        Servers = cursor.fetchone()
        server_port = None
        playerSlot = None

        server_properties = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{server_id}" / "server.properties"
        if server_properties.exists():
            with open(server_properties, "r") as f:
                for line in f:
                    if line.startswith("server-port"):
                        server_port = int(line.split("=")[1])
                    if line.startswith("max-players"):
                        playerSlot = int(line.split("=")[1])

        if Servers is not None:
            return render_template("serverDatapack.html", server={"ID": Servers[0], "name": Servers[1], "Slot": playerSlot,"Version": Servers[3],"Memory": Servers[4], "Port": server_port})
        else:
            flash("Server not found")
            return redirect(url_for('home'))
    return None

@app.route('/API/UpdatePort/<port>/<server_id>', methods=['POST'])
def update_server_settings(port, server_id):
    server_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{server_id}"
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

@app.route("/API/GetProperties/<serverid>")
def get_properties(serverid):
    server_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{serverid}" / "world" / "level.dat"
    ServerProperties = server_path.parent.parent / "server.properties"
    ServProperties = Properties(str(ServerProperties))
    return str(ServProperties)

@app.route('/API/GetFeatures/<serverid>', methods=['GET'])
def get_features(serverid):
    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("SELECT Name FROM Servers WHERE ID = %s", (serverid,))
    ServerID = cursor.fetchone()
    if ServerID is not None:
        server_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{serverid}" / "world" / "level.dat"
        if server_path.exists():
            LevelDat = nbtlib.load(server_path)
            Level = LevelDat["Data"]["DataPacks"]
            return Level
        return None
    else:
        return redirect(url_for('home'))

@app.route('/API/EnableFeature/<serverid>/', methods=['POST'])
def EnableFeature(serverid):
    Data = request.json.get("data")
    server_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{serverid}" / "world" / "level.dat"
    ServerProperties = server_path.parent.parent / "server.properties"
    if  server_path.exists():

        LevelDat = nbtlib.load(server_path)
        EnabledList = LevelDat["Data"]["DataPacks"]["Enabled"]
        EnabledList.append(nbtlib.String(str(Data)))
        DisabledList = LevelDat["Data"]["DataPacks"]["Disabled"]
        DisabledList.remove(nbtlib.String(str(Data)))

        if LevelDat["Data"]["enabled_features"] is None:
            enabledfeatures = LevelDat["Data"]["enabled_features"] = nbtlib.List([])
        else:
            enabledfeatures = LevelDat["Data"]["enabled_features"]

        enabledfeatures.append(nbtlib.String(str(Data)))

        LevelDat.save()

        server_properties = server_path.parent.parent / "server.properties"

        ServProperties = Properties(str(server_properties))
        ServProperties.setValue(23, f"{ServProperties.getValue(23)}, {Data}")
        ServProperties.save()

        return LevelDat
    else:
        return redirect(url_for('home'))

@app.route('/API/DisableFeature/<serverid>/', methods=['POST'])
def disableFeature(serverid):
    Data = request.json.get("data")

    server_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{serverid}" / "world" / "level.dat"
    if  server_path.exists():
        LevelDat = nbtlib.load(server_path)
        EnabledList = LevelDat["Data"]["DataPacks"]["Enabled"]
        EnabledList.remove(nbtlib.String(str(Data)))
        DisabledList = LevelDat["Data"]["DataPacks"]["Disabled"]
        DisabledList.append(nbtlib.String(str(Data)))
        if LevelDat["Data"]["enabled_features"] is None:
            enabledfeatures = LevelDat["Data"]["enabled_features"] = nbtlib.List([])
        else:
            enabledfeatures = LevelDat["Data"]["enabled_features"]

        enabledfeatures.remove(nbtlib.String(str(Data)))

        LevelDat.save()

        server_properties = server_path.parent.parent / "server.properties"

        ServProperties = Properties(str(server_properties))
        ServProperties.RemoveValue(23, f"{Data}")
        ServProperties.save()
        return LevelDat
    else:
        return redirect(url_for('home'))

@app.route('/API/SetFeatures/<servername>/', methods=['POST'])
def set_features(servername):
    """
    Data = json.loads(request.json.get("Data"))

    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("SELECT ID FROM Servers WHERE Name = %s", (servername,))
    ServerID = cursor.fetchone()
    server_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{ServerID[0]}" / "world" / "level.dat"
    if  server_path.exists():
        LevelDat = nbtlib.load(server_path)
        Level = LevelDat["Data"]["DataPacks"]
        Level["Disabled"] = Data["Disabled"]
        Level["Enabled"] = Data["Enabled"]
        LevelDat.save()
        return Level
    else:
        return redirect(url_for('home'))
    """
    return "Not Implemented", 404

@app.route('/API/UpdateVersion/<jarfile>/<server_id>', methods=['POST'])
def update_server_version_settings(jarfile, server_id):
    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("UPDATE Servers SET Jar = %s WHERE ID = %s", (jarfile, server_id))
    conn.commit()
    cursor.close()
    return redirect(url_for("home"))

def start_server(server_id, jar_name):
    if server_id in running_servers:
        return False

    server_dir = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers" / f"Server-{server_id}"
    jar_path = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Jars" / jar_name

    if not jar_path.exists():
        return "Jar file not found", 404
    if not server_dir.exists():
        return "Server directory not found", 404

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

    server_logs[server_id] = []
    server_logs[server_id].append(f"[{date.hour}:{date.minute}:{date.second}] [SingleCraft/INFO] Starting server.")
    running_servers[server_id] = process

    def read_output():
        for line in iter(process.stdout.readline, ''):
            server_logs[server_id].append(line)
            if len(server_logs[server_id]) > 100:
                server_logs[server_id] = server_logs[server_id][-100:]

    Thread(target=read_output, daemon=True).start()
    return True

def stop_server(server_id):
    process = running_servers.get(server_id)
    token = request.cookies.get("token")

    if not process:
        server_logs[server_id].append(f"[{date.hour}:{date.minute}:{date.second}] [SingleCraft/INFO] Server already stopped.")
        return False
    try:
        server_logs[server_id].append(f"[{date.hour}:{date.minute}:{date.second}] [SingleCraft/INFO] Stopping server.")
        process.stdin.write("stop\n")
        #process.wait(timeout=10)
    except Exception as e:
        process.kill()
    finally:
        del running_servers[server_id]
    return True

def get_console_output(server_name):
    return server_logs.get(server_name, ["No console history for this server!"])

@app.route('/API/Console/<server_name>', methods=['GET'])
def get_console(server_name):
    logs = get_console_output(server_name)
    return jsonify({"logs": logs})

@app.route('/API/SendCommand/<server_id>', methods=['POST'])
def send_command(server_id):
    command = request.json.get("command")

    process = running_servers.get(server_id)
    if process and process.stdin:
        try:
            server_logs[server_id].append(f"[{date.hour}:{date.minute}:{date.second}] [SingleCraft/INFO] executing \"{command}\" ")
            process.stdin.write(command + '\n')
            process.stdin.flush()
            return jsonify({"success": True})
        except KeyError:
            server_logs[server_id].append(f"[{date.hour}:{date.minute}:{date.second}] [SingleCraft/INFO] Cannot execute \"{command}\" ")
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return jsonify({"success": False, "error": "Cannot send command."})


@app.route('/API/ClearConsoleHistory', methods=['GET'])
def clear_console_history():
    server_id = request.args.get('server_id')
    del server_logs[server_id]
    return 300

@app.route('/API/StartServer/<server_id>/<jar_name>', methods=['POST'])
def start_mc_server(server_id, jar_name):
    if server_id not in running_servers:
        success = start_server(server_id, jar_name)
        return jsonify({"success": success})
    return jsonify({"success": False})

@app.route('/API/StopServer/<server_id>', methods=['POST'])
def stop_mc_server(server_id):
    if server_id in running_servers:
        success = stop_server(server_id)
        return jsonify({"success": success})
    return jsonify({"success": False})

@app.route('/home')
def home():
    token = request.cookies.get('token')
    serversFile = Path.home() / "Documents" / "Scripts" / "Mes Scripts" / "SingleCraft" / "Servers"

    conn = DatabaseManager.get_db_connection("Singlecraft")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Accounts WHERE Token = %s", (token,))
    account = cursor.fetchone()
    isonline = None
    if account is None:
        return redirect(url_for('Logout'))


    servers = []
    for folder in serversFile.iterdir():
        if folder.is_dir():
            if folder.name.replace("Server-", "") in running_servers:
                isonline = True
            else:
                isonline = False
            cursor.execute("SELECT * FROM Servers WHERE ID = %s", (folder.name.replace("Server-", ""),))
            ServerDB = cursor.fetchone()
            if ServerDB is not None and ServerDB[2] == account[2]:
                server = {
                    "ID": ServerDB[0],
                    "name": ServerDB[1],
                    "PlayerSlot": ServerDB[2],
                    "Memory": ServerDB[3],
                    "Online": isonline,
                }
                servers.append(server)

    return render_template("home.html", user={"name": account[2], "token": account[3], "access": account[5], "flags": account[6]}, servers=servers)

if __name__ == '__main__':
    port=80
    try:
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"""
            #---------- Critical Error ----------#
            # An exception occured while starting server.
            # Please verify if the port {port} is not used by another program.
            #
            # The exception name was :
            # {e}
            #---------- End of error report ------#
        """)