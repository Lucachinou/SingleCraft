import subprocess

import flask
import requests

from modules import database

bp = flask.Blueprint("Settings", __name__, url_prefix="/API/Settings")

@bp.get('/API/GetCurrentVersion')
def get_current_version():
    result = subprocess.run("git log --oneline", shell=True, text=True, capture_output=True)
    current_version = result.stdout[:7]
    return flask.jsonify({"success": True, "version": current_version})

@bp.get('/API/IsUpdateAvailable')
def IsUpdateAvailable():
    response = requests.get("https://api.github.com/repos/lucachinou/SingleCraft/commits/main")
    if response.status_code == 200:
        latest_commit = response.json()['sha'][6]
        return flask.jsonify({"success": True, "latest_commit": latest_commit, "is_update_available": latest_commit != subprocess.run("git log --oneline", shell=True, text=True, capture_output=True).stdout[:7]})
    else:
        return flask.jsonify({"success": False, "latest_commit": None})

@bp.get("/IsAuthAvailable")
def IsRegisterAvailable():
    return flask.jsonify({"login": database.GetSetting(3).lower(), "register": database.GetSetting(4).lower()})

@bp.get("/GetSettings")
def GetSettings():
    return flask.jsonify({"settings": database.GetSettings()})

@bp.get("/GetInstalledVersion")
def GetInstalledVersion():
    token = flask.request.cookies.get("token")
    if not token:
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})
    return flask.jsonify({"success": True, "version": database.getInstalledVersion()})

@bp.post("/AddInstalledVersion")
def AddInstalledVersion():
    data = flask.request.get_json()

    token = flask.request.cookies.get("token")
    name = data.get("name")
    version = data.get("version")
    start_command = data.get("start_command")
    if not name or not version or not start_command:
        return flask.jsonify({"success": False, "message": "INVALID_PARAMETERS"})

    if not token:
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})
    rank = database.getUserRank(database.GetUserIDByToken(token))
    if rank != "ADMIN":
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})

    return flask.jsonify({"success": database.addInstalledVersion(name, version, start_command)})

@bp.delete("/RemoveInstalledVersion")
def RemoveInstalledVersion():
    token = flask.request.cookies.get("token")
    name = flask.request.args.get("name")
    if not name:
        return flask.jsonify({"success": False, "message": "INVALID_PARAMETERS"})
    if not token:
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})
    rank = database.getUserRank(database.GetUserIDByToken(token))
    if rank != "ADMIN":
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})

    return flask.jsonify({"success": database.removeInstalledVersionFromName(name)})

@bp.post("/UpdateSetting")
def UpdateSettings():
    setting_id = flask.request.args.get("setting_id")
    setting_value = flask.request.args.get("setting_value")
    if setting_id is None or setting_value is None:
        return flask.jsonify({"success": False, "message": "INVALID_PARAMETERS"})
    try:
        setting_id = int(setting_id)
    except (ValueError, TypeError):
        return flask.jsonify({"success": False, "message": "INVALID_PARAMETERS"})
    if flask.request.cookies.get("token") is None:
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})

    rank = database.getUserRank(database.GetUserIDByToken(flask.request.cookies.get("token")))
    if rank != "ADMIN":
        return flask.jsonify({"success": False, "message": "UNAUTHORIZED"})

    database.UpdateSetting(setting_id, setting_value)
    return flask.jsonify({"success": True})