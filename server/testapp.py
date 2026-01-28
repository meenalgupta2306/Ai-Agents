from flask import Flask, request, render_template, redirect, session
import requests
import os
import json
import urllib.parse
from dotenv import load_dotenv
from flask_cors import CORS
import webbrowser


load_dotenv()

REDIRECT_URI = "http://localhost:8000/callback"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

CORS(app, supports_credentials=True)

from routes import api_blueprint

# Register blueprint
app.register_blueprint(api_blueprint)


@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return {"error": "Authorization code not found"}, 400

    token_resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10
    )

    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    url = "https://api.linkedin.com/v2/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    data = response.json()

    print(data)

    # print("\n✅ ACCESS TOKEN RESPONSE:")
    # print(token_data)

    # headers = {
    #     "Authorization": f"Bearer {access_token}",
    #     "Content-Type": "application/json",
    #     "LinkedIn-Version": "202401",
    #     "X-Restli-Protocol-Version": "2.0.0"
    # }

    # userinfo_resp = requests.get(
    #     "https://api.linkedin.com/v2/userinfo",
    #     headers=headers,
    #     timeout=10
    # )
    # userinfo = userinfo_resp.json()
    # member_id = userinfo["sub"]

    # # --- THE BRIDGE: Save to a shared file ---
    # auth_payload = {
    #     "access_token": access_token,
    #     "member_id": member_id
    # }
    
    # # This file allows the MCP Agent to 'see' the login session
    # with open("linkedin_creds.json", "w") as f:
    #     json.dump(auth_payload, f)
    # -----------------------------------------

    # session["linkedin_access_token"] = access_token
    # session["member_id"] = member_id
    # session["user"] = {
    #     "given_name": userinfo.get("given_name"),
    #     "family_name": userinfo.get("family_name"),
    #     "email": userinfo.get("email"),
    #     "picture": userinfo.get("picture"),
    #     "locale": userinfo.get("locale"),
    #     "email_verified": userinfo.get("email_verified")
    # }

    #redirect to react dashboard
    return redirect("http://localhost:3000/dashboard")

# @app.route("/login")
# def login():
#     params = {
#         "response_type": "code",
#         "client_id": CLIENT_ID,
#         "redirect_uri": REDIRECT_URI,
#         "scope": ""openid profile email w_member_social",
#         "state": "linkedin-poc"
#     }

#     auth_url = (
#         "https://www.linkedin.com/oauth/v2/authorization?"
#         + urllib.parse.urlencode(params)
#     )

#     return redirect(auth_url)

def login():
    auth_url = (
    f"https://www.linkedin.com/oauth/v2/authorization"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=w_member_sociaw_member_sociall"
    )

    webbrowser.open(auth_url)


@app.route("/dashboard")
def dashboard():
    if "linkedin_access_token" not in session:
        return redirect("/")auth_url = (
    f"https://www.linkedin.com/oauth/v2/authorization"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&scope=w_member_sociaw_member_sociall"
    )

    return render_template("dashboard.html")

login()
if __name__ == "__main__":
    app.run(port=8000, debug=True)
