from flask import Flask, render_template
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
def index():
    return render_template("feed.html")

if __name__ == "__main__":
    app.run(debug=True)