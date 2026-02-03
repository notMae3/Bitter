from . import app
from .utils.misc_utils import (
    render_template_with_defaults,
    login_required,
    check_user_input_validity,
    format_logging_info
)
from .config import USER_INPUT_CONFIG
from flask import url_for, request, redirect, session, flash, Response

@app.after_request
def after_request(resp : Response):
    # apply cors headers
    resp.headers.set("Cross-Origin-Resource-Policy", "same-origin")
    resp.headers.set("Access-Control-Allow-Origin", request.base_url)

    # log the request and response if a request didnt go as expected. this point
    # is only reached if the initial error was caught and an error code was
    # manually returned. see error_routes.py for uncaught errors
    if resp.status_code >= 400:
        app.logger.info(format_logging_info(resp))

    return resp

@app.route("/", methods = ["GET"])
@login_required
def timeline():
    return render_template_with_defaults("timeline.html")

@app.route("/p", methods = ["GET"])
@app.route("/p/<post_id>", methods = ["GET"])
@login_required
def post(post_id = None):
    if not post_id:
        return redirect(url_for("timeline"))

    # sanitize the inputted post id
    post_id, error_message = check_user_input_validity(post_id, "post", "post_id")
    if error_message:
        flash(error_message)
        return redirect(url_for("timeline"))

    return render_template_with_defaults(
        "post.html",
        post_id = post_id,
        reply_body_max_len = USER_INPUT_CONFIG["reply"]["body"]["max_len"]
    )

@app.route("/chat", methods = ["GET"])
@app.route("/chat/<username>", methods = ["GET"])
@login_required
def chat(username = None):
    if username:
        return render_template_with_defaults(
            "chat.html",
            username = username,
            message_body_max_len = USER_INPUT_CONFIG["message"]["body"]["max_len"]
        )

    return render_template_with_defaults(
        "conversations.html",
        username_max_len = USER_INPUT_CONFIG["user"]["username"]["max_len"]
    )

@app.route("/profile", methods = ["GET"])
@login_required
def profile():
    return render_template_with_defaults(
        "profile.html",
        user_id = session.get("user_id"),
        max_pfp_size = USER_INPUT_CONFIG["user"]["pfp"]["max_size"],
        display_name_max_len = USER_INPUT_CONFIG["user"]["display_name"]["max_len"],
        username_max_len = USER_INPUT_CONFIG["user"]["username"]["max_len"]
    )
