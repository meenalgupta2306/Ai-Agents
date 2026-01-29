import requests
from typing import Optional
import os
from rich.console import Console


BASE_URL = "https://api.linkedin.com/v2"

console = Console(stderr=True)

class LinkedInService:
    def __init__(self, token: str, member_id: str = None):
        if not token:
            raise ValueError("LinkedIn access token is required")
        self.token = token
        self.member_id = member_id
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202511",
            "Content-Type": "application/json",
        }
    
    def get_profile(self) -> dict:
        """Get user profile information including email"""
        try:
            # Get basic profile

            print("\n\n calaling")
            print(f"{BASE_URL}/me")
            profile_resp = requests.get(
                f"{BASE_URL}/me",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            profile_resp.raise_for_status()
            profile = profile_resp.json()
            
            
            return {
                "urn": f"urn:li:person:{profile.get('id')}",
                "id": profile.get("id"),
                "name": f"{profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}".strip(),
                "firstName": profile.get("localizedFirstName"),
                "lastName": profile.get("localizedLastName"),
            }
        except Exception as e:
            console.print(f"❌ Error fetching profile: {str(e)}")
            raise
    
    def get_organizations(self) -> list:
        """Get list of organizations where user has admin access"""
        try:
            # Step 1: Get organization ACLs (admin access)
            # We use the same parameters as agentweb: q=roleAssignee, role=ADMINISTRATOR, state=APPROVED
            acl_resp = requests.get(
                f"{BASE_URL}/organizationAcls",
                params={
                    "q": "roleAssignee",
                    "role": "ADMINISTRATOR",
                    "state": "APPROVED"
                },
                headers=self.headers,
                timeout=10
            )
            acl_resp.raise_for_status()
            acl_data = acl_resp.json()
            
            organizations = []
            for element in acl_data.get("elements", []):
                # Organization URN can be in 'organization' or 'organizationTarget'
                org_urn = element.get("organization") or element.get("organizationTarget")
                if not org_urn:
                    continue
                
                org_id = org_urn.replace("urn:li:organization:", "")
                
                # Step 2: Get organization details
                try:
                    org_resp = requests.get(
                        f"{BASE_URL}/organizations/{org_id}",
                        headers=self.headers,
                        timeout=10
                    )
                    org_resp.raise_for_status()
                    org_data = org_resp.json()
                    
                    # Extract logo URL - matching agentweb logic
                    logo_url = None
                    logo_v2 = org_data.get("logoV2", {})
                    if logo_v2:
                        # Try original or cropped-mini as per agentweb
                        logo_url = logo_v2.get("original") or logo_v2.get("cropped-mini")
                    
                    organizations.append({
                        "urn": org_urn,
                        "id": org_id,
                        "name": org_data.get("localizedName") or org_data.get("name", {}).get("localized", {}).get("en_US") or f"Organization {org_id}",
                        "vanityName": org_data.get("vanityName"),
                        "logoUrl": logo_url
                    })
                except Exception as org_err:
                    console.print(f"⚠️ Warning: Could not fetch details for organization {org_urn}: {str(org_err)}")
                    # Add basic info if details fetch fails
                    organizations.append({
                        "urn": org_urn,
                        "id": org_id,
                        "name": f"Organization {org_id}",
                        "vanityName": None,
                        "logoUrl": None
                    })
            
            return organizations
        except Exception as e:
            console.print(f"❌ Error fetching organizations: {str(e)}")
            return []

    def upload_image(self, image_path: str) -> str:
        import mimetypes
        import os
        
        filename = os.path.basename(image_path)
        file_type, _ = mimetypes.guess_type(filename)
        file_type = file_type or "image/png"

        # Ensure member_id isn't already a full URN
        owner_urn = self.member_id if self.member_id.startswith("urn:li:") else f"urn:li:person:{self.member_id}"

        # Use the full headers from self.headers to ensure Protocol Version is present
        payload = {
            "initializeUploadRequest": {
                "owner": owner_urn
            }
        }

        # Step 1: Initialize
        # We use self.headers which includes X-Restli-Protocol-Version: 2.0.0
        
        try:
            resp = requests.post(
            f"{BASE_URL}/images?action=initializeUpload",
            headers=self.headers,
            json=payload
        )
        except Exception as e:
            console.print("errorrrrrrrrrr", e)
        
        
        if resp.status_code != 200:
            console.print(f"Init Failed: {resp.text}") # This will tell you EXACTLY what is wrong
            resp.raise_for_status()

        value = resp.json()["value"]
        upload_url = value["uploadUrl"]
        image_urn = value["image"]

        with open(image_path, "rb") as f:
            put_resp = requests.put(upload_url, data=f, headers={"Content-Type": "image/png"})
            put_resp.raise_for_status()

        return image_urn

    def create_linkedin_post(
        self,
        text: str,
        image_path: Optional[str] = None
    ) -> str:
        """
        Create a LinkedIn post. Optional image can be attached.
        Returns the post URN.
        """
        media_urn = None
        
        if image_path:
            # 1. Check if the path exists and is a file
            if not os.path.isfile(image_path):
                console.print(f"⚠️ Error: Image path '{image_path}' does not exist or is not a file.")
              
            
            # 2. Check if the file is not empty
            elif os.path.getsize(image_path) == 0:
                console.print(f"⚠️ Error: Image file '{image_path}' is empty.")
            
            else:
                console.print(f"✅ Image verified at {image_path}. Calling upload image...")
                media_urn = self.upload_image(image_path)
        # -------------------------

        payload = {
            "author": f"urn:li:person:{self.member_id}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED"
        }

        if media_urn:
            payload["content"] = {
                "media": {
                    "id": media_urn
                }
            }

        console.print(f"📤 Creating post with payload:")
        console.print(f"Author URN: {payload['author']}")
        console.print(f"Member ID used: {self.member_id}")

        try:
            resp = requests.post(
                f"{BASE_URL}/posts",
                headers=self.headers,
                json=payload
            )
            
            console.print(f"📥 Response Status: {resp.status_code}")
            console.print(f"📥 Response Headers: {dict(resp.headers)}")
            console.print(f"📥 Response Body: {resp.text}")
            
            resp.raise_for_status()
            return resp.headers.get("x-restli-id")
        except Exception as e:
            console.print(f"❌ Error creating post: {str(e)}")
            console.print(f"❌ Response text: {resp.text if 'resp' in locals() else 'No response'}")
            return f"Error: {str(e)}"
