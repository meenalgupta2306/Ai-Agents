"""LinkedIn controller - handles business logic"""
from flask import session, request
from .service import LinkedInService
import os
import json
from datetime import datetime


class LinkedInController:
    """LinkedIn business logic controller"""
    
    @staticmethod
    def create_post():
        """Create a LinkedIn post"""
        token = session.get("linkedin_access_token")
        member_id = session.get("member_id") or "ME"

        if not token or not member_id:
            return {"error": "Not authenticated"}, 401

        data = request.json or {}
        text = "This is a sample LinkedIn post created via API."
        image_path = None

        service = LinkedInService(token, member_id)
        post_urn = service.create_linkedin_post(text, image_path)
        
        # Save post to JSON storage
        if post_urn and not post_urn.startswith("Error"):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            posts_file = os.path.join(base_dir, "..", "..", "documents", "json", "posts_storage.json")
            
            try:
                with open(posts_file, 'r') as f:
                    posts = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                posts = []
            
            post_data = {
                "id": post_urn,
                "urn": post_urn,
                "text": text,
                "timestamp": datetime.now().isoformat(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            posts.append(post_data)
            
            with open(posts_file, 'w') as f:
                json.dump(posts, f, indent=2)

        return {"postUrn": post_urn}, 200
    
    @staticmethod
    def delete_post():
        """Delete a LinkedIn post"""
        import requests
        from urllib.parse import quote
        
        token = session.get("linkedin_access_token")
        data = request.get_json(silent=True) or {}
        post_urn = data.get("postUrn")

        if not token or not post_urn:
            return {"error": "Missing token or postUrn"}, 400

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202506"
        }
        encoded_urn = quote(post_urn, safe="")
        url = f"https://api.linkedin.com/rest/posts/{encoded_urn}"

        resp = requests.delete(url, headers=headers, timeout=10)

        # Remove from storage if successful
        if resp.status_code in [200, 204]:
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                posts_file = os.path.join(base_dir, "..", "..", "documents", "json", "posts_storage.json")
                
                with open(posts_file, 'r') as f:
                    posts = json.load(f)
                
                posts = [post for post in posts if post.get("urn") != post_urn]
                
                with open(posts_file, 'w') as f:
                    json.dump(posts, f, indent=2)
            except Exception as e:
                print(f"⚠️ Error removing from storage: {e}")

        try:
            response_data = resp.json()
        except ValueError:
            response_data = {
                "status": resp.status_code,
                "message": "Post deleted successfully" if resp.status_code in [200, 204] else "Failed to delete post"
            }

        return response_data, resp.status_code
    
    @staticmethod
    def get_profile_analytics():
        """Get profile analytics"""
        import requests
        
        token = session.get("linkedin_access_token")
        if not token:
            return {"error": "Not authenticated"}, 401
        
        headers = {
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": "202506",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }
        
        try:
            url = "https://api.linkedin.com/rest/memberFollowersCount"
            params = {"q": "me"}
            
            resp = requests.get(url, headers=headers, params=params, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                followers = data.get("elements", [{}])[0].get("memberFollowersCount", 0)
                return {"followers": followers}, 200
            else:
                return {"error": "LinkedIn API Error", "details": resp.text}, resp.status_code
                
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_post_analytics():
        """Get aggregated post analytics"""
        import requests
        from datetime import datetime, timedelta
        
        token = session.get("linkedin_access_token")
        if not token:
            return {"error": "Not authenticated"}, 401
        
        headers = {
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": "202506",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        try:
            if not end_date:
                end = datetime.now()
            else:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                
            if not start_date:
                start = end - timedelta(days=30)
            else:
                start = datetime.strptime(start_date, '%Y-%m-%d')
            
            date_range = f"(start:(day:{start.day},month:{start.month},year:{start.year}),end:(day:{end.day},month:{end.month},year:{end.year}))"
            
            metrics = ["IMPRESSION", "MEMBERS_REACHED"]
            analytics_data = {}
            
            for metric in metrics:
                url = f"https://api.linkedin.com/rest/memberCreatorPostAnalytics?q=me&queryType={metric}&aggregation=TOTAL&dateRange={date_range}"
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    total_count = sum(element.get("count", 0) for element in data.get("elements", []))
                    analytics_data[metric.lower()] = total_count
                else:
                    analytics_data[metric.lower()] = 0
            
            return analytics_data, 200
                
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_posts():
        """Get all posts from storage"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            posts_file = os.path.join(base_dir, "..", "..", "documents", "json", "posts_storage.json")
            
            try:
                with open(posts_file, 'r') as f:
                    posts = json.load(f)
                return posts[::-1], 200
            except (FileNotFoundError, json.JSONDecodeError):
                return [], 200
                
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_post_analytics_by_id(post_id):
        """Get analytics for specific post"""
        import requests
        import urllib.parse
        
        token = session.get("linkedin_access_token")
        if not token:
            return {"error": "Not authenticated"}, 401
        
        headers = {
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": "202506",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        try:
            if post_id.startswith("urn:li:share:"):
                entity_param = f"(share:{urllib.parse.quote(post_id, safe='')})"
            elif post_id.startswith("urn:li:ugcPost:"):
                entity_param = f"(ugc:{urllib.parse.quote(post_id, safe='')})"
            else:
                return {"error": "Invalid post URN format"}, 400
            
            metrics = ["IMPRESSION", "MEMBERS_REACHED", "REACTION", "COMMENT", "RESHARE"]
            analytics_data = {}
            
            for metric in metrics:
                url = f"https://api.linkedin.com/rest/memberCreatorPostAnalytics?q=entity&entity={entity_param}&queryType={metric}&aggregation=TOTAL"
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    data = resp.json()
                    total_count = sum(element.get("count", 0) for element in data.get("elements", []))
                    analytics_data[metric.lower()] = total_count
                else:
                    analytics_data[metric.lower()] = 0
            
            return analytics_data, 200
                
        except Exception as e:
            return {"error": str(e)}, 500
