from .config import APP_CONFIG
from flask import Flask
from flask_socketio import SocketIO
from flask_wtf import CSRFProtect
from mysql.connector import pooling
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time, os, dotenv, logging

dotenv.load_dotenv()
CWD = Path.cwd()

# setup and config Flask, MySQL and SocketIO
app = Flask(
    __name__,
    template_folder = CWD / "templates",
    static_folder = CWD / "static"
)

app.config.update(
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "SuperSecretAndCoolFlaskSecretKey"),
    UPLOAD_FOLDER = CWD / "uploads",
    WTF_CSRF_ENABLED = APP_CONFIG["CSRF_session_tokens_enabled"]
)

csrf = CSRFProtect(app)

socketio = SocketIO(app)
socket_rooms : dict[int, list[dict[str, str]]] = {}
# ^ {conversation_id : [ {"user_id": user_id, "sid": request.sid}, ]}

db_pool = pooling.MySQLConnectionPool(
    pool_name = "mysql_pool",
    pool_size = os.getenv("DB_POOL_SIZE", 5),
    host = os.getenv("DB_HOST", "localhost"),
    user = os.getenv("DB_USER", "root"),
    password = os.getenv("DB_PASSWORD", ""),
    database = "Bitter"
)

# initialize routes and apis
from . import (
    main_routes,
    error_routes,
    db_api,
    socket_api
)

from .utils import db_utils

def setup_logging() -> None:
    log_dir_path = CWD / "logs"
    log_dir_path.mkdir(exist_ok = True)

    file_handler = RotatingFileHandler(
        log_dir_path / "Bitter.log",
        maxBytes = config.LOGGING["max_bytes"],
        backupCount = config.LOGGING["backup_count"]
    )

    logging.Formatter.converter = time.gmtime
    formatter = logging.Formatter("%(asctime)s+00:00 %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    file_handler.setFormatter(formatter)
    
    file_handler.setLevel(config.LOGGING["log_level"])
    app.logger.setLevel(config.LOGGING["log_level"])
    app.logger.addHandler(file_handler)

    app.logger.info("Logging enabled")


# propegate the Flask socketio run() to Bitter
def run(host: str | None = None,
        port: int | None = None,
        debug: bool = True,
        log_output: bool = ...,
        allow_unsafe_werkzeug: bool = False) -> None:
    """Run the Flask and Flask SocketIO webserver. Effectively a wrapper of ```flask_socketio```'s ```SocketIO.run```.
    """
    setup_logging()

    db_utils.ensure_admin_account_exists()

    app.logger.info("Flask startup")

    socketio.run(
        app = app,
        host = host,
        port = port,
        debug = debug,
        log_output = log_output,
        allow_unsafe_werkzeug = allow_unsafe_werkzeug
    )
