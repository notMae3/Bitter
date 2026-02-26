from .config import FORM_CONFIG
from flask_wtf import FlaskForm
from wtforms import Field, StringField, TextAreaField, PasswordField, EmailField, SubmitField, FileField

def construct_input_field(field_type : type[Field], label : str, VALUE_CONFIG : dict, **kwargs):
    # read values from config
    field_name = VALUE_CONFIG["field_name"]
    filters = VALUE_CONFIG["filters"]
    validators = VALUE_CONFIG["validators"]
    default = VALUE_CONFIG["default"]

    # insert this field's name into all the validator error messages
    for validator in validators:
        validator.message = validator.message.format(field_name = field_name)

    return field_type(label, validators = validators, filters = filters, default = default, **kwargs)

class LoginForm(FlaskForm):
    username = construct_input_field(StringField, "Username", FORM_CONFIG["user_username"])
    password = construct_input_field(PasswordField, "Password", FORM_CONFIG["user_password"])
    submit = SubmitField("Login")

class SignupForm(FlaskForm):
    display_name = construct_input_field(StringField, "Display-name", FORM_CONFIG["user_display_name"])
    username = construct_input_field(StringField, "Username", FORM_CONFIG["user_username"])
    email = construct_input_field(EmailField, "Email", FORM_CONFIG["user_email"])
    password = construct_input_field(PasswordField, "Password", FORM_CONFIG["user_password"])
    submit = SubmitField("Sign-up")

class UpdateProfileForm(FlaskForm):
    display_name = construct_input_field(StringField, "Display-name", FORM_CONFIG["user_display_name"])
    pfp = construct_input_field(FileField, "pfp", FORM_CONFIG["user_pfp"])
    submit = SubmitField("Update profile")

class PostCreationForm(FlaskForm):
    post_body = construct_input_field(TextAreaField, "Post body", FORM_CONFIG["post_body"])
    image = construct_input_field(FileField, "Image", FORM_CONFIG["post_image"])
    submit = SubmitField("Post")

class ReplyCreationForm(FlaskForm):
    reply_body = construct_input_field(TextAreaField, "Reply", FORM_CONFIG["reply_body"])
    post_id = construct_input_field(StringField, "Post id", FORM_CONFIG["post_id"])
    submit = SubmitField("")

class ConversationCreationForm(FlaskForm):
    username = construct_input_field(StringField, "Username", FORM_CONFIG["user_username"])
    submit = SubmitField("Start chat")

class LikePostForm(FlaskForm):
    post_id = construct_input_field(StringField, "Post id", FORM_CONFIG["post_id"])

class UnlikePostForm(FlaskForm):
    post_id = construct_input_field(StringField, "Post id", FORM_CONFIG["post_id"])

class DeletePostForm(FlaskForm):
    post_id = construct_input_field(StringField, "Post id", FORM_CONFIG["post_id"])

class DeleteReplyForm(FlaskForm):
    reply_id = construct_input_field(StringField, "Reply id", FORM_CONFIG["reply_id"])
