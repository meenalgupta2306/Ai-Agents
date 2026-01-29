"""
Chat API Routes - Handles chat messages with Gemini/OpenAI and MCP tool calling
Uses LLM wrapper for model selection and chat storage for session persistence
"""
from flask import Blueprint, request, jsonify, session, send_file
import os
import sys
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chat_storage import get_chat_storage
from llm import get_llm_wrapper
from research.MCPClient import MCPClient

chat_blueprint = Blueprint("chat", __name__, url_prefix="/api/chat")

# Path to MCP server
MCP_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "mcpServer/mcpServer.py"
)


def get_user_email():
    """Get user email from session"""
    user = session.get("user", {})
    return user.get("email", "test@example.com")


async def get_mcp_tools():
    """Get tools from MCP server"""
    mcp_client = MCPClient(api_key=os.getenv("GEMINI_API_KEY"))
    await mcp_client.connect_to_server(MCP_SERVER_PATH)
    tools = await mcp_client.getAvailableTools()
    return tools, mcp_client


@chat_blueprint.route("/sessions", methods=["GET"])
def get_sessions():
    """Get all chat sessions for the current user"""
    try:
        user_email = get_user_email()
        storage = get_chat_storage()
        sessions = storage.get_user_sessions(user_email)
        
        # Return sessions without full message history (just metadata)
        session_list = [{
            'id': s['id'],
            'created_at': s['created_at'],
            'updated_at': s['updated_at'],
            'model': s['model'],
            'messages': s['messages']  # Include messages for preview
        } for s in sessions]
        
        return jsonify({"sessions": session_list})
    except Exception as e:
        print(f"❌ Error getting sessions: {e}")
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/sessions", methods=["POST"])
def create_session():
    """Create a new chat session"""
    try:
        data = request.json or {}
        model = data.get("model", "gemini-2.5-flash")
        
        # Model migration: map old model names to new ones
        model_migration = {
            "gemini-2.0-flash-exp": "gemini-2.5-flash",
            "gemini-2.0-flash": "gemini-2.5-flash",
        }
        
        if model in model_migration:
            model = model_migration[model]
        
        user_email = get_user_email()
        
        storage = get_chat_storage()
        new_session = storage.create_session(user_email, model)
        
        return jsonify({"session": new_session})
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a chat session"""
    try:
        user_email = get_user_email()
        storage = get_chat_storage()
        success = storage.delete_session(user_email, session_id)
        
        if success:
            return jsonify({"message": "Session deleted"})
        else:
            return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        print(f"❌ Error deleting session: {e}")
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/sessions/<session_id>/messages", methods=["GET"])
def get_session_messages(session_id):
    """Get messages for a specific session"""
    try:
        user_email = get_user_email()
        storage = get_chat_storage()
        messages = storage.get_session_messages(user_email, session_id)
        
        return jsonify({"messages": messages})
    except Exception as e:
        print(f"❌ Error getting session messages: {e}")
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/message", methods=["POST"])
def send_message():
    """
    Send a message to the chat agent
    
    Request body:
    {
        "message": "User message",
        "conversation_id": "session-id",
        "model": "gemini-2.5-flash" or "gpt-4o"
    }
    """
    try:
        data = request.json
        user_message = data.get("message")
        session_id = data.get("conversation_id")
        model = data.get("model", "gemini-2.5-flash")

        # Model migration: map old model names to new ones
        model_migration = {
            "gemini-2.0-flash-exp": "gemini-2.5-flash",
            "gemini-2.0-flash": "gemini-2.5-flash",
        }
        
        if model in model_migration:
            old_model = model
            model = model_migration[model]
            print(f"🔄 Migrated model: {old_model} → {model}")

        print(f"📝 Using model: {model}")
        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        user_email = get_user_email()
        storage = get_chat_storage()
        llm_wrapper = get_llm_wrapper()
        
        # Get or create session
        if not session_id:
            new_session = storage.create_session(user_email, model)
            session_id = new_session['id']
        
        # Save user message
        storage.save_message(user_email, session_id, "user", user_message)
        
        # Load chat history
        session_messages = storage.get_session_messages(user_email, session_id)
        
        # Build messages for LLM (system + history)
        system_prompt = f"""You are an AI assistant helping the user with their requests. The user's email is {user_email}.

Your capabilities:
- Research on trending topics using web search
- Social media content creation and data analytics
- Generate social media posts for LinkedIn
- Generate images based on descriptions
- Manage connected social media accounts (LinkedIn personal and company pages)
- Analyze social media performance metrics

Communication Style:
- Be helpful, professional, and conversational
- Provide clear and actionable responses
- Use web search proactively to gather current information before asking users for clarification
- When presenting data from tools (like connected accounts, metrics, or posts), format it in a clear, readable way
- Offer relevant next actions based on the data you retrieve
- Keep responses concise but informative

Response Format:
- For direct answers, respond in plain text
- If the response contains file locations or downloadable content, return in JSON format:
{{
  "message": "Your message text with {{{{REPORT_LINK}}}} placeholder where the link should appear",
  "action": {{
    "type": "view_report",
    "filename": "final_report.html",
    "label": "final_report.html"
  }}
}}

Example:
{{
  "message": "Report completed! View it here: {{{{REPORT_LINK}}}}",
  "action": {{
    "type": "view_report",
    "filename": "final_report.html",
    "label": "final_report.html"
  }}
}}
"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history (last 10 user messages and their responses)
        user_msg_count = 0
        for msg in reversed(session_messages):
            if msg['role'] == 'user':
                user_msg_count += 1
                if user_msg_count > 10:
                    break
            messages.insert(1, {"role": msg['role'], "content": msg['content']})
        
        # Run async orchestration with LLM wrapper and MCP tools
        async def run_chat():
            mcp_client = None
            try:
                # Get MCP tools
                tools_list, mcp_client = await get_mcp_tools()
                
                # Pass tools directly - LLM wrapper will handle format conversion
                # MCP returns: [{"name": "...", "description": "...", "parameters": {...}}]
                # LLM wrapper converts to appropriate format for each provider
                
                # Call LLM with tools
                max_iterations = 5
                iteration = 0
                final_response = None
                
                while iteration < max_iterations:
                    iteration += 1
                    
                    # Pass user_query only on first iteration for Gemini
                    # This prevents re-sending the user message in tool continuations
                    response = await llm_wrapper.generate(
                        model=model,
                        messages=messages,
                        tools=tools_list if tools_list else None,
                        tool_choice='auto',
                        temperature=0.1,
                        user_query=user_message if iteration == 1 else None
                    )
                    
                    assistant_message = response.choices[0].message
                    
                    print(f"\n🤖 Assistant response (iteration {iteration}):\n{vars(assistant_message)}\n")
                    
                    # Check for tool calls
                    if not hasattr(assistant_message, 'tool_calls') or not assistant_message.tool_calls:
                        # No tool calls - add assistant message and finish
                        if assistant_message.content:
                            messages.append({
                                "role": "assistant",
                                "content": assistant_message.content
                            })
                        final_response = assistant_message.content
                        break
                    
                    # Has tool calls - add assistant message with tool_calls
                    # IMPORTANT: Both OpenAI and Gemini need tool_calls preserved in history
                    assistant_msg = {
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    }
                    
                    messages.append(assistant_msg)
                    
                    # Execute tool calls
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        
                        # Parse arguments
                        import json
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except:
                            tool_args = eval(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                        
                        print(f"🔧 Calling MCP tool: {tool_name} with args: {tool_args}")
                        
                        # Call MCP tool
                        result = await mcp_client.call_mcp_tool(tool_name, tool_args)
                        

                        print("\n\n",result)
                        
                        # Convert result to string
                        result_text = "".join([item.text for item in result if hasattr(item, 'text')])
                        
                        print("\n", result_text)
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": result_text
                        })
                
                return final_response or "I apologize, but I couldn't generate a response."
            
            finally:
                # Cleanup MCP client
                if mcp_client and hasattr(mcp_client, 'exit_stack'):
                    try:
                        await mcp_client.exit_stack.aclose()
                    except:
                        pass
        
        # Execute async chat
        response_text = asyncio.run(run_chat())
        
        # Save assistant response
        storage.save_message(user_email, session_id, "assistant", response_text)
        
        return jsonify({
            "type": "message",
            "message": response_text,
            "conversation_id": session_id
        })
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/reports/<filename>", methods=["GET"])
def get_report(filename):
    """
    Serve a research report HTML file
    
    Args:
        filename: Name of the report file (e.g., 'final_report.html')
    
    Returns:
        HTML file content or 404 if not found
    """
    try:
        # Security: Only allow .html files and prevent directory traversal
        print(f"📄 API HIT - Filename requested: {filename}")
        if not filename.endswith('.html') or '/' in filename or '\\' in filename or '..' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        # Construct path to reports directory
        server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(server_root, os.getenv("DOCUMENT_PATH", "documents"), "reports")
        report_path = os.path.join(reports_dir, filename)
        
        print(f"📂 Server root: {server_root}")
        print(f"📂 Reports dir: {reports_dir}")
        print(f"📂 Full report path: {report_path}")
        print(f"📂 File exists: {os.path.exists(report_path)}")
        
        # Check if file exists
        if not os.path.exists(report_path):
            print(f"❌ File not found: {report_path}")
            return jsonify({"error": "Report not found"}), 404
        
        # Read and print first 200 chars to verify content
        with open(report_path, 'r') as f:
            preview = f.read(200)
            print(f"📄 File preview: {preview}")
        
        # Return the HTML file
        print(f"✅ Serving file: {report_path}")
        return send_file(report_path, mimetype='text/html')
        
    except Exception as e:
        print(f"❌ Error serving report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/reports/images/<filename>", methods=["GET"])
def get_report_image(filename):
    """Serve research report images"""
    try:
        # Security: prevent directory traversal
        if '/' in filename or '\\' in filename or '..' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        images_dir = os.path.join(server_root, os.getenv("DOCUMENT_PATH", "documents"), "images")
        image_path = os.path.join(images_dir, filename)
        
        if not os.path.exists(image_path):
            return jsonify({"error": "Image not found"}), 404
        
        return send_file(image_path)
    except Exception as e:
        print(f"❌ Error serving image: {e}")
        return jsonify({"error": str(e)}), 500


@chat_blueprint.route("/reports/charts/<filename>", methods=["GET"])
def get_report_chart(filename):
    """Serve research report charts"""
    try:
        # Security: prevent directory traversal
        if '/' in filename or '\\' in filename or '..' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        charts_dir = os.path.join(server_root, os.getenv("DOCUMENT_PATH", "documents"), "charts")
        chart_path = os.path.join(charts_dir, filename)
        
        if not os.path.exists(chart_path):
            return jsonify({"error": "Chart not found"}), 404
        
        return send_file(chart_path)
    except Exception as e:
        print(f"❌ Error serving chart: {e}")
        return jsonify({"error": str(e)}), 500
