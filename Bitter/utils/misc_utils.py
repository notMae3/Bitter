from .. import app
from ..config import (
    FORM_CONFIG,
    APP_CONFIG,
    FORM_FIELD_REGEX_PATTERNS,
    FORM_FIELD_LENGTH_LIMITS,
    FORM_VALIDATOR_ERROR_MESSAGES
)
from ..forms import LoginForm, SignupForm, PostCreationForm
from .socket_utils import emit_error_response
from functools import wraps
from flask import Response, request, make_response, jsonify
from flask_wtf import FlaskForm
from werkzeug.datastructures import FileStorage
from pathlib import Path
import flask, re, filetype, json, jwt, traceback, typing
from datetime import datetime, timezone, timedelta
from inspect import getfullargspec


def get_current_user() -> dict | None:
    """Decode the JWT token stored in the access_token cookie value, if it exists

    Returns:
        dict | None: Decoded JWT as a dict, or None if something went wrong
    """
    # fetch the JWT access token from cookies and return None if its not present
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        return None

    # declare a variable to which the JWT access token contents inserted, if any content is present
    jwt_dict = {}

    # try to parse the JWT access token and return None if parsing failes or the access token is outdated
    try:
        jwt_dict = jwt.decode(
            jwt_token,
            key = app.config["SECRET_KEY"],
            algorithms = ["HS256"]
        )
    except:
        return None
    
    # return None if the jwt access token is somehow malformed, or in other words doesnt include a truthly user_id value
    if not jwt_dict.get("user_id"):
        return None

    # verify user_id value validity. the JWT access token is very unlikely to be compromised but to protect from
    # SQL-injection the user_id value is checked anyway
    user_id, error_message = check_user_input_validity(str(jwt_dict["user_id"]), "user_id", return_response = False)
    if error_message:
        return None

    # create a current_user object and insert he values from the parsed JWT access token
    current_user = {
        "user_id": int(user_id),
        "is_admin": bool(jwt_dict.get("is_admin", False))
    }

    return current_user


def make_response_with_template(template_name : str,
                                is_admin : bool = False,
                                status_code : int = 200,
                                **kwargs) -> Response:
    # render the inputted template name and add some default arguments
    template = flask.render_template(
        template_name,
        post_creation_form = PostCreationForm(),
        post_max_image_size = FORM_CONFIG["post_image"]["custom_data"]["max_size"],
        user_is_admin = is_admin,
        **kwargs
    )

    return make_response(template, status_code)

def make_json_response(object : list | dict, code : int) -> Response:
    return make_response(jsonify(object), code)

def make_error_response(error : str, code : int) -> Response:
    return make_response(jsonify({"errors": [error]}), code)

def _failed_login_required_return_value(is_api_request : bool, is_socket_request : bool) -> Response | None:
    if is_api_request:
        return make_error_response("Missing access token", 401)
    
    if is_socket_request:
        emit_error_response("Missing access token")
        return

    # load the login template if this is neither an api request or a socket request
    resp = make_response_with_template(
        "login.jinja2",
        login_form = LoginForm(),
        signup_form = SignupForm(),
        status_code = 401
    )

    # remove the access token from the client if its present in the request cookie but malformed or outdated
    if "access_token" in request.headers:
        append_removal_of_access_token_to_response(resp)
    
    return resp

def login_required(func) -> typing.Callable:
    """Decorator that ensures the request contains a valid JWT token and user_id. The wrapped fucntion may include a
    key-word argument "current_user" but is not required to. The "current_user" value is a dictionary like the
    following: {"user_id": str, "is_admin": bool}.

    Returns:
        Any: Either a "Missing access token" 401 response, if the jwt access token is missing and the request is to
             an api route. If the jwt access token is missing and the request is not to an api route, return a
             render of the login page. If the jwt access token is valid and contains a user_id then return the
             result of the wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        is_api_request = request.path.startswith("/api")
        is_socket_request = request.path.startswith("/socket.io")
        current_user = get_current_user()

        # return some form of unauthorized response if the current user is not logged in
        if not current_user:
            return _failed_login_required_return_value(is_api_request, is_socket_request)

        return func(*args, **kwargs, current_user = current_user)
    
    return wrapper

def admin_required(func) -> typing.Callable:
    """Decorator that ensures the request contains a valid JWT token, user_id and a True is_admin value. The decorated
    fucntion may include a key-word argument "current_user" but is not required to. The "current_user" value is a
    dictionary like the following: {"user_id": str, "is_admin": bool}.
    
    This decorator performs the same check as login_required, as well as an "is admin?" check.

    Returns:
        Any: Either a "Missing access token" 401 response, if the jwt access token is missing and the request is to
             an api route. If the jwt access token is missing and the request is not to an api route, return a
             render of the login page. If the jwt access token is valid and contains a user_id then return the
             result of the decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        is_api_request = request.path.startswith("/api")
        is_socket_request = request.path.startswith("/socket.io")
        current_user = get_current_user()

        # return some form of unauthorized response if the current user is not logged in
        if not current_user:
            return _failed_login_required_return_value(is_api_request, is_socket_request)
        
        # return some form of unauthorized response if the current user is not an admin
        if not current_user["is_admin"]:
            if is_socket_request:
                emit_error_response("Unauthorized")
                return
            
            return make_error_response(f"User '{current_user['user_id']}' is not an admin", 401)

        return func(*args, **kwargs, current_user = current_user)
    
    return wrapper

def use_only_expected_kwargs(func) -> typing.Callable:
    """Decorator that filters the inputted keyword-arguments to ensure that only expected arguments are passed to the
    decorated function. This enables functions to accept only the neccessary arguments and not all arguments produced
    by decorators such as login_required, admin_required and uses_db_connection.
    
    Returns:
        Any: The returned value from the wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        # filter the inputted kwargs by what the decorated function expects
        expected_args = getfullargspec(func).args
        kwargs = {key:val for key,val in kwargs.items() if key in expected_args}

        return func(*args, **kwargs)
    
    return wrapper

def renews_access_token(func) -> typing.Callable:
    """Decorator that renews the JWT access token when the decorated function is called. This decorator is meant to be
    used on a function dedicated as a Flask route which returns a Flask Response. If this decorator is used it must come
    after a decorator that ensures the that the current user is logged-in.
    
    Returns:
        Any: The returned value from the wrapped function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        if "current_user" not in kwargs:
            raise KeyError(f"Function to renew access token didn't receive the 'current_user' parameter. kwargs: {kwargs}")
        
        # get the values for the current user
        current_user = kwargs["current_user"]
        user_id = current_user["user_id"]
        is_admin = current_user["is_admin"]

        # call the decorated function and append a new JWT access token to the response
        response = func(*args, **kwargs)
        append_access_token_to_response(user_id, is_admin, response)
        
        return response
    
    return wrapper

def validates_CSRF_form(form_type : type[FlaskForm]) -> typing.Callable:
    """Decorator generator which returns a decorator that validates the form data passed in the request. The validation
    is done using the inputted form_type. Only meant to be used for API routes. The parsed form is then passed to the
    decorated function.

    Args:
        form_type (type[FlaskForm]): A type of FlaskForm to perform the form validation with.
    
    Returns:
        callable: The generated decorator function
    """

    def _validates_CSRF_form(func) -> typing.Callable:
        """Decorator that validates the form data passed in the request. Only meant to be used for API routes. The
        parsed form is then passed to the decorated function.
        
        Returns:
            Response: Error response if the inputted form isn't valid
            Any: The returned value from the wrapped function
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> typing.Any:
            form = form_type()
            form_valid = form.validate_on_submit()
            
            # return error response if the form is invalid
            if not form_valid:
                return make_json_response(form.errors, 400)

            return func(*args, **kwargs, form = form)
        
        return wrapper

    return _validates_CSRF_form

def check_user_input_validity(user_input : str | None,
                              value_key : str,
                              return_response = True) -> tuple[str | None, str | Response | None]:

    def format_error(error_message : str, field_name : str, return_response : bool) -> str | Response:
        error_message = error_message.format(field_name = field_name)

        if return_response:
            return make_error_response(error_message, 400)
        
        return error_message

    # fetch the config values for the current value
    field_name = FORM_CONFIG[value_key]["field_name"]
    missing_error_message = FORM_VALIDATOR_ERROR_MESSAGES["required"]
    regex_pattern = FORM_FIELD_REGEX_PATTERNS[value_key]["regex"]
    regex_error_message = FORM_FIELD_REGEX_PATTERNS[value_key]["message"]
    length_limits = FORM_FIELD_LENGTH_LIMITS[value_key]
    length_error_message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
    filters = FORM_CONFIG[value_key]["filters"]

    # if the user input is missing or an empty string
    if not user_input:
        # format the error and return it along with the user input
        error = format_error(missing_error_message, field_name, return_response)
        return (user_input, error)

    # apply the filters defined in config
    for func in filters:
        user_input = func(user_input)

    # if the user_input doesnt match the required regular expression
    if not re.match(regex_pattern, user_input):
        # format the error and return it along with the user input
        error = format_error(regex_error_message, field_name, return_response)
        return (user_input, error)
    
    # if the sanitized user input value is too short or too long
    user_input_too_short = len(user_input) < length_limits["min"]
    user_input_too_long = len(user_input) > length_limits["max"]
    if user_input_too_short or user_input_too_long:        
        # format the error and return it along with the user input
        error = format_error(length_error_message % length_limits, field_name, return_response)
        return (user_input, error)
    
    return (user_input, None)

def handle_user_upload(file : FileStorage,
                       filename : str,
                       image_type : str) -> Response | None:
    max_file_size = int(FORM_CONFIG[image_type]["custom_data"]["max_size"])
            
    # dont save the file if it doesnt appear to be an image
    if not filetype.is_image(file.stream):
        return make_error_response("Invalid image-file content", 415)

    # download max_file_size bytes of the inputted image
    file_bytes = file.stream.read(max_file_size)

    # dont save the file if the file content was cut of by the file-size limit
    if len(file_bytes) == max_file_size:
        return make_error_response("File too large", 400)

    # save the file
    filepath = Path(f"uploads/{filename}")
    filepath.write_bytes(file_bytes)

def format_logging_info(response = None, status_code : int | str = "") -> str:
    """Submit status_code if there is no response"""

    log_dict = {
        "request": {
            "url": request.url,
            "method": request.method,
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "files": list(request.files.to_dict().keys()),
            "body": request.get_data(as_text = True),
        }
    }

    if response:
        log_dict["response"] = {
            "content": response.get_data(True),
            "content_length": response.content_length,
            "status_code": response.status_code
        }

        status_code = response.status_code
    
    error_traceback = traceback.format_exc()
    log_dict["traceback"] = error_traceback
    
    return f"{status_code if status_code else '-'}: " + json.dumps(log_dict)

def append_access_token_to_response(user_id : str, is_admin : bool, response : Response) -> None:
    """Generate a JWT access token and attach it to the inputted response as a cookie

    Args:
        user_id (str): user id
        is_admin (bool): whether the user is an admin
        response (Response): The response to attach the JWT access token to as a cookie
    """

    max_age = timedelta(hours = APP_CONFIG["JWT_max_age_hours"])
    issued_at = datetime.now(timezone.utc)
    expires = issued_at + max_age

    jwt_token = jwt.encode(
        payload = {"user_id": user_id,
                   "is_admin": is_admin,
                   "iat": issued_at,
                   "exp": expires},
        key = app.config["SECRET_KEY"],
        algorithm = "HS256"
    )

    response.set_cookie(
        "access_token",
        jwt_token,
        max_age = max_age,
        expires = expires,
        path = "/",
        secure = True,
        httponly = True,
        samesite = "Strict"
    )

    app.logger.info(f"JWT access token issued for user id '{user_id}' which expires {expires}")

def append_removal_of_access_token_to_response(response : Response) -> None:
    response.delete_cookie(
        "access_token",
        path = "/",
        secure = True,
        httponly = True,
        samesite = "Strict"
    )
