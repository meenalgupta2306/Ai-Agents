# import json
# import re
# import os
from rich.console import Console
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from google.genai import types
import json
import webbrowser
import os
import asyncio

console = Console()

class MCPClient:
    def __init__(self, api_key):
        self.api_key = api_key

        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()


    async def connect_to_server(self, server_script_path: str):
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()


    async def getAvailableTools(self):
        """Fetches tools from MCP server and formats them for Gemini SDK."""
        if not self.session:
            return []
        
        response = await self.session.list_tools()
        # Gemini expects a specific format for tool definitions
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema 
            } for tool in response.tools
        ]
    
    async def orchestrate(self, user_prompt: str):
        gemini = genai.Client(api_key=self.api_key)

        chat = gemini.aio.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                tools=[{
                    "function_declarations": await self.getAvailableTools()
                }]
            )
        )

        console.print(f"[bold magenta]🚀 Orchestrating task:[/bold magenta] {user_prompt}")

        response = await chat.send_message(user_prompt)

        while True:
            tool_calls = []
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    tool_calls.append(part.function_call)

            if not tool_calls:
                break

            tool_responses = []

            for call in tool_calls:
                console.print(
                    f"\n[bold cyan]🤖 Gemini wants to call:[/bold cyan] [green]{call.name}[/green]"
                )
                console.print(f"[bold cyan]Parameters:[/bold cyan] {call.args}")

                mcp_output = await self.call_mcp_tool(call.name, call.args)

                # Convert the TextContent list to a single string
                full_text_result = ""
                for content_item in mcp_output:
                    if hasattr(content_item, 'text'):
                        full_text_result += content_item.text + "\n"

                if "AUTH_REQUIRED" in full_text_result:
                    await self.handleLinkedinLogin(full_text_result, call)

                console.print(mcp_output, "///////////////////")
                tool_responses.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": full_text_result}
                    )
                )

            response = await chat.send_message(tool_responses)

        return response.text


    async def call_mcp_tool(self, name: str, args: dict):
        """The actual executor that Gemini calls internally."""
        console.print(f"[bold yellow]⚙️ Orchestrator calling tool:[/bold yellow] {name}")
        result = await self.session.call_tool(name, args)
        
        # We return the content of the tool result back to Gemini
        # result.content is usually a list of content objects
        return result.content
    
    async def handleLinkedinLogin(self, full_text_result, call):
        try:
            # 1. Parse the Auth Signal
            data = json.loads(full_text_result)
            auth_url = data.get("url")
            status = data.get("status")

            if status != "AUTH_REQUIRED" or not auth_url:
                return full_text_result

            console.print(f"[bold red]🔐 Auth Required![/bold red] Opening: {auth_url}")
            
            # 2. Open Browser
            webbrowser.open(auth_url)
            
            # 3. Polling for the "Bridge" file
            # This is more reliable than a fixed sleep
            creds_path = "linkedin_creds.json"
            
            # Clean up old creds if they exist to prevent false positives
            if os.path.exists(creds_path):
                os.remove(creds_path)

            console.print("[yellow]Waiting for you to complete the LinkedIn login flow...[/yellow]")
            
            authenticated = False
            for i in range(45):  # Wait up to 90 seconds (45 * 2s)
                if os.path.exists(creds_path):
                    # Small extra sleep to ensure the file is fully written/closed by Flask
                    await asyncio.sleep(1) 
                    authenticated = True
                    break
                await asyncio.sleep(2)

            if not authenticated:
                console.print("[bold red]❌ Timeout:[/bold red] Login not detected.")
                return "Error: Authentication timed out. Please try again."

            # 4. Retry the tool call
            console.print("[bold green]✅ Auth Success![/bold green] Retrying LinkedIn post...")
            mcp_output = await self.call_mcp_tool(call.name, call.args)
            
            # Return the new output (the success message) to the orchestrator
            return "".join([c.text for c in mcp_output if hasattr(c, 'text')])
                        
        except json.JSONDecodeError:
            # Not an auth signal, just return the text as is
            return full_text_result

