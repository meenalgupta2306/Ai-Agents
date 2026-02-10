"""OAuth controller - handles business logic"""
from flask import session, request
from .service import OAuthService
from features.linkedin.service import LinkedInService
import requests
import uuid
from config.settings import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, META_APP_ID, META_APP_SECRET, META_REDIRECT_URI


class OAuthController:
    """OAuth business logic controller"""
    
    def __init__(self):
        self.oauth_service = OAuthService()
    
    def linkedin_oauth_init(self):
        """Initialize LinkedIn OAuth flow"""
        try:
            state = str(uuid.uuid4())
            session["oauth_state"] = state
            auth_url = self.oauth_service.get_linkedin_auth_url(state)
            return {"success": True, "url": auth_url}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
            
    def meta_oauth_init(self):
        """Initialize Meta OAuth flow"""
        try:
            state = str(uuid.uuid4())
            session["oauth_state"] = state
            auth_url = self.oauth_service.get_meta_auth_url(state)
            return {"success": True, "url": auth_url}, 200
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def linkedin_oauth_finalize(self):
        """Finalize LinkedIn OAuth"""
        try:
            data = request.json
            code = data.get("code")
            state = data.get("state")
            
            if not code:
                return {"success": False, "error": "Authorization code not provided"}, 400
            
            expected_state = session.get("oauth_state")
            if state != expected_state:
                return {"success": False, "error": "Invalid OAuth state"}, 403
            
            # Exchange code for token
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
            
            if not access_token:
                return {"success": False, "error": "Failed to get access token"}, 400
            
            linkedin_service = LinkedInService(access_token)
            
            # Get profile
            profile = None
            try:
                profile = linkedin_service.get_profile()
            except Exception as profile_error:
                profile = {
                    "urn": f"urn:li:person:unknown",
                    "name": "LinkedIn User",
                    "id": "unknown"
                }
            
            # Get organizations
            organizations = []
            try:
                organizations = linkedin_service.get_organizations()
            except Exception as org_error:
                print(f"⚠️ Error fetching organizations: {org_error}")
            
            # Store token in session
            token_session_id = str(uuid.uuid4())
            session[f"linkedin_token_{token_session_id}"] = access_token
            
            return {
                "success": True,
                "profile": profile,
                "organizations": organizations,
                "tokenSessionId": token_session_id
            }, 200
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def meta_oauth_finalize(self):
        """Finalize Meta OAuth"""
        try:
            data = request.json
            code = data.get("code")
            state = data.get("state")
            
            if not code:
                return {"success": False, "error": "Authorization code not provided"}, 400
            
            # expected_state = session.get("oauth_state")
            # if state and state != expected_state:
            #     return {"success": False, "error": "Invalid OAuth state"}, 403
            
            # Exchange code for token
            token_resp = requests.get(
                "https://graph.facebook.com/v18.0/oauth/access_token",
                params={
                    "client_id": META_APP_ID,
                    "redirect_uri": META_REDIRECT_URI,
                    "client_secret": META_APP_SECRET,
                    "code": code
                },
                timeout=10
            )
            
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return {"success": False, "error": f"Failed to get access token: {token_data.get('error', {}).get('message')}"}, 400
            
            # Get user profile
            profile_resp = requests.get(
                "https://graph.facebook.com/v18.0/me",
                params={
                    "fields": "id,name,email,picture",
                    "access_token": access_token
                },
                timeout=10
            )
            profile_data = profile_resp.json()
            
            profile = {
                "id": profile_data.get("id"),
                "name": profile_data.get("name"),
                "email": profile_data.get("email"),
                "picture": profile_data.get("picture", {}).get("data", {}).get("url")
            }
            
            # Get ad accounts
            ad_accounts_resp = requests.get(
                "https://graph.facebook.com/v18.0/me/adaccounts",
                params={
                    "fields": "id,name,account_id,currency",
                    "access_token": access_token
                },
                timeout=10
            )
            ad_accounts_data = ad_accounts_resp.json()
            ad_accounts = ad_accounts_data.get("data", [])
            
            # Store token in session
            token_session_id = str(uuid.uuid4())
            session[f"meta_token_{token_session_id}"] = access_token
            
            return {
                "success": True,
                "profile": profile,
                "adAccounts": ad_accounts,
                "tokenSessionId": token_session_id
            }, 200
            
        except Exception as e:
            print(f"Error in meta_oauth_finalize: {str(e)}")
            return {"success": False, "error": str(e)}, 500

    def connect_linkedin_accounts(self):
        """Connect selected LinkedIn accounts"""
        try:
            data = request.json
            personal = data.get("personal", False)
            organizations = data.get("organizations", [])
            profile = data.get("profile", {})
            token_session_id = data.get("tokenSessionId")
            
            token_key = f"linkedin_token_{token_session_id}"
            access_token = session.get(token_key)
            
            if not access_token:
                return {"success": False, "error": "OAuth session expired. Please try again."}, 400
            
            user = session.get("user", {})
            user_email = user.get("email", "test@example.com")
            
            connected_accounts = []
            
            if personal:
                account = {
                    "platform": "linkedin",
                    "type": "personal",
                    "name": profile.get("name"),
                    "email": profile.get("email"),
                    "accountId": profile.get("urn"),
                    "accessToken": access_token,
                    "picture": profile.get("picture")
                }
                self.oauth_service.add_account(user_email, account)
                connected_accounts.append(account)
            
            for org in organizations:
                account = {
                    "platform": "linkedin",
                    "type": "organization",
                    "name": org.get("name"),
                    "accountId": org.get("urn"),
                    "accessToken": access_token,
                    "vanityName": org.get("vanityName"),
                    "logoUrl": org.get("logoUrl")
                }
                self.oauth_service.add_account(user_email, account)
                connected_accounts.append(account)
            
            session.pop(token_key, None)
            
            return {"success": True, "accounts": connected_accounts}, 200
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def connect_meta_accounts(self):
        """Connect selected Meta accounts"""
        try:
            data = request.json
            personal = data.get("personal", False) # Meta doesn't really have "personal" ad accounts in the same way, but checking for profile connection
            ad_accounts = data.get("adAccounts", [])
            profile = data.get("profile", {})
            token_session_id = data.get("tokenSessionId")
            
            token_key = f"meta_token_{token_session_id}"
            access_token = session.get(token_key)
            
            if not access_token:
                return {"success": False, "error": "OAuth session expired. Please try again."}, 400
            
            user = session.get("user", {})
            user_email = user.get("email", "test@example.com")
            
            connected_accounts = []
            
            # If user wants to connect their personal profile identity (maybe for pages later?)
            if personal:
                account = {
                    "platform": "meta",
                    "type": "personal", 
                    "name": profile.get("name"),
                    "email": profile.get("email"),
                    "accountId": profile.get("id"),
                    "accessToken": access_token,
                    "picture": profile.get("picture")
                }
                self.oauth_service.add_account(user_email, account)
                connected_accounts.append(account)
            
            for ad_account in ad_accounts:
                account = {
                    "platform": "meta",
                    "type": "ad_account",
                    "name": ad_account.get("name"),
                    "accountId": ad_account.get("id"), # act_ID
                    "accessToken": access_token,
                    "currency": ad_account.get("currency")
                }
                self.oauth_service.add_account(user_email, account)
                connected_accounts.append(account)
            
            session.pop(token_key, None)
            
            return {"success": True, "accounts": connected_accounts}, 200
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500

    def get_connected_accounts(self):
        """Get all connected accounts"""
        try:
            user = session.get("user", {})
            user_email = user.get("email", "test@example.com")
            
            accounts = self.oauth_service.get_user_accounts(user_email)
            
            safe_accounts = []
            for account in accounts:
                safe_account = {k: v for k, v in account.items() if k != "accessToken"}
                safe_accounts.append(safe_account)
            
            return {"success": True, "accounts": safe_accounts}, 200
            
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def delete_connected_account(self, platform, account_id):
        """Delete a connected account"""
        try:
            user = session.get("user", {})
            user_email = user.get("email", "test@example.com")
            
            success = self.oauth_service.delete_account(user_email, platform, account_id)
            
            if success:
                return {"success": True, "message": "Account disconnected successfully"}, 200
            else:
                return {"success": False, "error": "Account not found"}, 404
                
        except Exception as e:
            return {"success": False, "error": str(e)}, 500
    
    def get_userinfo(self):
        """Get user info"""
        user = session.get("user")
        if not user:
            return {"error": "Not authenticated"}, 401
        return user, 200
