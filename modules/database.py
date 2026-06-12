import ast
import json

import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()


def get_db_connection(database: str):
    try:
        dbconnection = mysql.connector.connect(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=database
        )
        return dbconnection

    except Exception as e:
        raise RuntimeError(
            f"Unable to connect to database. \n{e}"
        )

def GetUserEmailByUsername(username):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Email FROM Accounts WHERE Username = %s', (username,))
    email = cursor.fetchone()
    conn.close()
    return email


def GetUserIDByToken(token):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT ID FROM Accounts WHERE Token = %s', (token,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


def GetUsernameByToken(token=None):
    if token is None:
        return "No token provided."
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Username FROM Accounts WHERE Token = %s', (token,))
    username = cursor.fetchone()
    conn.close()
    return username


def DatabaseUpdated():
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'singlecraft' AND table_name = 'Accounts'")
    IsAccountExist = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'singlecraft' AND table_name = 'Settings'")
    IsSettingsExist = cursor.fetchone()
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'singlecraft' AND table_name = 'InstalledVersions'")
    IsInstalledVersionsExist = cursor.fetchone()
    cursor.close()
    conn.close()
    return True if IsAccountExist[0] == 1 and IsSettingsExist[0] == 1 and IsInstalledVersionsExist[0] else False

def getPermission(user_id: int, server_id: int):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Access FROM Accounts WHERE ID = %s', (user_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    if result is None:
        return None

    for server in ast.literal_eval(result[0][0]):
        if server.get('id') == server_id:
            return server.get('rank')
    return None

def getServerJar(server_id: int):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT jar FROM servers WHERE ID = %s', (server_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def getServerMemory(server_id: int):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Memory FROM servers WHERE ID = %s', (server_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def GetSetting(ID):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Value FROM Settings WHERE ID = %s', (ID,))
    setting = cursor.fetchone()
    return setting[0] if setting else None

def GetSettings():
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Name, Value FROM Settings")
    settings = cursor.fetchall()
    cursor.close()
    conn.close()
    return settings

def UpdateSetting(ID: int, Value: str):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('UPDATE Settings SET Value = %s WHERE ID = %s', (Value, ID))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def getUserRank(user_id: int):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Rank FROM Accounts WHERE ID = %s', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None


def GetUsernameByID(user_id: int):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Username FROM Accounts WHERE ID = %s', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def changeServerJar(server_id: int, jar_name: str):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute("UPDATE servers SET jar = %s WHERE ID = %s",(jar_name, server_id,))
    conn.commit()
    cursor.close()
    conn.close()

def getServerNameFromID(server_id: int):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT Name FROM servers WHERE ID = %s', (server_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else 0

def removeInstalledVersionFromName(name: str):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM InstalledVersions WHERE Name = %s', (name,))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def removeInstalledVersionFromFile_name(file_name: str):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM InstalledVersions WHERE file_name = %s', (file_name,))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def addInstalledVersion(name: str, file_name: str, start_command="java -Xmx{max_memory} -jar {file_name}"):
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('INSERT INTO InstalledVersions VALUES (%s, %s, %s)', (name, file_name, start_command))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def getInstalledVersion():
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM InstalledVersions')
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def SetupDatabase():
    conn = get_db_connection(os.getenv("DATABASE_NAME"))
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Accounts
                      (
                          ID
                              INT
                              AUTO_INCREMENT
                              PRIMARY
                                  KEY,
                          Email
                              TEXT
                              NULL,
                          Username
                              TEXT
                              NULL,
                          Password
                              TEXT
                              NULL,
                          Token
                              TEXT
                              NULL,
                          Access
                              JSON
                              DEFAULT
                                  '[]',
                          `rank`
                              TEXT
                              DEFAULT
                                  'default'
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS servers
                      (
                          ID
                              INT
                              AUTO_INCREMENT
                              PRIMARY
                                  KEY,
                          Name
                              TEXT
                              NULL,
                          Owner
                              TEXT
                              NULL,
                          jar
                              TEXT
                              DEFAULT
                                  'Default.jar',
                          Memory
                              INT
                              DEFAULT
                                  1024
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Settings
                      (
                          ID
                              INT
                              AUTO_INCREMENT
                              PRIMARY
                                  KEY,
                          Name
                              TEXT
                              NULL,
                          Value
                              TEXT
                              NULL
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS InstalledVersions
                      (
                          Name
                              TEXT
                              NULL,
                          file_name
                              TEXT
                              NULL,
                          start_command
                              TEXT
                              NULL
                      )''')

    cursor.execute('TRUNCATE TABLE Settings')
    cursor.execute("INSERT IGNORE INTO Settings (Name, Value) VALUES ('SpigotWarning', 'False')")
    cursor.execute("INSERT IGNORE INTO Settings (Name, Value) VALUES ('EnableRCon', 'True')")
    cursor.execute("INSERT IGNORE INTO Settings (Name, Value) VALUES ('AllowLogin', 'True')")
    cursor.execute("INSERT IGNORE INTO Settings (Name, Value) VALUES ('AllowRegister', 'True')")
    conn.commit()
    cursor.close()
    conn.close()
    print("#---------- DATABASE SETUP COMPLETE ----------#")
