"""LinkedIn posting tool"""
import os
import json
from pathlib import Path
from features.linkedin.service import LinkedInService


def linkedin_tool(text: str, image_path: str = None):
    """Posts content to LinkedIn for the currently authenticated user."""
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    creds_path = BASE_DIR / "documents" / "json" / "linkedin_creds.json"
    
    if not os.path.exists(creds_path):
        return {
            "status": "AUTH_REQUIRED",
            "url": "http://localhost:8000/login",
            "message": "User must sign in via the provided link."
        }
    
    try:
        with open(creds_path, "r") as f:
            creds = json.load(f)
        
        token = creds.get("access_token")
        member_id = creds.get("member_id")
        
        if not token or not member_id:
            os.remove(creds_path)
            return "Error: Saved credentials are invalid. Please log in again."
    except (json.JSONDecodeError, IOError):
        return "Error: Could not read credentials file."
    
    try:
        service = LinkedInService(token, member_id)
        post_urn = service.create_linkedin_post(text, image_path)
        return {"status": "SUCCESS", "post_urn": post_urn}
    except Exception as e:
        if "unauthorized" in str(e).lower():
            os.remove(creds_path)
            return {"status": "AUTH_REQUIRED", "url": "http://localhost:5000/login"}
        return {"status": "FAILED", "error": str(e)}
