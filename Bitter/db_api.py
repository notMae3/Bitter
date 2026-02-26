from . import app, CWD
from .forms import (
    LoginForm,
    SignupForm,
    UpdateProfileForm,
    PostCreationForm,
    ReplyCreationForm,
    ConversationCreationForm,
    LikePostForm,
    UnlikePostForm,
    DeletePostForm,
    DeleteReplyForm
)
from .utils.misc_utils import (
    check_user_input_validity,
    handle_user_upload,
    login_required,
    admin_required,
    use_only_expected_kwargs,
    validates_CSRF_form,
    append_access_token_to_response,
    make_json_response,
    make_error_response
)
from .utils.db_utils import uses_db_connection
from flask import (
    request,
    send_file,
    send_from_directory,
    Response
)
from .config import API_CONFIG
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from mysql.connector.pooling import PooledMySQLConnection
from mysql.connector.cursor import MySQLCursorDict
from datetime import datetime, timezone
import os, json

@app.route("/api/uploads", methods = ["GET"])
@app.route("/api/uploads/<category>", methods = ["GET"])
@app.route("/api/uploads/<category>/<filename>", methods = ["GET"])
@login_required
@use_only_expected_kwargs
def uploads(category = None, filename = None) -> Response:
    if not category or not filename:
        return make_error_response("Resource not found", 404)

    safe_path = CWD / app.config["UPLOAD_FOLDER"] / secure_filename(category) / secure_filename(filename)
    
    if safe_path.exists():
        resp = send_file(safe_path, "image/*")

        # add the files last modified data to the response
        last_modified_time = safe_path.stat().st_mtime
        resp.last_modified = datetime.fromtimestamp(last_modified_time).astimezone()

    # send the default user pfp if the requested user pfp doesnt exist
    elif category == "user-pfps":
        resp = send_from_directory(app.static_folder, path="img/default_user_pfp.png")
        resp.last_modified = datetime.now(timezone.utc)

    else:
        resp = make_error_response("Resource not found", 404)
    
    # add anti-caching headers if the provided resource is a user profile-picture since profile-pictures may change
    if category == "user-pfps":
        resp.headers.set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0")
        resp.headers.set("Pragma", "no-cache")
    
    return resp

@app.route("/api/login", methods = ["POST"])
@uses_db_connection
@validates_CSRF_form(LoginForm)
@use_only_expected_kwargs
def login(form : LoginForm, db_cursor : MySQLCursorDict) -> Response:
    input_username = form.username.data
    input_password = form.password.data

    # fetch the stored password and check if the inputted password is correct
    db_cursor.execute(
        # get user id and password for the user that has the inputted username
        f"""
        SELECT user_id, password, is_admin FROM users
        WHERE username = '{input_username}'
        """
    )

    user_query = db_cursor.fetchone() or {}
    
    if not user_query:
        return make_error_response(f"User '{input_username}' doesn't exist", 404)
    
    hashed_password = user_query.get("password", "")
    correct_password = check_password_hash(hashed_password, input_password)

    if not correct_password:
        return make_error_response(f"Incorrect password for user '{input_username}'", 401)

    # format the Response and attach a JWT access token to it
    user_id = user_query.get("user_id")
    is_admin = user_query.get("is_admin") == 1

    resp = Response("Login successful", 200, mimetype = "text/plain")
    append_access_token_to_response(user_id, is_admin, resp)

    app.logger.info(f"User id '{user_id}' logged in")

    return resp

@app.route("/api/signup", methods = ["POST"])
@validates_CSRF_form(SignupForm)
@uses_db_connection
def signup(form : SignupForm, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    display_name = form.display_name.data
    username = form.username.data
    email = form.email.data
    password = form.password.data

    # check if either username of email is unavailable
    db_cursor.execute(
        # select the first value, either username of email, that already exists in the users table
        f"""
        SELECT 
            COALESCE(
                (SELECT username FROM users WHERE username = '{username}'),
                (SELECT email FROM users WHERE email = '{email}')
            ) as result
        """
    )

    # return a conflict error if either the username or email value is a duplicate
    duplicate_value = (db_cursor.fetchone() or {}).get("result")
    if duplicate_value != None:
        unavailable_column = "Username" if duplicate_value == username else "Email"
        return make_error_response(f"{unavailable_column} '{duplicate_value}' is unavailable", 409)

    # generate the password hash and update db
    hashed_password = generate_password_hash(
        password,
        salt_length = API_CONFIG["account_password_salt_length"]
    )

    db_cursor.execute(
        # create a new row in users with the inputted values
        f"""
        INSERT INTO users (username, display_name, email, password) 
        VALUES ('{username}', '{display_name}', '{email}', '{hashed_password}')
        """
    )
    db_conn.commit()

    # dont log the plaintext password
    account_creation_object = {
        "display_name": display_name,
        "username": username,
        "email": email
    }
    app.logger.info(f"Created account with values {json.dumps(account_creation_object)}")

    return Response(f"Successfully created account {json.dumps(account_creation_object)}", status = 201)

@app.route("/api/update-profile", methods = ["PUT"])
@login_required
@validates_CSRF_form(UpdateProfileForm)
@uses_db_connection
def update_profile(current_user : dict, form : UpdateProfileForm, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # figure out what the user wants to update
    request_includes_display_name = form.display_name.data != ""
    request_includes_pfp = isinstance(form.pfp.data, FileStorage) and form.pfp.data.filename != ""

    updated_display_name = False
    updated_pfp = False

    user_id : int = current_user["user_id"]

    # if the user wants to update their display name
    if request_includes_display_name:
        # extract and sanitize user inputs
        display_name = form.display_name.data

        # update db
        db_cursor.execute(
            # update the display name of the user who's user id is the inputted
            # user id
            f"""
            UPDATE users SET display_name = '{display_name}' WHERE user_id = {user_id}
            """
        )

        updated_display_name = True

    # if the user wants to update their profile-picture
    if request_includes_pfp:
        # get the file and attempt to save it
        pfp_file = form.pfp.data
        error_response = handle_user_upload(
            pfp_file,
            f"user-pfps/{user_id}.png",
            "user_pfp"
        )

        # return an error if the pfp wasnt saved and rollback the display-name update if the display name was updated
        if error_response:
            if updated_display_name:
                db_conn.rollback()

            return error_response

        updated_pfp = True

    db_conn.commit()

    # create a "profile_change" object to use for logging and user-feedback
    profile_change = {
        "updated_display_name": updated_display_name,
        "updated_pfp": updated_pfp,
        "new_display_name": form.display_name.data
    }
    app.logger.info(f"Updated user profile {json.dumps(profile_change)}")

    # create the response and its message
    resp_message = ""
    match (updated_display_name, updated_pfp):
        case (True, False): resp_message = "Successfully set display name"
        case (False, True): resp_message = "Successfully set profile picture"
        case (True, True): resp_message = "Successfully set display name and profile picture"
        case _: resp_message = "Updated nothing"
    
    profile_change["message"] = resp_message
    return make_json_response(profile_change, 200)

@app.route("/api/create-post", methods = ["POST"])
@login_required
@validates_CSRF_form(PostCreationForm)
@uses_db_connection
def create_post(current_user : dict,
                form : PostCreationForm,
                db_conn : PooledMySQLConnection,
                db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    post_body = form.post_body.data

    # create a post in the db now since storing the image requires the generated post id
    user_id : int = current_user["user_id"]
    date_created = datetime.now(timezone.utc).timestamp() // 1 # floor to seconds
    contains_image = isinstance(form.image.data, FileStorage) and form.image.data.filename != ""

    db_cursor.execute(
        # create a new row in the posts table with the inputted values
        f"""
        INSERT INTO posts (author_id, date_created, body, contains_image) 
        VALUES ({user_id}, {date_created}, '{post_body}', {contains_image})
        """
    )
    db_cursor.execute(
        # fetch the post that was just created
        f"""
        SELECT
            posts.*,
            0 as "like_count",
            0 as "reply_count",
            users.username as "author_username",
            users.display_name as "author_display_name",
            0 as "user_liked"
        FROM posts
        INNER JOIN users ON posts.author_id = users.user_id
        WHERE author_id = {user_id}
        ORDER BY post_id DESC
        LIMIT 1
        """
    )

    new_post = db_cursor.fetchone() or {}
    post_id = new_post.get("post_id")
    
    # store the image if one was inputted
    if contains_image:
        # attempt to save the inputted image
        image_file = form.image.data
        error_response = handle_user_upload(
            image_file,
            f"post-images/{post_id}.png",
            "post_image"
        )

        # return an error and rollback the post creation if the image wasnt saved
        if error_response:
            db_conn.rollback()
            return error_response

    db_conn.commit()

    # remove the old_like_count since the user client doesnt need to differentiate between it and like_count
    new_post.pop("old_like_count")

    app.logger.info(f"Created post {json.dumps(new_post)}")

    return make_json_response(new_post, 201)

@app.route("/api/create-reply", methods = ["POST"])
@login_required
@validates_CSRF_form(ReplyCreationForm)
@uses_db_connection
def create_reply(current_user : dict,
                 form : ReplyCreationForm,
                 db_conn : PooledMySQLConnection,
                 db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    reply_body = form.reply_body.data
    parent_post_id = form.post_id.data

    # create a reply in the db
    user_id : int = current_user["user_id"]
    date_created = datetime.now(timezone.utc).timestamp() // 1 # floor to seconds

    db_cursor.execute(
        # add a new row to the replies table using the inputted values
        f"""
        INSERT INTO replies (parent_post_id, author_id, date_created, body)
        VALUES ({parent_post_id}, {user_id}, {date_created}, '{reply_body}')
        """
    )
    db_cursor.execute(
        # fetch the reply_id from the reply that was just created
        f"""
        SELECT 
            replies.*,
            users.username as "author_username",
            users.display_name as "author_display_name"
        FROM replies
        INNER JOIN users ON replies.author_id = users.user_id
        WHERE author_id = {user_id}
        ORDER BY reply_id DESC
        LIMIT 1
        """
    )

    new_reply = db_cursor.fetchone() or {}
    db_conn.commit()

    app.logger.info(f"Created reply {json.dumps(new_reply)}")
    
    return make_json_response(new_reply, 201)

@app.route("/api/create-conversation", methods = ["POST"])
@login_required
@validates_CSRF_form(ConversationCreationForm)
@uses_db_connection
def create_conversation(current_user : dict,
                        form : ConversationCreationForm,
                        db_conn : PooledMySQLConnection,
                        db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    input_username = form.username.data

    # create a conversation in the db
    user_id : int = current_user["user_id"]
    date_created = datetime.now(timezone.utc).timestamp() // 1 # floor to seconds

    # ensure that the inputted user exists and that a conversation can be created with them and the current user
    db_cursor.execute(
        # retrieve the user id corresponding to the inputted username, if it exist. also retreive whether a conversation
        # already exists with both the user id of the inputted username and the user id of the currently logged in user
        f"""
        SELECT
            user_id,
            COALESCE(convo_as_u1.conversation_id, convo_as_u2.conversation_id) AS "conversation_id"
        FROM users
        LEFT JOIN conversations convo_as_u1 ON (user_id, {user_id}) = (convo_as_u1.user_1_id, convo_as_u1.user_2_id)
        LEFT JOIN conversations convo_as_u2 ON ({user_id}, user_id) = (convo_as_u2.user_1_id, convo_as_u2.user_2_id)
        WHERE username = '{input_username}'
        """
    )

    user_query = db_cursor.fetchone() or {}

    # return errors for a variety of cases
    if not user_query:
        return make_error_response(f"User '{input_username}' doesn't exist", 404)

    if user_query.get("conversation_id"):
        return make_error_response("A conversation with that user already exists", 409)
    
    user_id_2 = user_query.get("user_id")
    if user_id == user_id_2:
        return make_error_response("Can't create a conversation with yourself", 400)
    
    # create the conversation in the db
    db_cursor.execute(
        # create a new row in the conversations table with the inputted user and the current user
        f"""
        INSERT INTO conversations (user_1_id, user_2_id, date_created)
        VALUES ({user_id}, {user_id_2}, {date_created})
        """
    )

    # fetch the newly created conversation
    db_cursor.execute(
        # return the conversation id, when the conversation was created, if the most recent message of the conversation
        # has been seen by the recipient, as well as the recipients display name and username for the newest
        # conversation the current user is a part of
        f"""
        SELECT
            convos.conversation_id,
            convos.date_created,
            0 AS "contains_unseen_messages",
            COALESCE(u1.user_id, u2.user_id) AS "recipient_user_id",
            COALESCE(u1.display_name, u2.display_name) AS "recipient_display_name",
            COALESCE(u1.username, u2.username) AS "recipient_username"
        FROM conversations convos
        LEFT JOIN users u1 ON (u1.user_id, {user_id}) = (convos.user_1_id, convos.user_2_id)
        LEFT JOIN users u2 ON ({user_id}, u2.user_id) = (convos.user_1_id, convos.user_2_id)
        WHERE {user_id} IN (convos.user_1_id, convos.user_2_id)
        ORDER BY convos.conversation_id DESC
        LIMIT 1
        """
    )

    new_conversation = db_cursor.fetchone() or {}
    db_conn.commit()
    
    # format the log message
    new_conversation_log_message = new_conversation.copy()
    new_conversation_log_message.pop("contains_unseen_messages")
    new_conversation_log_message["creator_user_id"] = user_id
    app.logger.info(f"Created conversation {json.dumps(new_conversation_log_message)}")

    return make_json_response(new_conversation, 201)

@app.route("/api/fetch-posts", methods = ["GET"])
@login_required
@uses_db_connection
def fetch_posts(current_user : dict, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    cursor = request.args.get("cursor")
    cursor, error_response = check_user_input_validity(cursor, "fetch_content_cursor")
    if error_response:
        return error_response

    user_id : int = current_user["user_id"]
    cursor = int(cursor)
    
    # fetch posts from db
    db_cursor.execute(
        # for each post with post id within a certain range, return all its data, the number of rows in the likes table
        # with the same post id, the number of rows in the replies table with the same parent post id, and the post
        # author's username and display name. order these results by descending post id
        f"""
        SELECT 
            posts.*,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id) as "like_count",
            (SELECT COUNT(*) FROM replies WHERE replies.parent_post_id = posts.post_id) as "reply_count",
            users.username as "author_username",
            users.display_name as "author_display_name",
            (SELECT EXISTS (SELECT 1 FROM likes WHERE likes.post_id = posts.post_id AND likes.user_id = {user_id})) as "user_liked",
            (ROW_NUMBER() OVER (ORDER BY posts.post_id ASC) - 1) as "post_idx"
        FROM posts 
        INNER JOIN users ON posts.author_id = users.user_id
        {f"WHERE posts.post_id < {cursor}" if cursor != 0 else ""}
        ORDER BY posts.post_id DESC
        LIMIT {API_CONFIG["post_fetch_max_results"]}
        """
    )

    posts = db_cursor.fetchall() or []

    db_cursor.execute(
        # increase the view count by 1 for each post that was just fetched
        f"""
        UPDATE posts p1
        INNER JOIN (
            SELECT * FROM posts
            {f"WHERE posts.post_id < {cursor}" if cursor != 0 else ""}
            ORDER BY post_id DESC
            LIMIT {API_CONFIG["post_fetch_max_results"]}
        ) AS p2
        ON p1.post_id = p2.post_id
        SET p1.view_count = p1.view_count+1
        """
    )
    
    db_conn.commit()

    # merge the like_count and old_like_count values since the user client doesnt need to differentiate between them.
    # also add 1 to the view count to account for the current user
    for post in posts:
        post["like_count"] += post["old_like_count"]
        post.pop("old_like_count")

        post["view_count"] += 1

    return make_json_response(posts, 200)

@app.route("/api/fetch-post", methods = ["GET"])
@login_required
@uses_db_connection
def fetch_post(current_user : dict, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    post_id = request.args.get("post_id")
    post_id, error_response = check_user_input_validity(post_id, "post_id")
    if error_response:
        return error_response
    
    user_id : int = current_user["user_id"]

    # fetch posts from db
    db_cursor.execute(
        # return all post data for the post with the inputted post id as well as the number of rows in the likes table
        # with the same post id, the number of rows in the replies table with the same parent post id, and the post
        # author's username and display name
        f"""
        SELECT 
            posts.*,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id) as "like_count",
            (SELECT COUNT(*) FROM replies WHERE replies.parent_post_id = posts.post_id) as "reply_count",
            users.username as "author_username",
            users.display_name as "author_display_name",
            (SELECT EXISTS (SELECT 1 FROM likes WHERE likes.post_id = posts.post_id AND likes.user_id = {user_id})) as "user_liked"
        FROM posts
        INNER JOIN users ON posts.author_id = users.user_id
        WHERE post_id = {post_id}
        """
    )
    
    post = db_cursor.fetchone() or {}

    db_cursor.execute(
        # increase the view count by 1 for the post with the inputted post id
        f"""
        UPDATE posts SET view_count = view_count+1 
        WHERE post_id = {post_id}
        """
    )

    db_conn.commit()

    # merge the like_count and old_like_count values since the user client doesnt need to differentiate between them.
    # also add 1 to the view count to account for the current user
    if post:
        post["like_count"] += post["old_like_count"]
        post.pop("old_like_count")

        post["view_count"] += 1

    return make_json_response(post, 200)

@app.route("/api/fetch-replies", methods = ["GET"])
@login_required
@uses_db_connection
@use_only_expected_kwargs
def fetch_replies(db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    post_id = request.args.get("post_id")
    post_id, error_response = check_user_input_validity(post_id, "post_id")
    if error_response:
        return error_response

    cursor = request.args.get("cursor")
    cursor, error_response = check_user_input_validity(cursor, "fetch_content_cursor")
    if error_response:
        return error_response

    cursor = int(cursor)
    
    # fetch replies from db
    db_cursor.execute(
        # for each reply with the parent post id post_id, return all its data as well as the reply index relative to the
        # parent post, the reply author's username and display name. order these results by descending reply id
        f"""
        SELECT 
            replies.*,
            users.username as "author_username",
            users.display_name as "author_display_name",
            (ROW_NUMBER() OVER (ORDER BY replies.reply_id ASC) - 1) as "reply_idx"
        FROM replies
        INNER JOIN users ON replies.author_id = users.user_id
        WHERE replies.parent_post_id = {post_id} {f"AND replies.reply_id < {cursor}" if cursor != 0 else ""}
        ORDER BY replies.reply_id DESC
        LIMIT {API_CONFIG["reply_fetch_max_results"]}
        """
    )

    replies = db_cursor.fetchall() or []

    return make_json_response(replies, 200)

@app.route("/api/fetch-conversations", methods = ["GET"])
@login_required
@uses_db_connection
@use_only_expected_kwargs
def fetch_conversations(current_user : dict, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    cursor = request.args.get("cursor")
    cursor, error_response = check_user_input_validity(cursor, "fetch_content_cursor")
    if error_response:
        return error_response

    cursor = int(cursor)
    user_id : int = current_user["user_id"]

    # fetch conversations from db
    db_cursor.execute(
        # return the conversation id, when the conversation was created, if the most recent message of the conversation
        # has been seen by the recipient, as well as the recipients display name and username for each conversation the
        # current user is a part of
        f"""
        SELECT
            convos.conversation_id,
            convos.date_created,
            (
                SELECT seen = 0 FROM messages
                WHERE (
                    conversation_id = convos.conversation_id AND
                    author_id != {user_id}
                )
                ORDER BY message_id DESC
                LIMIT 1
            ) AS "contains_unseen_messages",
            COALESCE(u1.user_id, u2.user_id) AS "recipient_user_id",
            COALESCE(u1.display_name, u2.display_name) AS "recipient_display_name",
            COALESCE(u1.username, u2.username) AS "recipient_username",
            (ROW_NUMBER() OVER (ORDER BY convos.conversation_id ASC) - 1) as "conversation_idx"
        FROM conversations convos
        LEFT JOIN users u1 ON (u1.user_id, {user_id}) = (convos.user_1_id, convos.user_2_id)
        LEFT JOIN users u2 ON ({user_id}, u2.user_id) = (convos.user_1_id, convos.user_2_id)
        WHERE {user_id} in (convos.user_1_id, convos.user_2_id)
            {f"AND convos.conversation_id < {cursor}" if cursor != 0 else ""}
        ORDER BY convos.conversation_id DESC
        LIMIT {API_CONFIG["conversation_fetch_max_results"]}
        """
    )

    conversations = db_cursor.fetchall() or []

    return make_json_response(conversations, 200)

@app.route("/api/fetch-own-profile", methods = ["GET"])
@login_required
@uses_db_connection
@use_only_expected_kwargs
def fetch_own_profile(current_user : dict, db_cursor : MySQLCursorDict) -> Response:
    user_id : int = current_user["user_id"]
    
    # fetch the current user's info
    db_cursor.execute(
        # return the display name and username of the currently logged in user
        f"""
        SELECT display_name,username FROM users WHERE user_id = {user_id}
        """
    )
    user_query = db_cursor.fetchone() or {}

    if not user_query:
        return make_error_response("User does not exist", 404)
    
    user_info = {
        "display_name": user_query.get("display_name"),
        "username": user_query.get("username"),
        "user_id": user_id
    }

    return make_json_response(user_info, 200)

@app.route("/api/fetch-profile-from-username", methods = ["GET"])
@login_required
@uses_db_connection
@use_only_expected_kwargs
def fetch_profile_from_username(db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    username = request.args.get("username")
    username, error_response = check_user_input_validity(username, "user_username")
    if error_response:
        return error_response
    
    # fetch user by username
    db_cursor.execute(
        # return the user id and display name for the user who's username value is the inputted username
        f"""
        SELECT user_id, display_name FROM users
        WHERE username = '{username}'
        """
    )
    user_query = db_cursor.fetchone() or {}

    if not user_query:
        return make_error_response("User does not exist", 404)
    
    # since we have the username value already, insert it manually as opposed to fetching it from the db
    user_query["username"] = username

    return make_json_response(user_query, 200)

@app.route("/api/like-post", methods = ["PUT"])
@login_required
@validates_CSRF_form(LikePostForm)
@uses_db_connection
def like_post(current_user : dict, form : LikePostForm, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    post_id = form.post_id.data

    user_id : int = current_user["user_id"]
    date_created = datetime.now(timezone.utc).timestamp() // 1 # floor to seconds
    
    # get like-status
    db_cursor.execute(
        # return whether the currently logged in user has likes the inputted post id if a post with the inputted post id
        # exists
        f"""
        SELECT
            likes.user_id IS NOT NULL AS "like_exists"
        FROM posts
        LEFT JOIN likes
            ON (
                likes.post_id = posts.post_id AND
                likes.user_id = {user_id}
            )
        WHERE posts.post_id = {post_id}
        """
    )

    like_exists_query = db_cursor.fetchone() or {}

    if not like_exists_query:
        return make_error_response(f"Post '{post_id}' doesn't exist", 404)
    
    elif like_exists_query.get("like_exists"):
        return make_error_response(f"User already liked post '{post_id}'", 409)
    
    # create a like row
    db_cursor.execute(
        # add a row to the likes table and for the currently logged in user and the inputted post id
        f"""
        INSERT INTO likes (post_id, user_id, date_created) 
        VALUES ({post_id}, {user_id}, {date_created})
        """
    )

    # remove old likes
    db_cursor.execute(
        # to limit db size, each user's oldest like is removed if their like-count exceeds the like-count limit. each
        # removed like record increments the corresponding post's "old_like_count" value
        f"""
        UPDATE posts all_posts
        INNER JOIN (
            SELECT post_id FROM likes
            WHERE likes.user_id = {user_id}
            ORDER BY date_created DESC
            LIMIT {API_CONFIG['user_like_count_limit']}, {API_CONFIG['user_like_count_limit']+999}
        ) AS relevant_posts
        ON all_posts.post_id = relevant_posts.post_id
        SET all_posts.old_like_count = all_posts.old_like_count + 1;

        DELETE likes FROM likes
        INNER JOIN (
            SELECT post_id FROM likes
            WHERE likes.user_id = {user_id}
            ORDER BY date_created DESC
            LIMIT {API_CONFIG['user_like_count_limit']}, {API_CONFIG['user_like_count_limit']+999}
        ) AS relevant_likes
        ON likes.post_id = relevant_likes.post_id
        """,
        multi = True
    )

    db_conn.commit()

    like_data = {"user_id": user_id, "post_id": post_id}
    app.logger.info(f"User liked post {json.dumps(like_data)}")

    return Response(f"Liked post id {post_id}", 200, mimetype = "text/plain")

@app.route("/api/unlike-post", methods = ["PUT"])
@login_required
@validates_CSRF_form(UnlikePostForm)
@uses_db_connection
def unlike_post(current_user : dict, form : UnlikePostForm, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    post_id = form.post_id.data

    user_id : int = current_user["user_id"]

    # ensure the post exists and is liked by the current user
    db_cursor.execute(
        # return whether the currently logged in user has liked the inputted post id if a post with the inputted post id
        # exists
        f"""
        SELECT
            likes.user_id IS NOT NULL AS "like_exists"
        FROM posts
        LEFT JOIN likes
            ON (
                likes.post_id = posts.post_id AND
                likes.user_id = {user_id}
            )
        WHERE posts.post_id = {post_id}
        """
    )

    like_exists_query = db_cursor.fetchone() or {}

    if not like_exists_query:
        return make_error_response(f"Post '{post_id}' doesn't exist", 404)
    
    elif not like_exists_query.get("like_exists"):
        return make_error_response(f"User hasn't liked post '{post_id}'", 409)

    # delete the like row
    db_cursor.execute(
        # delete the row from the likes table that says this user liked the inputted post
        f"""
        DELETE FROM likes WHERE post_id = {post_id} AND user_id = {user_id}
        """
    )

    db_conn.commit()

    unlike_data = {"user_id": user_id, "post_id": post_id}
    app.logger.info(f"User liked post {json.dumps(unlike_data)}")

    return Response(f"Unliked post id {post_id}", 200, mimetype = "text/plain")

@app.route("/api/delete-post", methods = ["DELETE"])
@admin_required
@validates_CSRF_form(DeletePostForm)
@uses_db_connection
def delete_post(current_user : dict, form : DeletePostForm, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    post_id = form.post_id.data
    
    # fetch the relevant post
    db_cursor.execute(
        # fetch the relevant post and its data using the inputted post_id if it exists
        f"""
        SELECT 
            posts.*,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id) as "like_count",
            (SELECT COUNT(*) FROM replies WHERE replies.parent_post_id = posts.post_id) as "reply_count"
        FROM posts
        WHERE post_id = {post_id}
        """
    )

    relevant_post = db_cursor.fetchone() or {}
    
    if not relevant_post:
        return make_error_response(f"Post '{post_id}' does not exist", 404)

    # delete the likes, replies and post related to the inputted post id. the order of deletion is important since if
    # the post is deleted first any likes and replies related to the post will fail their post-id foreign-key check. for
    # some reason using a single db_cursor.execute call with multiple commands silently fails, therefore call each
    # DELETE command separately
    db_cursor.execute(f"DELETE FROM likes WHERE post_id = {post_id};")
    db_cursor.execute(f"DELETE FROM replies WHERE parent_post_id = {post_id};")
    db_cursor.execute(f"DELETE FROM posts WHERE post_id = {post_id};")

    db_conn.commit()

    # remove the post image if it exists
    filepath = CWD / app.config["UPLOAD_FOLDER"] / "post-images" / f"{post_id}.png"
    if filepath.exists():
        os.remove(filepath)

    relevant_post["deleter_user_id"] = current_user["user_id"]
    app.logger.info(f"Deleted post {json.dumps(relevant_post)}")

    return Response(status = 204)

@app.route("/api/delete-reply", methods = ["DELETE"])
@admin_required
@validates_CSRF_form(DeleteReplyForm)
@uses_db_connection
def delete_reply(current_user : dict, form : DeleteReplyForm, db_conn : PooledMySQLConnection, db_cursor : MySQLCursorDict) -> Response:
    # extract and sanitize user inputs
    reply_id = form.reply_id.data
    
    # fetch the relevant reply
    db_cursor.execute(
        # fetch the relevant reply and its data using the inputted reply_id if it exists
        f"""
        SELECT * FROM replies WHERE reply_id = {reply_id}
        """
    )

    relevant_reply = db_cursor.fetchone() or {}

    if not relevant_reply:
        return make_error_response(f"Reply '{reply_id}' does not exist", 404)

    # delete the reply
    db_cursor.execute(
        # delete the reply with the inputted reply id
        f"""
        DELETE FROM replies WHERE reply_id = {reply_id}
        """
    )

    db_conn.commit()

    relevant_reply["deleter_user_id"] = current_user["user_id"]
    app.logger.info(f"Deleted reply {json.dumps(relevant_reply)}")

    return Response(status = 204)
