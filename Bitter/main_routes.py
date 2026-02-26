from . import app
from .forms import (
    ReplyCreationForm,
    ConversationCreationForm,
    UpdateProfileForm
)
from .utils.misc_utils import (
    make_response_with_template,
    login_required,
    check_user_input_validity,
    renews_access_token,
    append_removal_of_access_token_to_response
)
from .config import FORM_CONFIG
from flask import url_for, request, redirect, flash, Response

@app.after_request
def after_request(resp : Response) -> Response:
    # apply cors headers
    resp.headers.set("Cross-Origin-Resource-Policy", "same-origin")
    resp.headers.set("Access-Control-Allow-Origin", request.host_url)

    return resp

@app.route("/signout", methods = ["GET"])
def signout() -> Response:
    resp = redirect(url_for("timeline"))
    append_removal_of_access_token_to_response(resp)

    return resp

@app.route("/", methods = ["GET"])
@login_required
@renews_access_token
def timeline(current_user : dict) -> Response:
    return make_response_with_template(
        "timeline.jinja2",
        is_admin = current_user["is_admin"]
    )

@app.route("/p", methods = ["GET"])
@app.route("/p/<post_id>", methods = ["GET"])
@login_required
@renews_access_token
def post(current_user : dict, post_id = None) -> Response:
    if not post_id:
        return redirect(url_for("timeline"))

    # extract and sanitize user inputs
    post_id, error_message = check_user_input_validity(str(post_id), "post_id", return_response = False)
    if error_message:
        flash(error_message)
        return redirect(url_for("timeline"))

    return make_response_with_template(
        "post.jinja2",
        reply_creation_form = ReplyCreationForm(),
        is_admin = current_user["is_admin"],
        post_id = post_id
    )

@app.route("/chat", methods = ["GET"])
@app.route("/chat/<username>", methods = ["GET"])
@login_required
@renews_access_token
def chat(current_user : dict, username = None) -> Response:
    # return the chat template if a username was inputted, otherwise render the conversations template

    if username:
        return make_response_with_template(
            "chat.jinja2",
            is_admin = current_user["is_admin"],
            username = username
        )

    return make_response_with_template(
        "conversations.jinja2",
        is_admin = current_user["is_admin"],
        conversation_creation_form = ConversationCreationForm()
    )

@app.route("/profile", methods = ["GET"])
@login_required
@renews_access_token
def profile(current_user : dict) -> Response:
    return make_response_with_template(
        "profile.jinja2",
        update_profile_form = UpdateProfileForm(),
        is_admin = current_user["is_admin"],
        user_id = current_user["user_id"],
        max_pfp_size = FORM_CONFIG["user_pfp"]["custom_data"]["max_size"],
    )
