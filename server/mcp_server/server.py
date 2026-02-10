"""MCP Server - registers and exposes tools"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from tools import research_tool, image_tool, linkedin_tool, accounts_tool, voice_tool, meta_tool

import logging

# Kill all noisy loggers
logging.getLogger().handlers.clear()
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

for name in ["google", "google.genai", "httpx", "httpcore", "mcp"]:
    logging.getLogger(name).setLevel(logging.ERROR)

load_dotenv()

mcp = FastMCP("Backend MCP Server")


@mcp.tool("research_tool")
async def start_research(research_type: str, user_query: str) -> str:
    """
    Performs deep research on a topic. 
    research_type: 'report' for research or 'summary' for social media post.
    user_query: MUST contain the user's complete request verbatim.
    Do NOT summarize, shorten, or paraphrase.
    Include comparison criteria, constraints, and output format exactly as given.

    IMPORTANT:
    If visuals are needed, the output will include a JSON block with instructions.
    """
    return await research_tool.research_tool(research_type, user_query)


@mcp.tool("generate_image")
def generate_image(prompt: str, filename: str) -> str:
    """
    Generates an image based on a text prompt and saves it to a local file.
    
    Args:
        prompt: A detailed description of the image to generate.
        filename: The desired name of the file (e.g., 'robot_research.png').
        
    Returns:
        The absolute local file path of the generated image. 
    """
    return image_tool.image_tool(prompt, filename)


@mcp.tool()
def post_to_linkedin(account_id: str, text: str, user_email: str = "test@example.com", image_path: str = None):
    """
    Posts content to LinkedIn using a specific connected account.
    
    IMPORTANT: You must first call get_connected_accounts to get the account_id.
    
    Args:
        account_id: The accountId from get_connected_accounts (e.g., 'urn:li:person:...')
        text: The text content to post to LinkedIn
        user_email: Email of the user (defaults to test@example.com)
        image_path: Optional path to an image file to include in the post
        
    Example workflow:
        1. Call get_connected_accounts(user_email="test@example.com")
        2. Get the accountId from the response
        3. Call post_to_linkedin(account_id="urn:li:person:...", text="My post")
    """
    return linkedin_tool.linkedin_tool(account_id, text, user_email, image_path)


@mcp.tool("get_connected_accounts")
def get_connected_accounts(user_email: str) -> str:
    """
    Gets all connected social media accounts for a user.
    
    Args:
        user_email: The email of the user to get accounts for.
        
    Returns:
        A JSON string with account details (platform, name, type, accountId).
    """
    return accounts_tool.accounts_tool(user_email)


@mcp.tool("generate_speech")
def generate_speech(text: str, user_email: str = "test@example.com"):
    """
    Generates speech in the user's cloned voice using their voice sample.
    
    IMPORTANT: User must have uploaded a voice sample first!
    If no sample exists, this will return an error asking them to upload one.
    
    Args:
        text: The text to convert to speech (max 5000 characters)
        user_email: Email of the user (defaults to test@example.com)
        
    Returns:
        JSON with status, audio URL, and playback instructions.
        
    Example response on success:
        {
            "status": "SUCCESS",
            "message": "Speech generated successfully!",
            "audio_url": "http://localhost:3001/api/voice/audio/...",
            "playback_instructions": "You can play the audio at: ..."
        }
        
    Example response when no sample exists:
        {
            "status": "ERROR",
            "message": "No voice sample found. Please upload a voice sample first...",
            "requires_sample": true
        }
    """
    return voice_tool.voice_tool(text, user_email)


@mcp.tool("create_meta_campaign")
def create_meta_campaign(
    account_id: str,
    campaign_name: str,
    objective: str,
    user_email: str = "test@example.com",
    status: str = "PAUSED",
    special_ad_categories: list = None
):
    """
    Creates a Meta (Facebook/Instagram) advertising campaign.
    
    IMPORTANT: You must first call get_connected_accounts to get the Meta account_id.
    
    Args:
        account_id: The Meta ad account ID from get_connected_accounts (format: act_123456789)
        campaign_name: Name for the campaign
        objective: Campaign objective - one of:
            - OUTCOME_TRAFFIC (drive traffic to website/app)
            - OUTCOME_LEADS (generate leads)
            - OUTCOME_SALES (drive sales/conversions)
            - OUTCOME_ENGAGEMENT (increase engagement)
            - OUTCOME_APP_PROMOTION (promote app installs)
            - OUTCOME_AWARENESS (build brand awareness)
        user_email: Email of the user (defaults to test@example.com)
        status: Campaign status - ACTIVE, PAUSED, or ARCHIVED (default: PAUSED for safety)
        special_ad_categories: List of special ad categories like ["EMPLOYMENT", "HOUSING", "CREDIT"] (default: [])
        
    Example workflow:
        1. Call get_connected_accounts(user_email="test@example.com")
        2. Find Meta account and get its accountId (e.g., "act_123456789")
        3. Call create_meta_campaign(
            account_id="act_123456789",
            campaign_name="Summer Sale 2024",
            objective="OUTCOME_TRAFFIC",
            status="PAUSED"
        )
        
    Returns:
        JSON with status, campaign_id, and details.
    """
    return meta_tool.create_meta_campaign_tool(
        account_id=account_id,
        campaign_name=campaign_name,
        objective=objective,
        user_email=user_email,
        status=status,
        special_ad_categories=special_ad_categories
    )


if __name__ == "__main__":
    # FastMCP uses stdio by default, which is perfect for Claude Desktop
    mcp.run()
