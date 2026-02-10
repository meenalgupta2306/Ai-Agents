"""Meta Marketing API Controller - Business Logic Layer"""
import os
import json
from pathlib import Path
from flask import session, request
from .service import MetaService
from rich.console import Console

console = Console(stderr=True)


class MetaController:
    """Controller for Meta Marketing API operations"""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.accounts_path = self.base_dir / "documents" / "json" / "connected_accounts.json"
    
    def _load_connected_accounts(self):
        """Load connected accounts from JSON file"""
        if not os.path.exists(self.accounts_path):
            return {}
        
        try:
            with open(self.accounts_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            console.print(f"❌ Error loading connected accounts: {str(e)}")
            return {}
    
    def _get_meta_account(self, user_email: str, account_id: str):
        """Get Meta account credentials for a user"""
        accounts_data = self._load_connected_accounts()
        user_accounts = accounts_data.get(user_email, {}).get("accounts", [])
        
        for account in user_accounts:
            if account.get("accountId") == account_id and account.get("platform") == "meta":
                return account
        
        return None
    
    def create_campaign(self):
        """Create a Meta campaign"""
        try:
            data = request.json
            
            # Extract parameters
            account_id = data.get("accountId")
            campaign_name = data.get("name")
            objective = data.get("objective")
            status = data.get("status", "PAUSED")
            special_ad_categories = data.get("specialAdCategories", [])
            
            # Validate required fields
            if not account_id:
                return {"success": False, "error": "Account ID is required"}, 400
            if not campaign_name:
                return {"success": False, "error": "Campaign name is required"}, 400
            if not objective:
                return {"success": False, "error": "Campaign objective is required"}, 400
            
            # Get user from session
            user = session.get("user", {})
            user_email = user.get("email", "test@example.com")
            
            # Get Meta account credentials
            meta_account = self._get_meta_account(user_email, account_id)
            if not meta_account:
                return {
                    "success": False,
                    "error": f"Meta account '{account_id}' not found for user {user_email}"
                }, 404
            
            access_token = meta_account.get("accessToken")
            if not access_token:
                return {
                    "success": False,
                    "error": "Access token not found. Please reconnect your Meta account."
                }, 401
            
            # Create campaign using MetaService
            service = MetaService(access_token, account_id)
            result = service.create_campaign(
                name=campaign_name,
                objective=objective,
                status=status,
                special_ad_categories=special_ad_categories
            )
            
            return {
                "success": True,
                "campaign": result,
                "message": f"Campaign '{campaign_name}' created successfully"
            }, 201
            
        except ValueError as e:
            return {"success": False, "error": str(e)}, 400
        except Exception as e:
            console.print(f"❌ Error in create_campaign controller: {str(e)}")
            return {"success": False, "error": str(e)}, 500
    
    def get_campaigns(self):
        """Get campaigns for a Meta ad account"""
        try:
            account_id = request.args.get("accountId")
            
            if not account_id:
                return {"success": False, "error": "Account ID is required"}, 400
            
            # Get user from session
            user = session.get("user", {})
            user_email = user.get("email", "test@example.com")
            
            # Get Meta account credentials
            meta_account = self._get_meta_account(user_email, account_id)
            if not meta_account:
                return {
                    "success": False,
                    "error": f"Meta account '{account_id}' not found"
                }, 404
            
            access_token = meta_account.get("accessToken")
            if not access_token:
                return {
                    "success": False,
                    "error": "Access token not found. Please reconnect your Meta account."
                }, 401
            
            # Get campaigns using MetaService
            service = MetaService(access_token, account_id)
            campaigns = service.get_campaigns()
            
            return {
                "success": True,
                "campaigns": campaigns,
                "count": len(campaigns)
            }, 200
            
        except Exception as e:
            console.print(f"❌ Error in get_campaigns controller: {str(e)}")
            return {"success": False, "error": str(e)}, 500
