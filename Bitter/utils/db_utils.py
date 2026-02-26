from .. import app, db_pool
from ..config import API_CONFIG
from .misc_utils import (
    login_required,
    use_only_expected_kwargs,
    check_user_input_validity
)
from contextlib import closing
from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.cursor import MySQLCursorDict
from functools import wraps
import os, typing, json
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection() -> PooledMySQLConnection:
    """Attempt to get a connection to the MySQL database. Return a 

    Returns:
        PooledMySQLConnection: A connection instance to the database
    """
    return db_pool.get_connection()

def uses_db_connection(func) -> typing.Callable:
    """Decorator that gets a database connection and passes it to the decorated function as parameter values "db_conn"
    (PooledMySQLConnection) and "db_cursor" (MySQLCursorDict). The decorated function may, but is not required to,
    expect either of the "db_conn" and "db_cursor" parameters. The database connection and cursor are automatically
    closed when out of scope.

    Returns:
        Any: The returned value from the decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor(dictionary=True)) as cursor:
                return func(*args, **kwargs, db_conn = conn, db_cursor = cursor)
    
    return wrapper

@uses_db_connection
def ensure_admin_account_exists(db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> None:
    # extract and sanitize user inputs
    password = os.getenv("ADMIN_ACCOUNT_PASSWORD", "pass123")
    password, error_message = check_user_input_validity(password, "user_password", return_response = False)
    if error_message:
        raise ValueError(f"Malformed admin account password. Password: '{password}', error message: '{error_message}'")
    
    hashed_password = generate_password_hash(
        password,
        salt_length = API_CONFIG["account_password_salt_length"]
    )

    # fetch the hashed password of the admin account if it exists
    db_cursor.execute(
        f"""
        SELECT password FROM users WHERE username = "admin"
        """
    )

    admin_account = db_cursor.fetchone() or {}

    if admin_account:
        old_hashed_password = admin_account.get("password")
        password_has_changed = not check_password_hash(old_hashed_password, password)

        # update the admin account's passowrd if the admin account exists and the password in env doesnt match the admin
        # account's current password
        if password_has_changed:
            # change the password
            db_cursor.execute(
                f"""
                UPDATE users SET password = '{hashed_password}' WHERE username = 'admin'
                """
            )
    
    else:
        # add the admin account since it doesnt exist
        db_cursor.execute(
            # add the new admin account. there will never be a username conflict with username "admin" since this runs
            # before users have access to the db
            f"""
            INSERT INTO users (username, display_name, password, is_admin)
            VALUES ('admin', 'Admin', '{hashed_password}', true)
            """
        )

    db_conn.commit()

    app.logger.info("Ensured primary admin account exists")

@login_required
@uses_db_connection
@use_only_expected_kwargs
def fetch_shared_conversation_id(username : str, current_user : dict, db_cursor : MySQLCursorDict) -> dict:
    # extract and sanitize user inputs
    username, error_message = check_user_input_validity(username, "user_username", return_response = False)
    if error_message:
        return {"error": error_message}

    user_id : int = current_user["user_id"]

    # fetch the conversation
    db_cursor.execute(
        # return the conversation id of the conversation that the currenly logged in user and the inputted username
        # share, if it exists
        f"""
        WITH user_id_2 AS (
            SELECT user_id FROM users
            WHERE username = '{username}'
        )

        SELECT convos.conversation_id
        FROM conversations convos
        LEFT JOIN user_id_2
            ON 1
        WHERE (
            ({user_id}, user_id) = (convos.user_1_id, convos.user_2_id) OR 
            (user_id, {user_id}) = (convos.user_1_id, convos.user_2_id)
        )
        """
    )

    conversation = db_cursor.fetchone() or {}

    if not conversation:
        return {"error": "Conversation ID doesn't exist"}

    return conversation

@login_required
@uses_db_connection
def create_message(recipient_username : str,
                   message_body : str,
                   current_user : dict,
                   db_conn : PooledMySQLConnection,
                   db_cursor : MySQLCursorDict) -> dict:
    # extract and sanitize user inputs
    recipient_username, error_message = check_user_input_validity(recipient_username, "user_username", return_response = False)
    if error_message:
        return {"error": error_message}
    
    message_body, error_message = check_user_input_validity(message_body, "message_body", return_response = False)
    if error_message:
        return {"error": error_message}
    
    user_id : int = current_user["user_id"]
    date_created = datetime.now(timezone.utc).timestamp() // 1 # floor to seconds
    
    # ensure that the inputted user exists and that a conversation can be created with them and the current user
    db_cursor.execute(
        # retrieve the user id corresponding to the inputted username, if one exist. also retreive whether a conversation
        # exists with both the user id of the inputted username and the user id of the currently logged in user
        f"""
        SELECT
            user_id AS "user_id",
            COALESCE(convo_as_u1.conversation_id, convo_as_u2.conversation_id) AS "conversation_id"
        FROM users
        LEFT JOIN conversations convo_as_u1 ON (user_id, {user_id}) = (convo_as_u1.user_1_id, convo_as_u1.user_2_id)
        LEFT JOIN conversations convo_as_u2 ON ({user_id}, user_id) = (convo_as_u2.user_1_id, convo_as_u2.user_2_id)
        WHERE username = '{recipient_username}'
        """
    )

    user_query = db_cursor.fetchone() or {}
    conversation_id = user_query.get("conversation_id")

    # return errors for a variety of cases
    if not user_query:
        return {"error": f"User '{recipient_username}' doesn't exist"}

    elif not conversation_id:
        return {"error": "A conversation with that user doesn't exist"}
    
    elif user_id == user_query.get("user_id"):
        return {"error": "Can't message yourself"}

    # create the message in the db
    db_cursor.execute(
        # create a new message row with the inputted values
        f"""
        INSERT INTO messages (author_id, body, date_created, conversation_id)
        VALUES ({user_id}, '{message_body}', {date_created}, {conversation_id})
        """
    )

    db_cursor.execute(
        # fetch the new message
        f"""
        SELECT * FROM messages
        ORDER BY message_id DESC
        LIMIT 1
        """
    )

    new_message = db_cursor.fetchone() or {}
    db_conn.commit()

    app.logger.info(f"Created message {json.dumps(new_message)}")

    return new_message

@uses_db_connection
def mark_message_as_seen(safe_message_id : int, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> None:
    # update message row
    db_cursor.execute(
        # update the seen value of the message with the inputted message id
        f"""
        UPDATE messages SET seen = true
        WHERE message_id = {safe_message_id}
        """
    )

    db_conn.commit()

@login_required
@uses_db_connection
def fetch_messages(recipient_username : str,
                   cursor : str,
                   current_user : dict,
                   db_conn : PooledMySQLConnection,
                   db_cursor : MySQLCursorDict) -> dict | list:
    # extract and sanitize user inputs
    recipient_username, error_message = check_user_input_validity(recipient_username, "user_username", return_response = False)
    if error_message:
        return {"error": error_message}
    
    cursor, error_message = check_user_input_validity(cursor, "fetch_content_cursor", return_response = False)
    if error_message:
        return {"error": error_message}

    cursor = int(cursor)
    user_id : int = current_user["user_id"]

    # fetch messages
    db_cursor.execute(
        # return all messages with the conversation id of the conversation that the currently logged in user and the
        # inputted recipient username share, if it exists
        f"""
        WITH user_id_2 AS (
            SELECT user_id FROM users
            WHERE username = '{recipient_username}'
        ), relevant_convo AS (
            SELECT conversation_id FROM conversations
            LEFT JOIN user_id_2 ON 1
            WHERE (
                ({user_id}, user_id_2.user_id) = (conversations.user_1_id, conversations.user_2_id) OR
                (user_id_2.user_id, {user_id}) = (conversations.user_1_id, conversations.user_2_id)
            )
        )

        SELECT
            messages.*,
            ROW_NUMBER() OVER (ORDER BY messages.message_id ASC) as "message_idx"
        FROM messages
        INNER JOIN relevant_convo
        	ON messages.conversation_id = relevant_convo.conversation_id
        {f"WHERE messages.message_id < {cursor}" if cursor != 0 else ""}
        ORDER BY messages.message_id DESC
        LIMIT {API_CONFIG["message_fetch_max_results"]}
        """
    )

    messages = db_cursor.fetchall() or []

    db_cursor.execute(
        # for each message in the previous query who's author isn't the currently logged in user, mark it as seen
        f"""
        UPDATE messages all_messages
        INNER JOIN (
            WITH user_id_2 AS (
                SELECT user_id FROM users
                WHERE username = '{recipient_username}'
            ), relevant_convo AS (
                SELECT conversation_id FROM conversations
                LEFT JOIN user_id_2 ON 1
                WHERE (
                    ({user_id}, user_id_2.user_id) = (conversations.user_1_id, conversations.user_2_id) OR
                    (user_id_2.user_id, {user_id}) = (conversations.user_1_id, conversations.user_2_id)
                )
            )

            SELECT
                messages.*,
                ROW_NUMBER() OVER (ORDER BY messages.message_id ASC) as "message_idx"
            FROM messages
            INNER JOIN relevant_convo
                ON messages.conversation_id = relevant_convo.conversation_id
            {f"WHERE messages.message_id < {cursor}" if cursor != 0 else ""}
            ORDER BY messages.message_id DESC
            LIMIT {API_CONFIG["message_fetch_max_results"]}
        ) AS relevant_messages
            ON (
                all_messages.message_id = relevant_messages.message_id AND
                relevant_messages.author_id != {user_id}
            )
        SET all_messages.seen = true
        """
    )

    db_conn.commit()

    # add "origin" data, which for each message specifies whether the currently logged in user sent or recieved the
    # message
    for message in messages:
        from_current_user = message["author_id"] == user_id
        message["origin"] = "sent" if from_current_user else "received"

    return messages
