from ..config import USER_INPUT_CONFIG
from functools import wraps
from flask import session, Response, request
from werkzeug.datastructures import FileStorage
from pathlib import Path
import flask, re, filetype, json


class DatabaseException(Exception):
    def __init__(self, code) -> None:
        self.code = code

class Redirect(Response):
    """Wrapper for flask.Response used to clarify what type of response a
    function returns
    """
    pass

@wraps(flask.render_template)
def render_template_with_defaults(*args, **kwargs) -> str:
    return flask.render_template(
        *args,
        post_body_max_len = USER_INPUT_CONFIG["post"]["body"]["max_len"],
        post_max_image_size = USER_INPUT_CONFIG["post"]["image"]["max_size"],
        user_is_admin = session.get("is_admin", False),
        **kwargs
    )

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return render_template_with_defaults(
                "login.html",
                username_max_len = USER_INPUT_CONFIG["user"]["username"]["max_len"],
                password_max_len = USER_INPUT_CONFIG["user"]["password"]["max_len"],
                display_name_max_len = USER_INPUT_CONFIG["user"]["display_name"]["max_len"],
                email_max_len = USER_INPUT_CONFIG["user"]["email"]["max_len"]
            )

        return func(*args, **kwargs)
    
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin", False):
            return Response(status=403)

        return func(*args, **kwargs)
    
    return wrapper

def sanitize_user_input(user_input : str, value_category : str, value_key) -> str:
    VALUE_CONFIG = USER_INPUT_CONFIG[value_category][value_key]
    regex_pattern = VALUE_CONFIG["regex"]
    return _sanitize_user_input(user_input, regex_pattern)

def _sanitize_user_input(user_input : str, regex_pattern : str) -> str:
    return re.subn(regex_pattern, "", str(user_input))[0]

def check_user_input_validity(user_input : str | None,
                              value_category : str,
                              value_key : str) -> tuple[str | None, str]:
    VALUE_CONFIG = USER_INPUT_CONFIG[value_category][value_key]

    regex_pattern = VALUE_CONFIG["regex"]
    key_str = VALUE_CONFIG["key_str"]
    max_len = VALUE_CONFIG["max_len"]
    min_len = VALUE_CONFIG["min_len"]
    strip = VALUE_CONFIG["strip"]
    char_limit_str = VALUE_CONFIG["char_limit_str"]

    if not user_input:
        return (user_input, f"{key_str} value is missing")

    if strip:
        user_input = user_input.strip()

    sanitized_user_input = _sanitize_user_input(user_input, regex_pattern)

    # if the new value changed after sanitization
    if sanitized_user_input != user_input:
        return (user_input, f"{key_str} can only contain {char_limit_str}")
    
    # if the new input value is too short or too long
    elif len(sanitized_user_input) < min_len or (max_len < len(sanitized_user_input) and max_len != -1):
        message = f"{key_str} must be"
        message_parts = []

        if min_len > 0:
            message_parts.append(
                f" at least {min_len} character{'s' if min_len > 1 else ''}"
            )
        if max_len > 0:
            message_parts.append(
                f" at most {max_len} character{'s' if max_len > 1 else ''}"
            )
        
        return (user_input, message + " and".join(message_parts))
    
    return (user_input, "")

def handle_user_upload(file : FileStorage,
                       filename : str,
                       value_category : str,
                       value_key : str) -> str | None:
    max_file_size = USER_INPUT_CONFIG[value_category][value_key]["max_size"]

    # dont save the file if it doesnt appear to be an image
    if not filetype.is_image(file.stream):
        return "Invalid image-file content"

    # download the file upto max_size
    file_bytes = file.stream.read(max_file_size)

    # dont save the file if the file content was cut of by the file size limit
    if len(file_bytes) == max_file_size:
        return "File too large"

    # save the file
    filepath = Path(f"uploads/{filename}")
    filepath.write_bytes(file_bytes)

def format_logging_info(response = None, status_code = int) -> str:
    """Submit status_code if there is no response"""

    log_dict = {
        "request": {
            "url": request.url,
            "method": request.method,
            "args": request.args.to_dict(),
            "form": request.form.to_dict(),
            "files": request.files.to_dict(),
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
    
    return f"{status_code if status_code else '-'}: " + json.dumps(log_dict)