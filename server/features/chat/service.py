"""Chat service - handles chat logic and MCP integration"""
import os
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession as MCPClientSession, StdioServerParameters as MCPStdioServerParameters
from mcp.client.stdio import stdio_client


class ChatService:
    """Chat service with embedded MCP client logic"""
    
    def __init__(self):
        self.mcp_session: Optional[MCPClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.mcp_server_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "..", "mcp_server", "server.py"
        )
    
    async def connect_to_mcp(self):
        """Connect to MCP server"""
        if self.mcp_session:
            return  # Already connected
        
        server_params = MCPStdioServerParameters(
            command="python",
            args=[self.mcp_server_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        self.mcp_session = await self.exit_stack.enter_async_context(MCPClientSession(stdio, write))
        await self.mcp_session.initialize()
    
    async def get_mcp_tools(self):
        """Get available tools from MCP server"""
        if not self.mcp_session:
            await self.connect_to_mcp()
        
        response = await self.mcp_session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema 
            } for tool in response.tools
        ]
    
    async def call_mcp_tool(self, name: str, args: dict):
        """Call a tool on the MCP server"""
        if not self.mcp_session:
            await self.connect_to_mcp()
        
        result = await self.mcp_session.call_tool(name, args)
        return result.content
    
    async def cleanup(self):
        """Cleanup MCP connection"""
        if hasattr(self, 'exit_stack'):
            try:
                await self.exit_stack.aclose()
            except:
                pass
