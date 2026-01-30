"""Connected accounts tool"""
import json
from features.oauth.service import OAuthService


def accounts_tool(user_email: str) -> str:
    """Gets all connected social media accounts for a user."""
    try:
        oauth_service = OAuthService()
        accounts = oauth_service.get_user_accounts(user_email)
        
        # Remove sensitive data
        safe_accounts = []
        for account in accounts:
            safe_account = {
                "platform": account.get("platform"),
                "type": account.get("type"),
                "name": account.get("name"),
                "accountId": account.get("accountId"),
                "email": account.get("email"),
                "vanityName": account.get("vanityName"),
            }
            safe_accounts.append(safe_account)
        
        if not safe_accounts:
            return json.dumps({
                "status": "SUCCESS",
                "message": "No connected accounts found.",
                "accounts": []
            })
        
        return json.dumps({
            "status": "SUCCESS",
            "accounts": safe_accounts,
            "count": len(safe_accounts)
        })
    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "error": str(e)
        })
