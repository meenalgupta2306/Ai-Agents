"""OAuth service for managing social media account connections"""
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), "documents", "json", "connected_accounts.json")


class OAuthService:
    """Service for managing OAuth flows and connected accounts"""
    
    def __init__(self):
        self.linkedin_client_id = os.getenv("CLIENT_ID")
        self.linkedin_client_secret = os.getenv("CLIENT_SECRET")
        self.linkedin_redirect_uri = os.getenv("REDIRECT_URI")
    
    def get_linkedin_auth_url(self, state: str = None) -> str:
        """Generate LinkedIn OAuth authorization URL"""
        import urllib.parse
        
        # Updated scopes for unified flow
        scopes = [
            'r_basicprofile',
      
            #  Personal Account Permissions
            'w_member_social',              # Create/modify posts on personal profile
            'r_member_postAnalytics',       # Retrieve personal post analytics
            'r_member_profileAnalytics',    # Retrieve personal profile analytics
            'r_1st_connections_size',       # Retrieve connection count
            'w_member_social_feed',         # Manage personal post comments/reactions

            # Organization Account Permissions
            'r_organization_social',        # Read organization posts and data
            'rw_organization_admin',        # Manage organization pages
            'w_organization_social',        # Create/modify organization posts
            'r_organization_followers',     # Access follower data
            'w_organization_social_feed',   # Manage organization post comments/reactions
            'r_organization_social_feed'    # Read organization engagement data
        ]
        
        params = {
            "response_type": "code",
            "client_id": self.linkedin_client_id,
            "redirect_uri": self.linkedin_redirect_uri,
            "scope": " ".join(scopes),
            "state": state or str(uuid.uuid4()),
            "prompt": "login"
        }
        
        return "https://www.linkedin.com/oauth/v2/authorization?" + urllib.parse.urlencode(params)
    
    def load_accounts(self) -> Dict:
        """Load all connected accounts from JSON file"""
        try:
            with open(ACCOUNTS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_accounts(self, accounts: Dict):
        """Save connected accounts to JSON file"""
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
    
    def get_user_accounts(self, user_email: str) -> List[Dict]:
        """Get all connected accounts for a user"""
        all_accounts = self.load_accounts()
        user_data = all_accounts.get(user_email, {})
        return user_data.get("accounts", [])
    
    def add_account(self, user_email: str, account: Dict) -> Dict:
        """Add a connected account for a user"""
        all_accounts = self.load_accounts()
        
        if user_email not in all_accounts:
            all_accounts[user_email] = {"accounts": []}
        
        # Check if account already exists
        existing = [a for a in all_accounts[user_email]["accounts"] 
                   if a.get("accountId") == account.get("accountId")]
        
        if existing:
            # Update existing account
            for i, a in enumerate(all_accounts[user_email]["accounts"]):
                if a.get("accountId") == account.get("accountId"):
                    all_accounts[user_email]["accounts"][i] = account
                    break
        else:
            # Add new account
            account["id"] = str(uuid.uuid4())
            account["connectedAt"] = datetime.now().isoformat()
            all_accounts[user_email]["accounts"].append(account)
        
        self.save_accounts(all_accounts)
        return account
    
    def delete_account(self, user_email: str, platform: str, account_id: str) -> bool:
        """Delete a connected account"""
        all_accounts = self.load_accounts()
        
        if user_email not in all_accounts:
            return False
        
        accounts = all_accounts[user_email]["accounts"]
        original_count = len(accounts)
        
        # Filter out the account to delete
        all_accounts[user_email]["accounts"] = [
            a for a in accounts 
            if not (a.get("platform") == platform and a.get("accountId") == account_id)
        ]
        
        if len(all_accounts[user_email]["accounts"]) < original_count:
            self.save_accounts(all_accounts)
            return True
        
        return False
    
    def find_account(self, user_email: str, platform: str, account_id: str) -> Optional[Dict]:
        """Find a specific connected account"""
        accounts = self.get_user_accounts(user_email)
        for account in accounts:
            if account.get("platform") == platform and account.get("accountId") == account_id:
                return account
        return None
