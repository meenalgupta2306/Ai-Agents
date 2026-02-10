"""Meta Marketing API Service"""
import requests
from typing import Optional, List, Dict
from rich.console import Console

BASE_URL = "https://graph.facebook.com/v18.0"

console = Console(stderr=True)


class MetaService:
    """Service for interacting with Meta Marketing API"""
    
    def __init__(self, access_token: str, ad_account_id: str = None):
        """
        Initialize Meta service
        
        Args:
            access_token: Meta OAuth access token
            ad_account_id: Ad account ID (format: act_123456789)
        """
        if not access_token:
            raise ValueError("Meta access token is required")
        
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.params = {"access_token": self.access_token}
    
    def get_ad_accounts(self) -> List[Dict]:
        """
        Get list of ad accounts accessible by the user
        
        Returns:
            List of ad account dictionaries
        """
        try:
            response = requests.get(
                f"{BASE_URL}/me/adaccounts",
                params={
                    **self.params,
                    "fields": "id,name,account_id,currency,account_status"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            console.print(f"❌ Error fetching ad accounts: {str(e)}")
            raise
    
    def create_campaign(
        self,
        name: str,
        objective: str,
        status: str = "PAUSED",
        special_ad_categories: Optional[List[str]] = None
    ) -> Dict:
        """
        Create a new Meta campaign
        
        Args:
            name: Campaign name
            objective: Campaign objective (e.g., OUTCOME_TRAFFIC, OUTCOME_LEADS, OUTCOME_SALES)
            status: Campaign status (ACTIVE, PAUSED, ARCHIVED)
            special_ad_categories: List of special ad categories (e.g., ["EMPLOYMENT"])
        
        Returns:
            Dictionary with campaign id and success status
        """
        if not self.ad_account_id:
            raise ValueError("Ad account ID is required to create a campaign")
        
        # Validate objective
        valid_objectives = [
            "OUTCOME_TRAFFIC",
            "OUTCOME_ENGAGEMENT", 
            "OUTCOME_LEADS",
            "OUTCOME_SALES",
            "OUTCOME_APP_PROMOTION",
            "OUTCOME_AWARENESS"
        ]
        if objective not in valid_objectives:
            raise ValueError(f"Invalid objective. Must be one of: {', '.join(valid_objectives)}")
        
        # Validate status
        valid_statuses = ["ACTIVE", "PAUSED", "ARCHIVED"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        payload = {
            "name": name,
            "objective": objective,
            "status": status,
            "special_ad_categories": special_ad_categories or [],
            "access_token": self.access_token,
            "is_adset_budget_sharing_enabled": False
        }
        
        try:
            console.print(f"📤 Creating campaign '{name}' with objective '{objective}'")
            
            response = requests.post(
                f"{BASE_URL}/{self.ad_account_id}/campaigns",
                json=payload,
                timeout=10
            )
            
            console.print(f"📥 Response Status: {response.status_code}")
            console.print(f"📥 Response Body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            console.print(f"✅ Campaign created successfully: {result.get('id')}")
            return result
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.text if e.response else str(e)}"
            console.print(f"❌ Error creating campaign: {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            console.print(f"❌ Error creating campaign: {str(e)}")
            raise
    
    def get_campaigns(self, fields: Optional[List[str]] = None) -> List[Dict]:
        """
        Get list of campaigns for the ad account
        
        Args:
            fields: List of fields to retrieve (default: id, name, objective, status)
        
        Returns:
            List of campaign dictionaries
        """
        if not self.ad_account_id:
            raise ValueError("Ad account ID is required to get campaigns")
        
        default_fields = ["id", "name", "objective", "status", "created_time", "updated_time"]
        fields_str = ",".join(fields or default_fields)
        
        try:
            response = requests.get(
                f"{BASE_URL}/{self.ad_account_id}/campaigns",
                params={
                    **self.params,
                    "fields": fields_str
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            console.print(f"❌ Error fetching campaigns: {str(e)}")
            raise
