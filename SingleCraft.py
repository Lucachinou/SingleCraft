import datetime
import os
from pathlib import Path

import flask
import logging
import dotenv
import sys

import blueprints.BlueprintsManager as Blueprints
from modules import database

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

if sys.version_info.major != 3 and sys.version_info.minor != 11:
    logger.warning(f"[!] SingleCraft is developed and tested under Python 3.11, not {sys.version_info}")

logger.warning("[!] SingleCraft is in early development, expect bugs and crashes. Please report them on the GitHub repository.")
logger.warning("[*] To launch SingleCraft in the best conditions, please execute 'pip install -r requirements.txt' (And install Argon2 at the first launch avoid older accounts being locked)")

if not Path(Path(__file__).parent.parent / ".env").exists():
    logger.warning("[!] Cannot find .env file, creating it..")
    Path(Path(__file__).parent.parent / ".env").touch()

if not os.getenv("DATABASE_NAME") or not os.getenv("DATABASE_USER") or not os.getenv("DATABASE_PASSWORD") or not os.getenv("DATABASE_HOST") or not os.getenv("DATABASE_PORT"):
    logger.error("[!] Unable to find database credentials from .env file. Please make sure to fill the .env file with the correct database credentials.")
    sys.exit()

logger.info(f"[*] Retrieved database informations from .env file. \n\tDATABASE_HOST: {os.getenv('DATABASE_HOST')}\n\tDATABASE_USER: {os.getenv('DATABASE_USER')}\n\tDATABASE_PASSWORD: {os.getenv('DATABASE_PASSWORD')[0:5]+'***'}\n\tDATABASE_NAME: {os.getenv('DATABASE_NAME')}")

logger.info("[*] Checking database connection..")
try:
    mysql = database.get_db_connection(os.getenv("DATABASE_NAME"))
    mysql.close()
except RuntimeError as error:
    logger.warning("[!] Cannot connect to database")
    sys.exit()

logger.info("[*] Database connection successful.")

if not database.DatabaseUpdated():
    database.SetupDatabase()

app = flask.Flask(__name__)


Blueprints.register_blueprints(app)
app.run(host="0.0.0.0", port=5500, debug=False)