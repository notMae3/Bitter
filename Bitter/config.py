import logging

USER_INPUT_CONFIG = {
    "user": {
        "display_name": {
            "regex": r"[^A-Za-z0-9_\-@ ]",
            "min_len": 1,
            "max_len": 24,
            "strip": True,
            "char_limit_str": "alphanumerical characters, whitespace and _ - @",
            "key_str": "Display name"},
        "username": {
            "regex": r"[^A-Za-z0-9_]",
            "min_len": 1,
            "max_len": 24,
            "strip": False,
            "char_limit_str": "alphanumerical characters and _",
            "key_str": "Username"},
        "email": {
            "regex": r"[^A-Za-z0-9_\-@\.]",
            "min_len": 1,
            "max_len": 255,
            "strip": False,
            "char_limit_str": "alphanumerical characters and _ - @ .",
            "key_str": "Email"},
        "password": {
            "regex": r"[^A-Za-z0-9_\-@\.\,!?]",
            "min_len": 1,
            "max_len": 24,
            "strip": False,
            "char_limit_str": "alphanumerical characters and _ - @ . , ! ?",
            "key_str": "Password"},
        "pfp": {
            "max_size": 5 * 1024 * 1024, # 5MB
        }
    },
    "post": {
        "body": {
            "regex": r"[^A-Za-z0-9_\-@\.\,!? ]",
            "min_len": 1,
            "max_len": 120,
            "strip": True,
            "char_limit_str": "alphanumerical characters, space and _ - @ . , ! ?",
            "key_str": "Post body"
        },
        "image": {
            "max_size": 16 * 1024 * 1024, #16MB
        },
        "post_id": {
            "regex": r"[^0-9]",
            "min_len": 1,
            "max_len": 10,
            "strip": False,
            "char_limit_str": "numerical characters",
            "key_str": "post_id"
        }
    },
    "reply": {
        "body": {
            "regex": r"[^A-Za-z0-9_\-@\.\,!? ]",
            "min_len": 1,
            "max_len": 120,
            "strip": True,
            "char_limit_str": "alphanumerical characters, space and _ - @ . , ! ?",
            "key_str": "Reply body"
        },
        "reply_id": {
            "regex": r"[^0-9]",
            "min_len": 1,
            "max_len": 10,
            "strip": False,
            "char_limit_str": "numerical characters",
            "key_str": "reply_id"
        }
    },
    "conversation": {
        "conversation_id": {
            "regex": r"[^0-9]",
            "min_len": 1,
            "max_len": 10,
            "strip": False,
            "char_limit_str": "numerical characters",
            "key_str": "conversation_id"
        }
    },
    "message": {
        "body": {
            "regex": r"[^A-Za-z0-9_\-@\.\,!? ]",
            "min_len": 1,
            "max_len": 120,
            "strip": True,
            "char_limit_str": "alphanumerical characters, space and _ - @ . , ! ?",
            "key_str": "Message body"
        },
    },
    "fetch_content": {
        "cursor": {
            "regex": r"[^0-9]",
            "min_len": 1,
            "max_len": 10,
            "strip": False,
            "char_limit_str": "numerical characters",
            "key_str": "Cursor"
        }
    }
}

API_CONFIG = {
    "account_password_salt_length": 50, # WARNING - CHANGING INVALIDATES ALL USER PASSWORDS
    "post_fetch_max_results": 5,
    "reply_fetch_max_results": 5,
    "conversation_fetch_max_results": 8,
    "message_fetch_max_results": 10,
    "user_like_count_limit": 100
}

LOGGING = {
    "max_bytes": 25 * 1024, # 25 KB
    "backup_count": 10,
    "log_level": logging.INFO
}