from flask import Flask, render_template, url_for
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

app.config.update(
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "pass123"),
    SESSION_PERMANENT = False,
    SESSION_TYPE = "filesystem"
)

@app.route("/")
def timeline():
    return render_template("timeline.html")

@app.route("/p/<int:post_id>")
def post(post_id):
    print(post_id)

    return render_template("post.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/chat/<username>")
def chat_conversation(username):
    return render_template("chat_conversation.html")

if __name__ == "__main__":
    app.run(debug=True)

    # TODO del clickthrough preventer?

    # post and reply char limit: 140
    # username char limit: 24

