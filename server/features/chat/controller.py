"""Chat controller - handles business logic"""
from flask import request, session, send_file
import os
import asyncio
from .storage import get_chat_storage
from .service import ChatService
from .artifacts import extract_artifacts_from_history, build_artifact_context
from shared.llm import get_llm_wrapper


class ChatController:
    """Chat business logic controller"""
    
    @staticmethod
    def get_user_email():
        """Get user email from session"""
        user = session.get("user", {})
        return user.get("email", "test@example.com")
    
    @staticmethod
    def get_sessions():
        """Get all chat sessions"""
        try:
            user_email = ChatController.get_user_email()
            storage = get_chat_storage()
            sessions = storage.get_user_sessions(user_email)
            
            session_list = [{
                'id': s['id'],
                'created_at': s['created_at'],
                'updated_at': s['updated_at'],
                'model': s['model'],
                'messages': s['messages']
            } for s in sessions]
            
            return {"sessions": session_list}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def create_session():
        """Create a new chat session"""
        try:
            data = request.json or {}
            model = data.get("model", "gemini-2.5-flash")
            
            # Model migration
            model_migration = {
                "gemini-2.0-flash-exp": "gemini-2.5-flash",
                "gemini-2.0-flash": "gemini-2.5-flash",
            }
            
            if model in model_migration:
                model = model_migration[model]
            
            user_email = ChatController.get_user_email()
            storage = get_chat_storage()
            new_session = storage.create_session(user_email, model)
            
            return {"session": new_session}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def delete_session(session_id):
        """Delete a chat session"""
        try:
            user_email = ChatController.get_user_email()
            storage = get_chat_storage()
            success = storage.delete_session(user_email, session_id)
            
            if success:
                return {"message": "Session deleted"}, 200
            else:
                return {"error": "Session not found"}, 404
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_session_messages(session_id):
        """Get messages for a session"""
        try:
            user_email = ChatController.get_user_email()
            storage = get_chat_storage()
            messages = storage.get_session_messages(user_email, session_id)
            
            return {"messages": messages}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def send_message():
        """Send a message to the chat agent"""
        try:
            data = request.json
            user_message = data.get("message")
            session_id = data.get("conversation_id")
            model = data.get("model", "gemini-2.5-flash")

            # Model migration
            model_migration = {
                "gemini-2.0-flash-exp": "gemini-2.5-flash",
                "gemini-2.0-flash": "gemini-2.5-flash",
            }
            
            if model in model_migration:
                model = model_migration[model]
            
            if not user_message:
                return {"error": "Message is required"}, 400
            
            user_email = ChatController.get_user_email()
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
            
            # Build system prompt
            system_prompt = f"""You are an AI assistant helping the user with their requests. The user's email is {user_email}.

Your capabilities:
- Research on trending topics using web search
- Social media content creation and data analytics
- Generate social media posts for LinkedIn
- Generate images based on descriptions
- Manage connected social media accounts (LinkedIn personal and company pages)
- Analyze social media performance metrics
- Read and reference previously generated files from this conversation

Communication Style:
- Be helpful, professional, and conversational
- Provide clear and actionable responses
- Use web search proactively to gather current information before asking users for clarification
- When presenting data from tools (like connected accounts, metrics, or posts), format it in a clear, readable way
- Offer relevant next actions based on the data you retrieve
- Keep responses concise but informative
- When the user references "that research", "the report", or "that file", check the artifact context for previously generated files

LinkedIn Posting Workflow:
IMPORTANT: To post to LinkedIn, you MUST follow this workflow:
1. First call get_connected_accounts(user_email="{user_email}") to get the list of connected accounts
2. Extract the accountId from the response (e.g., "urn:li:person:...")
3. Then call post_to_linkedin(account_id="<accountId>", text="<your post content>", user_email="{user_email}")
DO NOT skip step 1. Always get the connected accounts first to obtain the account_id.

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
}}"""

            messages = [{"role": "system", "content": system_prompt}]
            
            # Add history (last 10 user messages)
            user_msg_count = 0
            for msg in reversed(session_messages):
                if msg['role'] == 'user':
                    user_msg_count += 1
                    if user_msg_count > 10:
                        break
                messages.insert(1, {"role": msg['role'], "content": msg['content']})
            
            # Extract and inject artifact context into system prompt (not as separate message)
            artifacts = extract_artifacts_from_history(session_messages)
            if artifacts:
                artifact_context = build_artifact_context(artifacts)
                # Append to system message instead of adding as assistant message
                messages[0]['content'] += f"\n\n{artifact_context}"
            
            # Run async orchestration
            async def run_chat():
                chat_service = None
                try:
                    chat_service = ChatService()
                    tools_list = await chat_service.get_mcp_tools()
                    
                    max_iterations = 5
                    iteration = 0
                    final_response = None
                    tool_calls_metadata = []  # Track tool calls for artifact extraction
                    
                    while iteration < max_iterations:
                        iteration += 1
                        
                        response = await llm_wrapper.generate(
                            model=model,
                            messages=messages,
                            tools=tools_list if tools_list else None,
                            tool_choice='auto',
                            temperature=0.1,
                            user_query=user_message if iteration == 1 else None
                        )
                        
                        assistant_message = response.choices[0].message
                        
                        if not hasattr(assistant_message, 'tool_calls') or not assistant_message.tool_calls:
                            if assistant_message.content:
                                messages.append({"role": "assistant", "content": assistant_message.content})
                            final_response = assistant_message.content
                            break
                        
                        # Has tool calls
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
                        
                        # Execute tool calls and extract artifact metadata
                        from .artifacts import extract_artifact_metadata
                        
                        for tool_call in assistant_message.tool_calls:
                            tool_name = tool_call.function.name
                            
                            import json
                            try:
                                tool_args = json.loads(tool_call.function.arguments)
                            except:
                                tool_args = eval(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                            
                            print("CALLING TOOL:", tool_name)
                            result = await chat_service.call_mcp_tool(tool_name, tool_args)
                            result_text = "".join([item.text for item in result if hasattr(item, 'text')])
                            print("TOOL RESULT:", result_text)
                            
                            # Extract artifact metadata from tool result
                            artifact = extract_artifact_metadata(tool_name, result_text, tool_args)
                            print(f"ARTIFACT EXTRACTED for {tool_name}:", artifact)
                            if artifact:
                                tool_calls_metadata.append({
                                    "name": tool_name,
                                    "arguments": tool_args,
                                    "artifact": artifact
                                })
                                print(f"Added artifact to metadata: {artifact}")
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": result_text
                            })
                    
                    return final_response or "I apologize, but I couldn't generate a response.", tool_calls_metadata
                
                finally:
                    if chat_service:
                        await chat_service.cleanup()
            
            response_text, tool_calls_metadata = asyncio.run(run_chat())
            
            # Save assistant message with artifact metadata if any
            metadata = None
            if tool_calls_metadata:
                metadata = {"tool_calls": tool_calls_metadata}
            
            storage.save_message(user_email, session_id, "assistant", response_text, metadata)
            
            return {
                "type": "message",
                "message": response_text,
                "conversation_id": session_id
            }, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_report(filename):
        """Serve a report file"""
        try:
            if not filename.endswith('.html') or '/' in filename or '\\' in filename or '..' in filename:
                return {"error": "Invalid filename"}, 400
            
            server_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config.settings import DOCUMENT_PATH
            reports_dir = os.path.join(server_root, DOCUMENT_PATH, "reports")
            report_path = os.path.join(reports_dir, filename)
            
            if not os.path.exists(report_path):
                return {"error": "Report not found"}, 404
            
            return send_file(report_path, mimetype='text/html'), 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_report_image(filename):
        """Serve a report image"""
        try:
            if '/' in filename or '\\' in filename or '..' in filename:
                return {"error": "Invalid filename"}, 400
            
            server_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config.settings import DOCUMENT_PATH
            images_dir = os.path.join(server_root, DOCUMENT_PATH, "images")
            image_path = os.path.join(images_dir, filename)
            
            if not os.path.exists(image_path):
                return {"error": "Image not found"}, 404
            
            return send_file(image_path), 200
        except Exception as e:
            return {"error": str(e)}, 500
    
    @staticmethod
    def get_report_chart(filename):
        """Serve a report chart"""
        try:
            if '/' in filename or '\\' in filename or '..' in filename:
                return {"error": "Invalid filename"}, 400
            
            server_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from config.settings import DOCUMENT_PATH
            charts_dir = os.path.join(server_root, DOCUMENT_PATH, "charts")
            chart_path = os.path.join(charts_dir, filename)
            
            if not os.path.exists(chart_path):
                return {"error": "Chart not found"}, 404
            
            return send_file(chart_path), 200
        except Exception as e:
            return {"error": str(e)}, 500
