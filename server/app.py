from flask import Flask, request, redirect
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

CORS(app, supports_credentials=True)

# Register feature blueprints
from features.linkedin.routes import linkedin_blueprint
from features.oauth.routes import oauth_blueprint
from features.chat.routes import chat_blueprint
from features.voice.routes import voice_blueprint
from features.voice_cloning import voice_cloning_bp, init_voice_cloning_service

app.register_blueprint(linkedin_blueprint)
app.register_blueprint(oauth_blueprint)
app.register_blueprint(chat_blueprint)
app.register_blueprint(voice_blueprint)
app.register_blueprint(voice_cloning_bp)

# Initialize voice cloning service
DOCUMENTS_DIR = os.getenv('DOCUMENTS_DIR', os.path.join(os.path.dirname(__file__), 'documents'))
VOICE_SERVICE_URL = os.getenv('VOICE_SERVICE_URL', 'http://localhost:5002')
init_voice_cloning_service(DOCUMENTS_DIR, VOICE_SERVICE_URL)


# OAuth callback (stays in app.py as it's a redirect endpoint)
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


if __name__ == "__main__":
    app.run(port=os.getenv("PORT"), debug=True)

