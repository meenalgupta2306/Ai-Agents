"""MCP Server - registers and exposes tools"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from tools import research_tool, image_tool, linkedin_tool, accounts_tool

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
def post_to_linkedin(text: str, image_path: str = None):
    """Posts content to LinkedIn for the currently authenticated user."""
    return linkedin_tool.linkedin_tool(text, image_path)


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


if __name__ == "__main__":
    # FastMCP uses stdio by default, which is perfect for Claude Desktop
    mcp.run()
