from . import app
from .utils.misc_utils import (
    make_response_with_template,
    format_logging_info,
    make_error_response
)
from mysql.connector.errors import DatabaseError, InterfaceError
from flask import redirect, url_for, flash, request
from werkzeug.exceptions import HTTPException

@app.errorhandler(DatabaseError)
@app.errorhandler(InterfaceError)
def on_database_error(_error : DatabaseError | InterfaceError) -> None:
    # log database exceptions here
    app.logger.error(format_logging_info())

    # tell the user about the error
    is_api_request = str(request.url_rule).startswith("/api/")
    if is_api_request:
        return make_error_response("Database error", 503)
    else:
        flash("Error - Database error")
        return redirect(url_for("timeline"))

@app.errorhandler(HTTPException)
def on_http_exception(error : HTTPException) -> None:
    # log general uncaught http exceptions here

    # tell the user about the error
    is_api_request = str(request.url_rule).startswith("/api/")
    if is_api_request:
        return make_error_response(error.description, error.code)
    else:
        return make_response_with_template(
            "error.jinja2",
            status_code = error.code,
            status_str = error.description
        )

@app.errorhandler(Exception)
def on_exception(_error : Exception) -> None:
    # log general app related exceptions here. if this point is reached then
    # there's a critical bug somewhere

    app.logger.critical(format_logging_info())
    
    # tell the user about the error
    is_api_request = str(request.url_rule).startswith("/api/")
    if is_api_request:
        return make_error_response("A critical system error has occured. Sorry about that", 500)
    else:
        flash("Error - A critical system error has occured. Sorry about that")
        return redirect(url_for("timeline"))
