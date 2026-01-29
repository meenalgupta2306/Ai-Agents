from flask import Flask, request, render_template, redirect, session
import requests
import os
import json
import urllib.parse
import uuid
from dotenv import load_dotenv
from flask_cors import CORS


load_dotenv()

REDIRECT_URI = os.getenv("REDIRECT_URI")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

CORS(app, supports_credentials=True)

from routes import api_blueprint, chat_blueprint

# Register blueprints
app.register_blueprint(api_blueprint)
app.register_blueprint(chat_blueprint)


@app.route("/api/oauth/linkedin/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    # Redirect to frontend OAuth callback page with parameters
    frontend_url = "http://localhost:3000/oauth/linkedin/callback"
    
    if error:
        return redirect(f"{frontend_url}?error={error}")
    
    if not code:
        return redirect(f"{frontend_url}?error=no_code")
    
    return redirect(f"{frontend_url}?code={code}&state={state}")

# @app.route("/login")
# def login():
#     params = {
#         "response_type": "code",
#         "client_id": CLIENT_ID,
#         "redirect_uri": REDIRECT_URI,
#         "scope": "r_basicprofile r_member_profileAnalytics r_member_postAnalytics w_member_social",
#         "state": "linkedin-poc"
#     }

#     auth_url = (
#         "https://www.linkedin.com/oauth/v2/authorization?"
#         + urllib.parse.urlencode(params)
#     )

#     return redirect(auth_url)


# @app.route("/dashboard")
# def dashboard():
#     if "linkedin_access_token" not in session:
#         return redirect("/")

#     return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(port=os.getenv("PORT"), debug=True)
