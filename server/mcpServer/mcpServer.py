import sys
import os
from dotenv import load_dotenv
# Add the 'server' directory to sys.path so 'linkedin' can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp.server.fastmcp import FastMCP
from services.linkedin import LinkedInService
from services.report import ReportService
from rich.console import Console
from research.prompt import getResearchPrompt
from research.agent import SpecializedDeepResearchAgent
from research.generators.image_generator import ImageGenerator
import json

import logging
import sys
from pathlib import Path

# Kill all noisy loggers
logging.getLogger().handlers.clear()
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)

for name in [
    "google",
    "google.genai",
    "httpx",
    "httpcore",
    "mcp",
]:
    logging.getLogger(name).setLevel(logging.ERROR)

load_dotenv()
console = Console(stderr=True)
agent = SpecializedDeepResearchAgent(os.getenv("GEMINI_API_KEY"))

mcp = FastMCP("Backend MCP Server")

@mcp.tool("research_tool")
async def start_research(research_type: str, user_query: str) -> str:
    """
    Performs deep research on a topic. 
    research_type: 'report' for HTML or 'summary' for text.
    user_query: MUST contain the user's complete request verbatim.
    Do NOT summarize, shorten, or paraphrase.
    Include comparison criteria, constraints, and output format exactly as given.

    IMPORTANT:
    If visuals are needed, the output will include a JSON block with instructions.

    """
    reportService = ReportService()

    console.print(f"[bold blue]Step 1: Researching '{user_query}'...[/bold blue]")
    prompt = getResearchPrompt(research_type, user_query)
    research_output = agent.research(prompt)

    console.print(research_type+"----------------------------")
    if research_type == 'report':
         # if type is report then research_outptu contains html + visuals
        reportService.generateReport(research_output)
        return f"""SUCCESS: Full HTML Report generated.
        LOCATION: {reportService.report_path}/final_report.html
        INSTRUCTIONS: Inform the user the report is ready at the path above."""
    
    reportService._save_report(research_output, reportService.report_path + "report_draft.txt")
    return research_output
    
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
    api_key =os.getenv("GEMINI_API_KEY")
         # Compute server root once
    server_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../")
    )
    image_path = os.path.join(server_root, os.getenv("DOCUMENT_PATH"), "images")
    imageGenerator =ImageGenerator(api_key=api_key, output_dir=image_path)

    result = imageGenerator.generate(prompt, filename)
    
    return result["file_path"]



@mcp.tool()
def post_to_linkedin(text: str, image_path: str = None):
    """
     Posts content to LinkedIn for the currently authenticated user.
    """
    BASE_DIR = Path(__file__).resolve().parent        # .../server/mcpServer
    creds_path = BASE_DIR.parent / "linkedin_creds.json"  

    console.print(os.path.exists(creds_path), "JSON EXISIT--------------")
    # 1. Check for the "Signal" file
    if not os.path.exists(creds_path):
        return {
            "status": "AUTH_REQUIRED",
            "url": "http://localhost:8000/login",
            "message": "User must sign in via the provided link."
        }
    
    # 2. Extract Token and Member ID
    try:
        with open(creds_path, "r") as f:
            creds = json.load(f)
            
        token = creds.get("access_token")
        member_id = creds.get("member_id")

        if not token or not member_id:
            # File exists but is malformed
            os.remove(creds_path) # Clean up bad state
            return "Error: Saved credentials are invalid. Please log in again."

    except (json.JSONDecodeError, IOError):
        return "Error: Could not read credentials file."
    
    # 3. Execute the Service
    try:
        service = LinkedInService(token, member_id)
        post_urn = service.create_linkedin_post(text, image_path)
        return {"status": "SUCCESS", "post_urn": post_urn}
    
    except Exception as e:
        # Handle expired tokens (LinkedIn tokens usually last 60 days)
        if "unauthorized" in str(e).lower():
            os.remove(creds_path)
            return {"status": "AUTH_REQUIRED", "url": "http://localhost:5000/login"}
        return {"status": "FAILED", "error": str(e)}

if __name__ == "__main__":
    # FastMCP uses stdio by default, which is perfect for Claude Desktop
    mcp.run()