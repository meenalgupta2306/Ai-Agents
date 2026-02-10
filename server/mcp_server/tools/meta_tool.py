"""Meta Marketing API MCP Tool"""
import os
import json
from pathlib import Path
from features.meta.service import MetaService


def create_meta_campaign_tool(
    account_id: str,
    campaign_name: str,
    objective: str,
    user_email: str = "test@example.com",
    status: str = "PAUSED",
    special_ad_categories: list = None
):
    """
    Create a Meta (Facebook/Instagram) advertising campaign.
    
    Args:
        account_id: The Meta ad account ID (format: act_123456789) from connected accounts
        campaign_name: Name for the campaign
        objective: Campaign objective (OUTCOME_TRAFFIC, OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_ENGAGEMENT, OUTCOME_APP_PROMOTION, OUTCOME_AWARENESS)
        user_email: Email of the user (defaults to test@example.com)
        status: Campaign status - ACTIVE, PAUSED, or ARCHIVED (default: PAUSED)
        special_ad_categories: List of special ad categories like ["EMPLOYMENT", "HOUSING", "CREDIT"] (default: [])
        
    Returns:
        Dict with status, message, and campaign_id if successful
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    accounts_path = BASE_DIR / "documents" / "json" / "connected_accounts.json"
    
    # Check if connected accounts file exists
    if not os.path.exists(accounts_path):
        return {
            "status": "ERROR",
            "message": "No connected accounts found. Please connect your Meta account first."
        }
    
    try:
        with open(accounts_path, "r") as f:
            accounts_data = json.load(f)
        
        # Get user's accounts
        user_accounts = accounts_data.get(user_email, {}).get("accounts", [])
        
        # Find Meta account by account_id
        target_account = None
        for account in user_accounts:
            if account.get("accountId") == account_id and account.get("platform") == "meta":
                target_account = account
                break
        
        if not target_account:
            return {
                "status": "ERROR",
                "message": f"Meta account with ID '{account_id}' not found for user {user_email}. Use get_connected_accounts to see available accounts."
            }
        
        # Extract credentials
        access_token = target_account.get("accessToken")
        
        if not access_token:
            return {
                "status": "ERROR",
                "message": "Meta account found but access token is missing. Please reconnect your account."
            }
        
    except (json.JSONDecodeError, IOError) as e:
        return {
            "status": "ERROR",
            "message": f"Could not read connected accounts file: {str(e)}"
        }
    
    # Create campaign
    try:
        service = MetaService(access_token, account_id)
        result = service.create_campaign(
            name=campaign_name,
            objective=objective,
            status=status,
            special_ad_categories=special_ad_categories or []
        )
        
        account_name = target_account.get('name', 'Meta Ad Account')
        
        return {
            "status": "SUCCESS",
            "campaign_id": result.get("id"),
            "message": f"Successfully created campaign '{campaign_name}' in {account_name}",
            "account_name": account_name,
            "objective": objective,
            "campaign_status": status
        }
    except ValueError as e:
        return {
            "status": "VALIDATION_ERROR",
            "error": str(e),
            "message": f"Invalid input: {str(e)}"
        }
    except Exception as e:
        error_msg = str(e)
        if "unauthorized" in error_msg.lower() or "190" in error_msg:
            return {
                "status": "AUTH_EXPIRED",
                "message": "Meta access token has expired. Please reconnect your Meta account."
            }
        return {
            "status": "FAILED",
            "error": error_msg,
            "message": f"Failed to create campaign: {error_msg}"
        }
