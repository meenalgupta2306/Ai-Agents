import os
import asyncio
from dotenv import load_dotenv
from rich.console import Console
from MCPClient import MCPClient

load_dotenv()
console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
server_path = os.path.join(os.path.dirname(BASE_DIR), "mcpServer", "mcpServer.py")

async def main():
   api_key = os.getenv("GEMINI_API_KEY")
   if not api_key:
       console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not found in .env file.")
       return
   client = MCPClient(api_key=api_key)
   
   console.print("[bold green]Deep Research System (Simplified POC) Initialized[/bold green]")
   "/server/mcp/mcpServer.py"
   # topic = console.input("\n[bold yellow]Enter a research topic:[/bold yellow] ")

   try:
      # This will now print your tools correctly
      await client.connect_to_server(server_path)
      
      console.print("[bold green]✅ Connected to MCP Server.[/bold green]")

      goal = '''
        I want you to perform a 3-step task:
         1. RESEARCH: Conduct a deep research on 'Agentic AI' and summarize the key trends.
         2. VISUALIZE: Based on your research, generate a professional chart or image that explains an Agentic AI concept.
         3. PUBLISH: Analyze your research and the image to create a high-quality LinkedIn post. 
            Post this directly to my LinkedIn account.
      '''
      
      final_answer = await client.orchestrate(goal)
          
      console.print("\n" + "="*50)
      console.print(f"[bold green]FINAL RESPONSE:[/bold green]\n{final_answer}")
      console.print("="*50)
        
   finally:
      await client.exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())
