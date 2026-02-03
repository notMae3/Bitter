from functools import wraps
from flask import Flask
from flask_socketio import SocketIO
from mysql.connector import pooling
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os, dotenv, logging

dotenv.load_dotenv()

# setup and config Flask, MySQL and SocketIO
app = Flask(
    __name__,
    template_folder = Path.cwd() / "templates",
    static_folder = Path.cwd() / "static"
)

app.config.update(
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "pass123"),
    SESSION_PERMANENT = False,
    SESSION_TYPE = "filesystem",
    UPLOAD_FOLDER = Path.cwd() / "uploads"
)

socketio = SocketIO(app)
socket_rooms : dict[int, list[dict[str, int | str]]] = {}
# ^ {conversation_id : [{"user_id": user_id, "sid": request.sid},]}

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
    socket_api,
    config
)

def setup_logging():
    log_dir_path = Path.cwd() / "logs"
    if not log_dir_path.exists():
        log_dir_path.mkdir()

    file_handler = RotatingFileHandler(
        log_dir_path / "Bitter.log",
        maxBytes = config.LOGGING["max_bytes"],
        backupCount = config.LOGGING["backup_count"]
    )

    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    ))
    
    file_handler.setLevel(config.LOGGING["log_level"])
    app.logger.setLevel(config.LOGGING["log_level"])
    app.logger.addHandler(file_handler)

    app.logger.info("Flask startup")


# propegate the Flask socketio run() to Bitter
@wraps(socketio.run)
def run(*args, **kwargs):
    """Run the Flask and Flask SocketIO webserver. The first argument, app, is not expected.
    """
    # setup logging
    setup_logging()

    # ensure the primary admin account exists
    db_api.ensure_admin_account_exists()

    kwargs["app"] = app
    socketio.run(*args, **kwargs)
