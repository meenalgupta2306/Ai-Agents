from flask import Blueprint, session, request, jsonify
from mcpServer.services.linkedin import LinkedInService
from oauth_service import OAuthService
from urllib.parse import quote
import requests
import os
import uuid

api_blueprint = Blueprint("api", __name__, url_prefix="/api")
oauth_service = OAuthService()


@api_blueprint.route("/userinfo")
def get_userinfo():
    user = session.get("user")
    print(user)
    if not user:
        return {"error": "Not authenticated"}, 401
    return user


# @api_blueprint.route("/linkedin/post", methods=["POST"])
# def create_post():
#     token = session.get("linkedin_access_token")
#     member_id = session.get("member_id")

#     print(token)
#     if not token or not member_id:
#         return {"error": "Not authenticated"}, 401

#     data = request.json or {}
#     text = data.get("text")

#     # Pick the image from documents folder
#     base_dir = os.path.dirname(os.path.abspath(__file__))

#     image_path = os.path.join(base_dir, "documents", "ai.jpeg")

#     print(text)
#     service = LinkedInService(token, member_id)
#     print("callingg........................")
#     post_urn = service.create_linkedin_post(text, image_path)

#     return jsonify({
#         "postUrn": post_urn
#     }), 200


@api_blueprint.route("/linkedin/post", methods=["POST"])
def create_post():
    token = session.get("linkedin_access_token")
    member_id = session.get("member_id") or "ME"

    print(member_id,"+++++++++++++++++++++++++++++++++")
    if not token or not member_id:
        return {"error": "Not authenticated"}, 401

    print("-------------------------------")
    data = request.json or {}
    # text = data.get("text")
    text ="This is a sample LinkedIn post created via API."

    # Pick the image from documents folder
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # image_path = os.path.join(base_dir, "documents", "ai.jpeg")
    image_path = None


    service = LinkedInService(token, member_id)
    print("callingg........................")
    post_urn = service.create_linkedin_post(text, image_path)


    print(f"✅ Post created with URN: {post_urn}-------------------------------")
    # Save post to JSON storage
    if post_urn and not post_urn.startswith("Error"):
        import json
        from datetime import datetime
        
        posts_file = os.path.join(base_dir, "posts_storage.json")
        
        # Read existing posts
        try:
            with open(posts_file, 'r') as f:
                posts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            posts = []
        
        # Add new post
        post_data = {
            "id": post_urn,
            "urn": post_urn,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        posts.append(post_data)
        
        # Save back to file
        with open(posts_file, 'w') as f:
            json.dump(posts, f, indent=2)
        
        print(f"✅ Post saved to storage: {post_urn}")

    return jsonify({
        "postUrn": post_urn
    }), 200


@api_blueprint.route("/linkedin/post", methods=["DELETE"])
def delete_post():
    token = session.get("linkedin_access_token")

    data = request.get_json(silent=True) or {}
    post_urn = data.get("postUrn")

    print(f"🗑️ Deleting post: {post_urn}")
    if not token or not post_urn:
        print("Missing token or postUrn")
        return jsonify({"error": "Missing token or postUrn"}), 400

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202506"
    }
    encoded_urn = quote(post_urn, safe="")

    url = f"https://api.linkedin.com/rest/posts/{encoded_urn}"

    resp = requests.delete(url, headers=headers, timeout=10)

    print(f"📥 Delete Response Status: {resp.status_code}")
    print(f"📥 Delete Response Body: {resp.text}")

    # If deletion was successful, remove from JSON storage
    if resp.status_code in [200, 204]:
        try:
            import json
            base_dir = os.path.dirname(os.path.abspath(__file__))
            posts_file = os.path.join(base_dir, "posts_storage.json")
            
            with open(posts_file, 'r') as f:
                posts = json.load(f)
            
            # Remove the post with matching URN
            posts = [post for post in posts if post.get("urn") != post_urn]
            
            with open(posts_file, 'w') as f:
                json.dump(posts, f, indent=2)
            
            print(f"✅ Post removed from storage: {post_urn}")
        except Exception as e:
            print(f"⚠️ Error removing from storage: {e}")

    try:
        response_data = resp.json()
    except ValueError:
        response_data = {
            "status": resp.status_code,
            "message": "Post deleted successfully" if resp.status_code in [200, 204] else "Failed to delete post"
        }

    return jsonify(response_data), resp.status_code


@api_blueprint.route("/linkedin/profile-analytics")
def get_profile_analytics():
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
        import requests
        url = "https://api.linkedin.com/rest/memberFollowersCount"
        params = {"q": "me"}
        
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        
        # print(f"\n✅ PROFILE ANALYTICS RESPONSE:")
        # print(f"Status Code: {resp.status_code}")
        # print(f"Response Body: {resp.text}")

        if resp.status_code == 200:
            data = resp.json()
            # Extract follower count from the response
            followers = data.get("elements", [{}])[0].get("memberFollowersCount", 0)
            return jsonify({"followers": followers}), 200
        else:
            return {
                "error": "LinkedIn API Error",
                "details": resp.text
            }, resp.status_code
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}, 500


@api_blueprint.route("/linkedin/post-analytics")
def get_post_analytics():
    token = session.get("linkedin_access_token")
    
    if not token:
        return {"error": "Not authenticated"}, 401
    
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202506",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    # Get date range from query parameters (optional)
    start_date = request.args.get('startDate')  # Format: YYYY-MM-DD
    end_date = request.args.get('endDate')      # Format: YYYY-MM-DD
    
    try:
        import requests
        from datetime import datetime, timedelta
        
        # If no dates provided, default to last 30 days
        if not end_date:
            end = datetime.now()
        else:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
        if not start_date:
            start = end - timedelta(days=30)
        else:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Build date range parameter
        date_range = f"(start:(day:{start.day},month:{start.month},year:{start.year}),end:(day:{end.day},month:{end.month},year:{end.year}))"
        
        # Only fetch IMPRESSION and MEMBERS_REACHED for aggregated analytics
        metrics = ["IMPRESSION", "MEMBERS_REACHED"]
        analytics_data = {}
        
        for metric in metrics:
            url = f"https://api.linkedin.com/rest/memberCreatorPostAnalytics?q=me&queryType={metric}&aggregation=TOTAL&dateRange={date_range}"
            
            resp = requests.get(url, headers=headers, timeout=10)
            
            # print(f"\n✅ POST ANALYTICS RESPONSE ({metric}):")
            # print(f"Status: {resp.status_code}")
            # print(f"URL: {url}")
            # print("DETAILS:", resp.text)
            
            if resp.status_code == 200:
                data = resp.json()
                # Sum up all counts for this metric
                total_count = sum(element.get("count", 0) for element in data.get("elements", []))
                analytics_data[metric.lower()] = total_count
            else:
                analytics_data[metric.lower()] = 0
        
        return jsonify(analytics_data), 200
            
    except Exception as e:
        print(f"❌ Error fetching post analytics: {e}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/linkedin/posts")
def get_posts():
    """Get list of all created posts from JSON storage"""
    try:
        import json
        base_dir = os.path.dirname(os.path.abspath(__file__))
        posts_file = os.path.join(base_dir, "posts_storage.json")
        
        try:
            with open(posts_file, 'r') as f:
                posts = json.load(f)
            # Return posts in reverse order (newest first)
            return jsonify(posts[::-1]), 200
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify([]), 200
            
    except Exception as e:
        print(f"❌ Error fetching posts: {e}")
        return jsonify({"error": str(e)}), 500


@api_blueprint.route("/linkedin/post/<path:post_id>/analytics")
def get_post_analytics_by_id(post_id):
    """Get analytics for a specific post using entity finder"""
    token = session.get("linkedin_access_token")
    
    if not token:
        return {"error": "Not authenticated"}, 401
    
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202506",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    try:
        import requests
        import urllib.parse
        
        # Encode the URN properly for the entity parameter
        # If URN is like "urn:li:share:123", use entity=(share:urn%3Ali%3Ashare%3A123)
        if post_id.startswith("urn:li:share:"):
            entity_param = f"(share:{urllib.parse.quote(post_id, safe='')})"
        elif post_id.startswith("urn:li:ugcPost:"):
            entity_param = f"(ugc:{urllib.parse.quote(post_id, safe='')})"
        else:
            return {"error": "Invalid post URN format"}, 400
        
        # Fetch all metrics for this specific post
        metrics = ["IMPRESSION", "MEMBERS_REACHED", "REACTION", "COMMENT", "RESHARE"]
        analytics_data = {}
        
        for metric in metrics:
            url = f"https://api.linkedin.com/rest/memberCreatorPostAnalytics?q=entity&entity={entity_param}&queryType={metric}&aggregation=TOTAL"
            
            resp = requests.get(url, headers=headers, timeout=10)
            
            print(f"\n✅ POST {post_id} ANALYTICS ({metric}):")
            print(f"Status: {resp.status_code}")
            print(f"URL: {url}")
            
            if resp.status_code == 200:
                data = resp.json()
                total_count = sum(element.get("count", 0) for element in data.get("elements", []))
                analytics_data[metric.lower()] = total_count
            else:
                print(f"Error: {resp.text}")
                analytics_data[metric.lower()] = 0
        
        return jsonify(analytics_data), 200
            
    except Exception as e:
        print(f"❌ Error fetching post analytics: {e}")
        return jsonify({"error": str(e)}), 500


# ============ OAuth Routes for Account Management ============

@api_blueprint.route("/oauth/linkedin/init", methods=["GET"])
def linkedin_oauth_init():
    """Initialize LinkedIn OAuth flow"""
    try:
        # Generate a unique state for this OAuth session
        state = str(uuid.uuid4())
        session["oauth_state"] = state
        
        auth_url = oauth_service.get_linkedin_auth_url(state)
        
        return jsonify({
            "success": True,
            "url": auth_url
        }), 200
    except Exception as e:
        print(f"❌ Error initializing LinkedIn OAuth: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_blueprint.route("/oauth/linkedin/finalize", methods=["POST"])
def linkedin_oauth_finalize():
    """Finalize LinkedIn OAuth - Exchange code for token and fetch accounts"""
    try:
        data = request.json
        code = data.get("code")
        state = data.get("state")
        
        if not code:
            return jsonify({
                "success": False,
                "error": "Authorization code not provided"
            }), 400
        
        # Verify state matches
        expected_state = session.get("oauth_state")
        if state != expected_state:
            return jsonify({
                "success": False,
                "error": "Invalid OAuth state"
            }), 403
        
        # Exchange code for access token
        CLIENT_ID = os.getenv("CLIENT_ID")
        CLIENT_SECRET = os.getenv("CLIENT_SECRET")
        REDIRECT_URI = os.getenv("REDIRECT_URI")
        
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
            return jsonify({
                "success": False,
                "error": "Failed to get access token"
            }), 400
        
        print("\n✅ ACCESS TOKEN RECEIVED")
        
        # Use LinkedIn service to get profile and organizations
        linkedin_service = LinkedInService(access_token)
        
        profile = linkedin_service.get_profile()
        organizations = linkedin_service.get_organizations()
        
        print(f"✅ Profile: {profile}")
        print(f"✅ Organizations: {len(organizations)} found")
        
        # Store token in session with a unique ID
        token_session_id = str(uuid.uuid4())
        session[f"linkedin_token_{token_session_id}"] = access_token
        
        return jsonify({
            "success": True,
            "profile": profile,
            "organizations": organizations,
            "tokenSessionId": token_session_id
        }), 200
        
    except Exception as e:
        print(f"❌ Error finalizing LinkedIn OAuth: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_blueprint.route("/oauth/linkedin/connect-accounts", methods=["POST"])
def connect_linkedin_accounts():
    """Connect selected LinkedIn accounts (personal and/or organizations)"""
    try:
        data = request.json
        personal = data.get("personal", False)
        organizations = data.get("organizations", [])
        profile = data.get("profile", {})
        token_session_id = data.get("tokenSessionId")
        
        # Get the access token from session using the token_session_id
        token_key = f"linkedin_token_{token_session_id}"
        access_token = session.get(token_key)
        
        if not access_token:
            return jsonify({
                "success": False,
                "error": "OAuth session expired. Please try again."
            }), 400
        
        # Get user email from session (or use a default for testing)
        user = session.get("user", {})
        user_email = user.get("email", "test@example.com")
        
        connected_accounts = []
        
        # Connect personal account if selected
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
            oauth_service.add_account(user_email, account)
            connected_accounts.append(account)
        
        # Connect organization accounts if selected
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
            oauth_service.add_account(user_email, account)
            connected_accounts.append(account)
        
        # Clean up the temporary token from session
        session.pop(token_key, None)
        
        return jsonify({
            "success": True,
            "accounts": connected_accounts
        }), 200
        
    except Exception as e:
        print(f"❌ Error connecting accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_blueprint.route("/oauth/connected-accounts", methods=["GET"])
def get_connected_accounts():
    """Get all connected accounts for the current user"""
    try:
        # Get user email from session
        user = session.get("user", {})
        user_email = user.get("email", "test@example.com")
        
        accounts = oauth_service.get_user_accounts(user_email)
        
        # Remove sensitive data before sending to client
        safe_accounts = []
        for account in accounts:
            safe_account = {k: v for k, v in account.items() if k != "accessToken"}
            safe_accounts.append(safe_account)
        
        return jsonify({
            "success": True,
            "accounts": safe_accounts
        }), 200
        
    except Exception as e:
        print(f"❌ Error fetching connected accounts: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api_blueprint.route("/oauth/connected-accounts/<platform>/<path:account_id>", methods=["DELETE"])
def delete_connected_account(platform, account_id):
    """Delete a connected account"""
    try:
        # Get user email from session
        user = session.get("user", {})
        user_email = user.get("email", "test@example.com")
        
        success = oauth_service.delete_account(user_email, platform, account_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Account disconnected successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Account not found"
            }), 404
            
    except Exception as e:
        print(f"❌ Error deleting account: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
