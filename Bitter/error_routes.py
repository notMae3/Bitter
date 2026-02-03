from . import app
from .utils.misc_utils import (
    render_template_with_defaults,
    format_logging_info,
    DatabaseException
)
from flask import redirect, url_for, request, Response
from werkzeug.exceptions import HTTPException
import traceback

@app.errorhandler(DatabaseException)
def on_database_error(error : DatabaseException):
    app.logger.error(format_logging_info(status_code = error.code))
    return redirect(url_for("timeline"))

@app.errorhandler(HTTPException)
def on_http_exception(error : HTTPException):
    # log general uncaught http exceptions here. see after_request in
    # main_routes.py for caught errors

    # the error.get_response() is auto generated and doesnt contain any
    # interesting data, therefore dont log it
    app.logger.info(format_logging_info(status_code=error.code))

    return render_template_with_defaults(
        "error.html",
        status_code = error.code,
        status_str = error.description
    )

@app.errorhandler(Exception)
def on_exception(error : Exception):
    # log general app related exceptions here. if this point is reached then
    # theres a critical bug somewhere

    error_str = traceback.format_exc().encode('unicode_escape').decode("utf-8")
    app.logger.critical(error_str)
    
    return redirect(url_for("timeline"))