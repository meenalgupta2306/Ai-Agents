"""LinkedIn posting tool"""
import os
import json
from pathlib import Path
from features.linkedin.service import LinkedInService


def linkedin_tool(account_id: str, text: str, user_email: str = "test@example.com", image_path: str = None):
    """
    Posts content to LinkedIn using a specific connected account.
    
    Args:
        account_id: The account ID (URN) from list_connected_accounts
        text: The text content to post
        user_email: Email of the user (defaults to test@example.com)
        image_path: Optional path to image to include in post
        
    Returns:
        Dict with status, message, and post_urn if successful
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    accounts_path = BASE_DIR / "documents" / "json" / "connected_accounts.json"
    
    # Check if connected accounts file exists
    if not os.path.exists(accounts_path):
        return {
            "status": "ERROR",
            "message": "No connected accounts found. Please connect your LinkedIn account first."
        }
    
    try:
        with open(accounts_path, "r") as f:
            accounts_data = json.load(f)
        
        # SECURITY: user_email ensures the user can only access their own accounts
        # This prevents using another user's account_id
        user_accounts = accounts_data.get(user_email, {}).get("accounts", [])
        
        # Find account by account_id within this user's accounts
        target_account = None
        for account in user_accounts:
            if account.get("accountId") == account_id:
                target_account = account
                break
        
        if not target_account:
            return {
                "status": "ERROR",
                "message": f"Account with ID '{account_id}' not found for user {user_email}. Use get_connected_accounts to see available accounts."
            }
        
        # Verify it's a LinkedIn account
        if target_account.get("platform") != "linkedin":
            return {
                "status": "ERROR",
                "message": f"Account '{account_id}' is not a LinkedIn account. Platform: {target_account.get('platform')}"
            }
        
        # Extract credentials
        access_token = target_account.get("accessToken")
        account_urn = target_account.get("accountId")
        
        if not access_token or not account_urn:
            return {
                "status": "ERROR",
                "message": "LinkedIn account found but credentials are incomplete. Please reconnect your account."
            }
        
        # Extract member_id from URN (format: urn:li:person:MEMBER_ID or urn:li:organization:ORG_ID)
        if account_urn.startswith("urn:li:person:"):
            member_id = account_urn.replace("urn:li:person:", "")
        elif account_urn.startswith("urn:li:organization:"):
            member_id = account_urn.replace("urn:li:organization:", "")
        else:
            member_id = account_urn
        
    except (json.JSONDecodeError, IOError) as e:
        return {
            "status": "ERROR",
            "message": f"Could not read connected accounts file: {str(e)}"
        }
    
    # Create LinkedIn post
    try:
        service = LinkedInService(access_token, member_id)
        post_urn = service.create_linkedin_post(text, image_path)
        
        account_name = target_account.get('name', user_email)
        account_type = target_account.get('type', 'account')
        
        return {
            "status": "SUCCESS",
            "post_urn": post_urn,
            "message": f"Successfully posted to LinkedIn {account_type} account: {account_name}",
            "account_name": account_name,
            "account_type": account_type
        }
    except Exception as e:
        error_msg = str(e)
        if "unauthorized" in error_msg.lower() or "401" in error_msg:
            return {
                "status": "AUTH_EXPIRED",
                "message": "LinkedIn access token has expired. Please reconnect your LinkedIn account."
            }
        return {
            "status": "FAILED",
            "error": error_msg,
            "message": f"Failed to post to LinkedIn: {error_msg}"
        }
