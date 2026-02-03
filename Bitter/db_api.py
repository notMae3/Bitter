from . import app
from .utils.db_utils import (
    db_exec,
    db_exec_multiple
)
from .utils.misc_utils import (
    check_user_input_validity,
    handle_user_upload,
    login_required,
    admin_required,
    Redirect
)
from flask import (
    request,
    redirect,
    flash,
    url_for,
    session,
    send_file,
    send_from_directory,
    Response
)
from .config import API_CONFIG
from werkzeug.security import check_password_hash, generate_password_hash
from pathlib import Path
import time, os, json

@app.route("/api/uploads", methods = ["GET"])
@app.route("/api/uploads/<category>", methods = ["GET"])
@app.route("/api/uploads/<category>/<filename>", methods = ["GET"])
@login_required
def uploads(category = None, filename = None) -> Response:
    if not category or not filename:
        return Response("Asset not found", 404, mimetype="text/plain")

    filepath = Path(app.config["UPLOAD_FOLDER"], category, filename).absolute()
    file_exists = filepath.exists()

    if file_exists:
        return send_file(filepath, "image/*")

    # send the default user pfp if the requested user pfp doesnt exist
    elif category == "user_pfps":
        return send_from_directory(app.static_folder, path="img/default_user_pfp.png")

    else:
        return Response("Asset not found", 404, mimetype="text/plain")

@app.route("/api/login", methods = ["POST"])
def login() -> Redirect:
    # extract and sanitize inputs
    input_username = request.form.get("username")
    input_username, error_message = check_user_input_validity(input_username, "user", "username")
    if error_message:
        flash(error_message)
        return redirect(url_for("timeline"))
    
    input_password = request.form.get("password")
    input_password, error_message = check_user_input_validity(input_password, "user", "password")
    if error_message:
        flash(error_message)
        return redirect(url_for("timeline"))
    
    # fetch the stored password and check if the inputted password is correct
    db_result = db_exec(
        # get user id and password for the user that has the inputted username
        f"""
        SELECT user_id, password, is_admin FROM users WHERE username = '{input_username}'
        """
    )
    
    if not db_result:
        flash(f"User '{input_username}' doesn't exist")
        return redirect(url_for("timeline"))
    
    hashed_password = db_result.get("password", "")
    correct_password = check_password_hash(hashed_password, input_password)

    if not correct_password:
        flash(f"Incorrect password for user '{input_username}'")
        return redirect(url_for("timeline"))

    # the login succeeded if this point is reached, therefore update cookies
    session["user_id"] = db_result.get("user_id")
    session["is_admin"] = db_result.get("is_admin") == 1

    return redirect(request.referrer)

@app.route("/api/signup", methods = ["POST"])
def signup() -> Redirect:
    # extract and check user input validity
    inputs = {
        "display_name": request.form.get("display-name"),
        "username": request.form.get("username"),
        "email": request.form.get("email"),
        "password": request.form.get("password")
    }

    for key, value in inputs.items():
        inputs[key], error_message = check_user_input_validity(value, "user", key)
        if error_message:
            flash(error_message)
            return redirect(url_for("timeline"))

    # check if either username of email is unavailable
    db_duplicates_result = db_exec(
        # select the first value, either username of email, that already exists
        # in the users table
        f"""
        SELECT 
            COALESCE(
                (SELECT username FROM users WHERE username = '{inputs['username']}'),
                (SELECT email FROM users WHERE email = '{inputs['email']}')
            ) as result
        """
    )

    duplicate_value = db_duplicates_result.get("result")
    if duplicate_value != None:
        unavailable_column = "Username" if duplicate_value == inputs["username"] else "Email"
        flash(f"{unavailable_column} '{duplicate_value}' is unavailable")
        return redirect(url_for("timeline"))

    # update db
    hashed_password = generate_password_hash(
        inputs["password"],
        salt_length = API_CONFIG["account_password_salt_length"]
    )

    db_exec(
        # create a new row in users with the inputted values
        f"""
        INSERT INTO users (username, display_name, email, password) 
        VALUES ('{inputs['username']}', '{inputs['display_name']}', '{inputs['email']}', '{hashed_password}')
        """,
        commit=True
    )

    flash("Account creation successful")

    return redirect(url_for("timeline"))

@app.route("/api/signout", methods = ["GET"])
def signout() -> Redirect:
    session.pop("user_id", None)
    session.pop("is_admin", None)
    return redirect(url_for("timeline"))

@app.route("/api/update-profile", methods = ["POST"])
@login_required
def update_profile() -> Redirect:
    # get user id
    user_id = session.get("user_id")

    if "display-name" in request.form:
        # verify input values are not empty or changed after sanitization
        display_name = request.form.get("display-name")
        display_name, error_message = check_user_input_validity(display_name, "user", "display_name")
        if error_message:
            flash(error_message)
            return redirect(url_for("profile"))

        # update db
        db_exec(
            # update the display name of the user who's user id is the inputted
            # user id
            f"""
            UPDATE users SET display_name = '{display_name}' WHERE user_id = {user_id}
            """,
            commit=True
        )

        flash("Successfully set display name")

    # save pfp file
    if "pfp" in request.files and request.files["pfp"].filename != "":
        pfp_file = request.files.get("pfp")

        error_message = handle_user_upload(
            pfp_file,
            f"user_pfps/{user_id}.png",
            "user",
            "pfp"
        )

        if error_message:
            flash(error_message)
            return redirect(url_for("profile"))

        flash("Successfully set profile picture")

    return redirect(url_for("profile"))

@app.route("/api/create-post", methods = ["POST"])
@login_required
def create_post() -> Redirect:
    # sanitize post body
    post_body = request.form.get("post-body")
    post_body, error_message = check_user_input_validity(post_body, "post", "body")
    if error_message:
        flash(error_message)
        return redirect(request.referrer)

    # create a post in the db now since storing the image requires a post id
    user_id = session.get("user_id")
    date_created = time.time() // 1 # floor to seconds
    contains_image = "image" in request.files and request.files["image"].filename != ""

    db_results = db_exec_multiple(
        # create a new row in the posts table with the inputted values
        f"""
        INSERT INTO posts (author_id, date_created, body, contains_image) 
        VALUES ({user_id}, {date_created}, '{post_body}', {contains_image})
        """,
        # fetch the post id of the post that was just created
        f"""
        SELECT post_id FROM posts WHERE author_id = {user_id} ORDER BY post_id DESC LIMIT 1
        """,
        commit = True,
        fetch_all = [False, False]
    )

    post_id = db_results[1].get("post_id")
    
    # store image
    if contains_image:
        image_file = request.files["image"]

        error_message = handle_user_upload(
            image_file,
            f"post_images/{post_id}.png",
            "post",
            "image"
        )

        # delete this post if the image upload failed
        if error_message:
            db_exec(
                # delete the post with the post id post_id
                f"""
                DELETE FROM posts WHERE post_id = {post_id}
                """,
                commit = True
            )
            flash(error_message)
            return redirect(request.referrer)

    return redirect(request.referrer)

@app.route("/api/create-reply", methods = ["POST"])
@login_required
def create_reply() -> Redirect:
    # sanitize reply body and parent post id
    reply_body = request.form.get("reply-body")
    reply_body, error_message = check_user_input_validity(reply_body, "reply", "body")
    if error_message:
        flash(error_message)
        return redirect(request.referrer)

    parent_post_id = request.form.get("parent-post-id")
    parent_post_id, error_message = check_user_input_validity(parent_post_id, "post", "post_id")
    if error_message:
        flash(error_message)
        return redirect(request.referrer)

    # create a reply in the db now since storing the image requires a reply id
    user_id = session.get("user_id")
    date_created = time.time() // 1 # floor to seconds

    db_exec_multiple(
        # add a new row to the replies table using the inputted values
        f"""
        INSERT INTO replies (parent_post_id, author_id, date_created, body)
        VALUES ({parent_post_id}, {user_id}, {date_created}, '{reply_body}')
        """,
        # fetch the reply_id from the reply that was just created
        f"""
        SELECT reply_id FROM replies WHERE author_id = {user_id} ORDER BY reply_id DESC LIMIT 1
        """,
        commit = True,
        fetch_all = [False, False]
    )
    
    return redirect(request.referrer)

@app.route("/api/create-conversation", methods = ["POST"])
@login_required
def create_conversation() -> Redirect:
    # sanitize reply body and parent post id
    input_username = request.form.get("username")
    input_username, error_message = check_user_input_validity(input_username, "user", "username")
    if error_message:
        flash(error_message)
        return redirect(request.referrer)

    # create a reply in the db now since storing the image requires a reply id
    user_id = session.get("user_id")
    date_created = time.time() // 1 # floor to seconds

    # ensure that the inputted user exists and that a conversation can be
    # created with them
    db_result = db_exec(
        # retrieve the user id corresponding to the inputted username, if one
        # exist. also retreive wether a conversation already exists with both
        # the user id of the inputted username and the user id of the currently
        # logged in user
        f"""
        SELECT
            user_id AS "user_id_query",
            COALESCE(convo_as_u1.conversation_id, convo_as_u2.conversation_id) AS "conversation_id"
        FROM users
        LEFT JOIN conversations convo_as_u1 ON (user_id, {user_id}) = (convo_as_u1.user_1_id, convo_as_u1.user_2_id)
        LEFT JOIN conversations convo_as_u2 ON ({user_id}, user_id) = (convo_as_u2.user_1_id, convo_as_u2.user_2_id)
        WHERE username = '{input_username}'
        """,
        fetch_all = False
    )

    if not db_result:
        flash(f"User '{input_username}' doesn't exist")
        return redirect(request.referrer)

    elif db_result.get("conversation_id"):
        flash(f"A conversation with that user already exists")
        return redirect(request.referrer)
    
    elif user_id == (user_id_2 := db_result.get("user_id_query")):
        flash(f"Can't create a conversation with yourself")
        return redirect(request.referrer)
    
    # create conversation
    db_exec(
        # create a new row in the conversations table with the inputted user
        f"""
        INSERT INTO conversations (user_1_id, user_2_id, date_created)
        VALUES ({user_id}, {user_id_2}, {date_created})
        """,
        commit = True
    )
    
    return redirect(request.referrer)

@login_required
def create_message(recipient_username : str, message_body : str) -> dict:
    # extract and sanitize inputs
    recipient_username, error_message = check_user_input_validity(recipient_username, "user", "username")
    if error_message:
        return {"error": error_message}
    
    # sanitize cursor
    message_body, error_message = check_user_input_validity(message_body, "message", "body")
    if error_message:
        return {"error": error_message}
    
    user_id = session.get("user_id")
    date_created = time.time() // 1 # floor to seconds
    
    # ensure that the inputted user exists and that a conversation can be
    # created with them
    db_result = db_exec(
        # retrieve the user id corresponding to the inputted username, if one
        # exist. also retreive wether a conversation exists with both the user
        # id of the inputted username and the user id of the currently logged in
        # user
        f"""
        SELECT
            user_id AS "user_id_query",
            COALESCE(convo_as_u1.conversation_id, convo_as_u2.conversation_id) AS "conversation_id"
        FROM users
        LEFT JOIN conversations convo_as_u1 ON (user_id, {user_id}) = (convo_as_u1.user_1_id, convo_as_u1.user_2_id)
        LEFT JOIN conversations convo_as_u2 ON ({user_id}, user_id) = (convo_as_u2.user_1_id, convo_as_u2.user_2_id)
        WHERE username = '{recipient_username}'
        """,
        fetch_all = False
    )

    if not db_result:
        return {"error": f"User '{recipient_username}' doesn't exist"}

    elif not (conversation_id := db_result.get("conversation_id")):
        return {"error": f"A conversation with that user doesn't exist"}
    
    elif user_id == db_result.get("user_id_query"):
        return {"error": f"Can't message yourself"}

    # update db
    db_message_result = db_exec_multiple(
        # create a new message row with the inputted information
        f"""
        INSERT INTO messages (author_id, body, date_created, conversation_id)
        VALUES ({user_id}, '{message_body}', {date_created}, {conversation_id})
        """,
        # fetch the new message
        f"""
        SELECT * FROM messages
        ORDER BY message_id DESC
        LIMIT 1
        """,
        commit = True,
        fetch_all = [False, False]
    )

    return db_message_result[1]

@app.route("/api/fetch-posts", methods = ["GET"])
@login_required
def fetch_posts() -> Response:
    # sanitize cursor
    cursor = request.args.get("cursor")
    cursor, error_message = check_user_input_validity(cursor, "fetch_content", "cursor")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    user_id = session.get("user_id")
    cursor = int(cursor)
    
    # fetch posts from db
    db_result = db_exec_multiple(
        # for each post with post id within a certain range, return all its
        # data, the number of rows in the likes table with the same post id,
        # the number of rows in the replies table with the same parent post id,
        # and the post author's username and display name. order these results
        # by descending post id
        f"""
        SELECT 
            posts.*,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id) as "like_count",
            (SELECT COUNT(*) FROM replies WHERE replies.parent_post_id = posts.post_id) as "reply_count",
            users.username as "author_username",
            users.display_name as "author_display_name",
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id AND likes.user_id = {user_id}) as "user_liked",
            ROW_NUMBER() OVER (ORDER BY posts.post_id ASC) as "post_idx"
        FROM posts 
        INNER JOIN users ON posts.author_id = users.user_id
        {f"WHERE posts.post_id < {cursor}" if cursor != 0 else ""}
        ORDER BY posts.post_id DESC
        LIMIT {API_CONFIG["post_fetch_max_results"]}
        """,
        # increase the view count by 1 for each post within a certain range
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
        """,
        commit = True,
        fetch_all = [True, False]
    )

    posts = db_result[0]

    return Response(json.dumps(posts).encode("utf-8"), 200, mimetype="application/json")

@app.route("/api/fetch-post", methods = ["GET"])
@login_required
def fetch_post() -> Response:
    # sanitize post id
    post_id = request.args.get("post_id")
    post_id, error_message = check_user_input_validity(post_id, "post", "post_id")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")
    
    user_id = session.get("user_id")

    # fetch posts from db
    db_result = db_exec_multiple(
        # return all post data for the post with the inputted post id as well as
        # the number of rows in the likes table with the same post id, the
        # number of rows in the replies table with the same parent post id, and
        # the post author's username and display name
        f"""
        SELECT 
            posts.*,
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id) as "like_count",
            (SELECT COUNT(*) FROM replies WHERE replies.parent_post_id = posts.post_id) as "reply_count",
            users.username as "author_username",
            users.display_name as "author_display_name",
            (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.post_id AND likes.user_id = {user_id}) as "user_liked"
        FROM posts
        INNER JOIN users ON posts.author_id = users.user_id
        WHERE post_id = {post_id}
        """,
        # increase the view count by 1 for the post with the inputted post id
        f"""
        UPDATE posts SET view_count = view_count+1 
        WHERE post_id = {post_id}
        """,
        commit = True,
        fetch_all = [True, False]
    )

    post = db_result[0]

    return Response(json.dumps(post).encode("utf-8"), 200, mimetype="application/json")

@app.route("/api/fetch-replies", methods = ["GET"])
@login_required
def fetch_replies() -> Response:
    # sanitize post id
    post_id = request.args.get("post_id")
    post_id, error_message = check_user_input_validity(post_id, "post", "post_id")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")
    
    # sanitize cursor
    cursor = request.args.get("cursor")
    cursor, error_message = check_user_input_validity(cursor, "fetch_content", "cursor")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    cursor = int(cursor)
    
    # fetch replies from db
    db_result = db_exec(
        # for each reply with the parent post id post_id, return all its data as
        # well as the reply index relative to the parent post, the reply
        # author's username and display name. order these results by descending
        # reply id
        f"""
        SELECT 
            replies.*,
            users.username as "author_username",
            users.display_name as "author_display_name",
            ROW_NUMBER() OVER (ORDER BY replies.reply_id ASC) as "reply_idx"
        FROM replies
        INNER JOIN users ON replies.author_id = users.user_id
        WHERE replies.parent_post_id = {post_id} {f"AND replies.reply_id < {cursor}" if cursor != 0 else ""}
        ORDER BY replies.reply_id DESC
        LIMIT {API_CONFIG["reply_fetch_max_results"]}
        """,
        fetch_all = True
    )

    replies = db_result

    return Response(json.dumps(replies).encode("utf-8"), 200, mimetype="application/json")

@app.route("/api/fetch-conversations", methods = ["GET"])
@login_required
def fetch_conversations() -> Response:
    # sanitize cursor
    cursor = request.args.get("cursor")
    cursor, error_message = check_user_input_validity(cursor, "fetch_content", "cursor")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    cursor = int(cursor)
    user_id = session.get("user_id")

    # fetch conversations from db
    db_result = db_exec(
        # return the conversation id, when the conversation was created, if the
        # most recent message of the conversation has been seen by the
        # recipient, as well as the recipients display name and username for
        # each conversation the current user is a part of
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
            ROW_NUMBER() OVER (ORDER BY convos.conversation_id ASC) as "conversation_idx"
        FROM conversations convos
        LEFT JOIN users u1 ON (u1.user_id, {user_id}) = (convos.user_1_id, convos.user_2_id)
        LEFT JOIN users u2 ON ({user_id}, u2.user_id) = (convos.user_1_id, convos.user_2_id)
        WHERE {user_id} in (convos.user_1_id, convos.user_2_id)
            {f"AND convos.conversation_id < {cursor}" if cursor != 0 else ""}
        ORDER BY convos.conversation_id DESC
        LIMIT {API_CONFIG["conversation_fetch_max_results"]}
        """,
        fetch_all = True
    )

    conversations = db_result

    return Response(json.dumps(conversations).encode("utf-8"), 200, mimetype="application/json")

@login_required
def fetch_messages(recipient_username : str, cursor : str) -> dict | list:
    # extract and sanitize inputs
    recipient_username, error_message = check_user_input_validity(recipient_username, "user", "username")
    if error_message:
        return {"error": error_message}
    
    # sanitize cursor
    cursor, error_message = check_user_input_validity(cursor, "fetch_content", "cursor")
    if error_message:
        return {"error": error_message}
    
    cursor = int(cursor)
    user_id = session.get("user_id")

    db_result = db_exec_multiple(
        # return all messages with the conversation id of the conversation that
        # the currently logged in user and the inputted recipient username
        # share, if it exists
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
        """,
        # for each message in the previous query who's author isn't the
        # currently logged in user, mark it as seen
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
        """,
        commit = True,
        fetch_all = [True, False]
    )

    messages = db_result[0]

    # add "origin" data, which for each message denotes wether the currely
    # logged in user sent or recieved the message
    for message in messages:
        from_current_user = message["author_id"] == user_id
        message["origin"] = "sent" if from_current_user else "received"

    return messages

@app.route("/api/fetch-own-profile", methods = ["GET"])
@login_required
def fetch_own_profile() -> Response:
    user_id = session.get("user_id")
    
    db_result = db_exec(
        # return the display name and username of the currently logged in user
        f"""
        SELECT display_name,username FROM users WHERE user_id = {user_id}
        """
    )

    if not db_result:
        return Response("User not found", status=404, mimetype="text/plain")
    
    user_info = {
        "display_name": db_result.get("display_name"),
        "username": db_result.get("username"),
        "user_id": user_id
    }

    return Response(json.dumps(user_info).encode("utf-8"), 200, mimetype="application/json")

@app.route("/api/fetch-profile-from-username", methods = ["GET"])
@login_required
def fetch_profile_from_username() -> Response:
    username = request.args.get("username")
    username, error_message = check_user_input_validity(username, "user", "username")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")
    
    db_result = db_exec(
        # return the user id and display name for the user who's username value
        # is the inputted username
        f"""
        SELECT user_id, display_name FROM users
        WHERE username = '{username}'
        """
    )

    if not db_result:
        return Response("User does not exist", 404, mimetype="text/plain")
    else:
        db_result["username"] = username

    return Response(json.dumps(db_result).encode("utf-8"), 200, mimetype="application/json")

@app.route("/api/like-post", methods = ["POST"])
@login_required
def like_post() -> Response:
    # sanitize post id
    request_json = request.get_json()
    if not request_json or "post_id" not in request_json:
        return Response("Couldn't parse as json", 400, mimetype="text/plain")
    
    post_id = str(request_json.get("post_id"))
    post_id, error_message = check_user_input_validity(post_id, "post", "post_id")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    user_id = session.get("user_id")
    date_created = time.time() // 1 # floor to seconds
    
    db_result = db_exec(
        # return wether the currently logged in user has likes the inputted post
        # id if a post with the inputted post id exists
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

    if not db_result:
        return Response(f"Post '{post_id}' doesn't exist", 404, mimetype="text/plain")
    
    if db_result.get("like_exists"):
        return Response("User already liked this post", 409, mimetype="text/plain")
    
    # update db
    db_exec_multiple(
        # add a row to the likes table and ignore the error raised if this user
        # had already liked this post or if the post doesnt exist
        f"""
        INSERT INTO likes (post_id, user_id, date_created) 
        VALUES ({post_id}, {user_id}, {date_created})
        """,
        # to limit db size, this users oldest like is removed if the like count
        # exceeds the like count limit
        f""" 
        DELETE l1
        FROM likes AS l1
        INNER JOIN (SELECT *
            FROM likes
            WHERE user_id = 1
            ORDER BY date_created DESC
            LIMIT {API_CONFIG['user_like_count_limit']}, {API_CONFIG['user_like_count_limit']+999}
            ) AS l2
        ON l1.post_id = l2.post_id
        """,
        commit = True,
        fetch_all = [False, False]
    )

    return Response(status=204)

@app.route("/api/unlike-post", methods = ["POST"])
@login_required
def unlike_post() -> Response:
    # sanitize post id
    request_json = request.get_json()
    if not request_json or "post_id" not in request_json:
        return Response("Couldn't parse as json", 400, mimetype="text/plain")
    
    post_id = str(request_json.get("post_id"))
    post_id, error_message = check_user_input_validity(post_id, "post", "post_id")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    user_id = session.get("user_id")

    # update db
    db_exec(
        # delete the row from the likes table that says this user liked this
        # post
        f"""
        DELETE FROM likes WHERE post_id = {post_id} AND user_id = {user_id}
        """,
        commit = True
    )

    return Response(status=204)

@app.route("/api/delete-post", methods = ["DELETE"])
@login_required
@admin_required
def delete_post() -> Response:
    # if the post to be delete is a post
    post_id = request.args.get("post_id")
    post_id, error_message = check_user_input_validity(post_id, "post", "post_id")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    db_exec_multiple(
        # delete the likes, reply and post are related to the inputted post id.
        # the order of deletion is important since if the post is deleted first
        # any likes and replies related to said post will fail their post-id
        # foreign-key check
        f"""
        DELETE FROM likes WHERE post_id = {post_id}
        """,
        f"""
        DELETE FROM replies WHERE parent_post_id = {post_id}
        """,
        f"""
        DELETE FROM posts WHERE post_id = {post_id}
        """,
        commit = True,
        fetch_all = [False, False, False]
    )

    filepath = Path(app.config["UPLOAD_FOLDER"], "post_images", f"{post_id}.png").absolute()
    if filepath.exists():
        os.remove(filepath)

    return Response(status=204)

@app.route("/api/delete-reply", methods = ["DELETE"])
@login_required
@admin_required
def delete_reply() -> Response:
    # if the reply to be delete is a reply
    reply_id = request.args.get("reply_id")
    reply_id, error_message = check_user_input_validity(reply_id, "reply", "reply_id")
    if error_message:
        return Response(error_message, 400, mimetype="text/plain")

    db_exec(
        # delete the reply with the inputted reply id
        f"""
        DELETE FROM replies WHERE reply_id = {reply_id}
        """,
        commit = True
    )

    return Response(status=204)

@login_required
def fetch_shared_conversation_id(username : str) -> dict:
    username, error_message = check_user_input_validity(username, "user", "username")
    if error_message:
        return {"error": error_message}
    
    user_id = session.get("user_id")
    
    db_result = db_exec(
        # return the conversation id of the conversation that the currenly
        # logged in user and the inputted username share
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

    if not db_result:
        return {"error": "Conversation ID doesn't exist"}

    return db_result

def mark_message_seen(safe_message_id : int) -> None:
    db_exec(
        # update the seen value of the message with the inputted message id
        f"""
        UPDATE messages SET seen = true
        WHERE message_id = {safe_message_id}
        """,
        commit = True
    )

def post_exists(safe_post_id : str) -> bool:
    db_result = db_exec(
        # return 1 if a post with the inputted post id exists, otherwise return
        # nothing
        f"""
        SELECT COUNT(*) AS "exists" FROM posts
        WHERE post_id = {safe_post_id}
        """
    )

    return bool(db_result.get("exists"))

def ensure_admin_account_exists() -> None:
    password = os.getenv("ADMIN_ACCOUNT_PASSWORD", "pass123")
    password, error_message = check_user_input_validity(password, "user", "password")
    if error_message:
        raise ValueError(password, error_message)

    hashed_password = generate_password_hash(
        password,
        salt_length = API_CONFIG["account_password_salt_length"]
    )

    db_exec(
        # add the admin account to the users table and ignore any errors. the
        # errors this comman ignores is if a user with username "admin" already
        # exists. this is not a problem since this will always be the first user
        # created on program boot, which means a random user cant possibly steal
        # the username
        f"""
        INSERT IGNORE INTO users (username, display_name, password, is_admin)
        VALUES ('admin', 'Admin', '{hashed_password}', true)
        """,
        commit = True
    )

    app.logger.info("Ensured primary admin account exists")
