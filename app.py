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
    print(url_for('static', filename='styles/components/feed.css'))
    return render_template("timeline.html", feed_type="timeline")

@app.route(f"/p/<int:post_id>")
def post(post_id):
    print(post_id)

    return render_template("post.html", feed_type="post")

if __name__ == "__main__":
    app.run(debug=True)

    # TODO del clickthrough preventer?