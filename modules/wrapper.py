import subprocess
import sys

import mysql.connector
import logging
import os
from pathlib import Path
import dotenv
dotenv.load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if sys.version_info.major != 3 and sys.version_info.minor != 11:
    logger.warning(f"[!] SingleCraft is developed and tested under Python 3.11, not {sys.version_info}")

if not Path(Path(__file__).parent.parent / ".env").exists():
    logger.warning("[!] Cannot find .env file, creating it..")
    Path(Path(__file__).parent.parent / ".env").touch()

if not os.getenv("DATABASE_NAME") or not os.getenv("DATABASE_USER") or not os.getenv("DATABASE_PASSWORD") or not os.getenv("DATABASE_HOST") or not os.getenv("DATABASE_PORT"):
    logger.error("[!] Unable to find database credentials from .env file. Please make sure to fill the .env file with the correct database credentials.")
    sys.exit()

logger.info(f"[*] Retrieved database informations from .env file. \n\tDATABASE_HOST: {os.getenv("DATABASE_HOST")}\n\tDATABASE_USER: {os.getenv("DATABASE_USER")}\n\tDATABASE_PASSWORD: {os.getenv("DATABASE_PASSWORD")[0:5]+"***"}\n\tDATABASE_NAME: {os.getenv("DATABASE_NAME")}")

logger.info("[*] Checking database connection..")
try:
    mysql = mysql.connector.connect(
        host=os.getenv("DATABASE_HOST"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
    )
    mysql.close()
except mysql.connector.Error as error:
    logger.warning("[!] Cannot connect to database")
    sys.exit()

logger.info("[*] Database connection successful.")

logger.info("[*] Launching main application..")

subprocess.run([sys.executable, "-m", "flask", "--app", "main", "run", "--debug"], cwd=Path(__file__).parent.parent)
logger.info("[*] SingleCraft was closed. If you think that an issue, please report it on https://github.com/lucachinou/SingleCraft/issues")