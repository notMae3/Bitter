from wtforms.validators import InputRequired, Regexp, Length, Email
import logging

APP_CONFIG = {
    "CSRF_session_tokens_enabled": False,
    "JWT_max_age_hours": 31 * 24 # 31 days
}

API_CONFIG = {
    "account_password_salt_length": 50,
    "post_fetch_max_results": 5,
    "reply_fetch_max_results": 5,
    "conversation_fetch_max_results": 8,
    "message_fetch_max_results": 10,
    "user_like_count_limit": 100
}

LOGGING = {
    "max_bytes": 25 * 1024, # 25 KiB
    "backup_count": 10,
    "log_level": logging.INFO
}

# field_name is inserted by Bitter using str.format, while %(min)d is inserted later by Flask-WTF using "" % {}
FORM_VALIDATOR_ERROR_MESSAGES = {
    "required": "{field_name} is missing",
    "regexp_alphanum": "{field_name} can only contain alphanumerical characters",
    "regexp_num": "{field_name} can only contain numerical characters",
    "length": "{field_name} must be between %(min)d and %(max)d characters long",
    "email": "Invalid email address"
}

FORM_FIELD_LENGTH_LIMITS = {
    "user_display_name":    {"min": 1, "max": 24},
    "user_username":        {"min": 1, "max": 24},
    "user_email":           {"min": 1, "max": 255},
    "user_password":        {"min": 1, "max": 24},
    "user_id":              {"min": 1, "max": 24},
    "post_body":            {"min": 1, "max": 120},
    "post_id":              {"min": 1, "max": 24},
    "reply_body":           {"min": 1, "max": 120},
    "reply_id":             {"min": 1, "max": 24},
    "conversation_id":      {"min": 1, "max": 24},
    "message_body":         {"min": 1, "max": 120},
    "fetch_content_cursor": {"min": 1, "max": 10},
    "uploads_category":     {"min": 1, "max": 24},
    "uploads_filename":     {"min": 1, "max": 24}
}

FORM_FIELD_REGEX_PATTERNS = {
    "user_display_name": {
        "regex": r"^[A-Za-z0-9_\-@ ]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + ", whitespace and _ - @"
    },
    "user_username": {
        "regex": r"^[A-Za-z0-9_]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + " and _"
    },
    "user_email": {
        "regex": r"^[A-Za-z0-9_\-@\.]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + " and _ - @ ."
    },
    "user_password": {
        "regex": r"^[A-Za-z0-9_\-@\.\,!?]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + " and _ - @ . , ! ?"
    },
    "user_id": {
        "regex": r"^[0-9]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_num"]
    },
    "post_body": {
        "regex": r"^[A-Za-z0-9_\-@\.\,!?:; ]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + ", space and _ - @ . , ! ? : ;"
    },
    "post_id": {
        "regex": r"^[0-9]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_num"]
    },
    "reply_body": {
        "regex": r"^[A-Za-z0-9_\-@\.\,!?:; ]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + ", space and _ - @ . , ! ? : ;"
    },
    "reply_id": {
        "regex": r"^[0-9]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_num"]
    },
    "conversation_id": {
        "regex": r"^[0-9]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_num"]
    },
    "message_body": {
        "regex": r"^[A-Za-z0-9_\-@\.\,!?:; ]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + ", space and _ - @ . , ! ? : ;"
    },
    "fetch_content_cursor": {
        "regex": r"^[0-9]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_num"]
    },
    "uploads_category": {
        "regex": r"^[A-Za-z0-9\.]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + " and .",
    },
    "uploads_filename": {
        "regex": r"^[A-Za-z0-9\.]+$",
        "message": FORM_VALIDATOR_ERROR_MESSAGES["regexp_alphanum"] + " and .",
    }
}

FORM_CONFIG = {
    "user_display_name": {
        "field_name": "Display name",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["user_display_name"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["user_display_name"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["user_display_name"]["message"]
            )
        ],
        "filters": [
            str.strip
        ],
        "default": "",
        "custom_data": {}
    },
    "user_username": {
        "field_name": "Username",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["user_username"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["user_username"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["user_username"]["message"]
            )
        ],
        "filters": [
            str.lower
        ],
        "default": "",
        "custom_data": {}
    },
    "user_email": {
        "field_name": "Email",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["user_email"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["user_email"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["user_email"]["message"]
            ),
            Email(FORM_VALIDATOR_ERROR_MESSAGES["email"])
        ],
        "filters": [
            str.lower
        ],
        "default": "",
        "custom_data": {}
    },
    "user_password": {
        "field_name": "Password",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["user_password"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["user_password"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["user_password"]["message"]
            )
        ],
        "filters": [],
        "default": "",
        "custom_data": {}
    },
    "user_id": {
        "field_name": "user_id",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["user_id"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["user_id"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["user_id"]["message"]
            )
        ],
        "filters": [],
        "default": "",
        "custom_data": {}
    },
    "user_pfp": {
        "field_name": "User profile-picture",
        "validators": [],
        "filters": [],
        "default": None,
        "custom_data": {
            "max_size": 1 * 1024 * 1024, # 1 MiB
        }
    },
    "post_body": {
        "field_name": "Post body",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["post_body"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["post_body"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["post_body"]["message"]
            )
        ],
        "filters": [
            str.strip
        ],
        "default": "",
        "custom_data": {}
    },
    "post_id": {
        "field_name": "post_id",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["post_id"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["post_id"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["post_id"]["message"]
            )
        ],
        "filters": [],
        "default": "",
        "custom_data": {}
    },
    "post_image": {
        "field_name": "Post image",
        "validators": [],
        "filters": [],
        "default": None,
        "custom_data": {
            "max_size": 8 * 1024 * 1024, #8 MiB
        }
    },
    "reply_body": {
        "field_name": "Reply body",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["reply_body"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["reply_body"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["reply_body"]["message"]
            )
        ],
        "filters": [
            str.strip
        ],
        "default": "",
        "custom_data": {}
    },
    "reply_id": {
        "field_name": "reply_id",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["reply_id"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["reply_id"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["reply_id"]["message"]
            )
        ],
        "filters": [],
        "default": "",
        "custom_data": {}
    },
    "conversation_id": {
        "field_name": "conversation_id",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["conversation_id"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["conversation_id"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["conversation_id"]["message"]
            )
        ],
        "filters": [],
        "default": "",
        "custom_data": {}
    },
    "message_body": {
        "field_name": "Message body",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["message_body"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["message_body"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["message_body"]["message"]
            )
        ],
        "filters": [
            str.strip
        ],
        "default": "",
        "custom_data": {}
    },
    "fetch_content_cursor": {
        "field_name": "fetch_content_cursor",
        "validators": [],
        "filters": [],
        "default": None,
        "custom_data": {}
    },
    "uploads_category": {
        "field_name": "Uploads category",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["uploads_category"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["uploads_category"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["uploads_category"]["message"]
            )
        ],
        "filters": [
            str.strip,
            str.lower
        ],
        "default": "",
        "custom_data": {}
    },
    "uploads_filename": {
        "field_name": "Uploads filename",
        "validators": [
            InputRequired(FORM_VALIDATOR_ERROR_MESSAGES["required"]),
            Length(
                **FORM_FIELD_LENGTH_LIMITS["uploads_filename"],
                message = FORM_VALIDATOR_ERROR_MESSAGES["length"]
            ),
            Regexp(
                FORM_FIELD_REGEX_PATTERNS["uploads_filename"]["regex"],
                message = FORM_FIELD_REGEX_PATTERNS["uploads_filename"]["message"]
            )
        ],
        "filters": [
            str.strip,
            str.lower
        ],
        "default": "",
        "custom_data": {}
    },
}
