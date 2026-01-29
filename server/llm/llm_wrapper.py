"""
LLM Wrapper - Hybrid approach for OpenAI and Gemini
- OpenAI: Uses OpenAI SDK
- Gemini: Uses native Google Generative AI SDK (supports all models including -exp)
"""
import os
from openai import AsyncOpenAI
from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional
from google.genai.types import GenerateContentConfig, ModelContent, UserContent
import json


class LLMWrapper:
    def __init__(self):
        """Initialize LLM wrapper with API keys from environment"""
        # OpenAI client
        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            )
        
        # Gemini client
        self.gemini_client = None
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Model to provider mapping
        self.model_providers = {
            "gpt-4o": "openai",
            "gpt-4o-mini": "openai",
            "gemini-2.5-flash": "gemini",
            "gemini-1.5-pro": "gemini",
            "gemini-2.5-pro": "gemini",
        }
    
    async def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = 'auto',
        user_query: Optional[str] = None
    ) -> Any:
        """
        Generate response using appropriate provider
        
        Args:
            model: Model name
            messages: List of message dicts with 'role' and 'content'
            temperature: Temperature for generation
            tools: Optional list of tool definitions (MCP format)
            tool_choice: Tool choice strategy
            user_query: Original user query (for Gemini, to avoid re-extracting from messages)
        
        Returns:
            Response in OpenAI-compatible format
        """
        if model not in self.model_providers:
            available = ", ".join(self.model_providers.keys())
            raise ValueError(f"Unsupported model: {model}. Available: {available}")
        
        provider = self.model_providers[model]
        
        if provider == "openai":
            return await self._generate_openai(model, messages, temperature, tools, tool_choice)
        elif provider == "gemini":
            return await self._generate_gemini(model, messages, temperature, tools, tool_choice, user_query)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _generate_openai(self, model, messages, temperature, tools, tool_choice):
        """Generate using OpenAI SDK"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        params = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        # Convert MCP tools to OpenAI format
        if tools and len(tools) > 0:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["parameters"]
                    }
                })
            params["tools"] = openai_tools
            params["tool_choice"] = tool_choice
        
        return await self.openai_client.chat.completions.create(**params)
    
    async def _generate_gemini(self, model, messages, temperature, tools, tool_choice, user_query):
        """
        Generate using Gemini SDK
        """
        if not self.gemini_client:
            raise ValueError("Gemini API key not configured")
        
        # Convert messages to Gemini format (history only)
        system_instruction, history = self._convert_messages_to_gemini(messages)
        
        # Create config
        config = GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            tools=[{"function_declarations": tools}] if tools else None
        )
        
        # Create chat with history
        chat = self.gemini_client.aio.chats.create(
            model=model,
            config=config,
            history=history  
        )
        
        # Send user query on first iteration, empty string for tool continuations
        message_to_send = user_query if user_query else ""
        response = await chat.send_message(message_to_send)
        
        # Convert response to OpenAI format
        return self._convert_gemini_response_to_openai(response)
    
    def _convert_messages_to_gemini(self, messages):
        """
        Convert OpenAI messages to Gemini format
        Returns: (system_instruction, history)
        
        Note: Gemini only understands UserContent and ModelContent.
        Tool results are already converted to assistant messages in chat.py.
        User query is passed separately via user_query parameter.
        """
        system_instruction = None
        history = []

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                system_instruction = content
            elif role == "user":
                # Corrected: Use text= keyword or direct types.Part(text=...)
                history.append(types.UserContent(parts=[types.Part(text=content)]))
            elif role == "assistant":
                parts = []
                if content:
                    parts.append(types.Part(text=content))
                
                # If preserving tool calls for Iteration 2+
                if "tool_calls" in msg:
                    for tc in msg["tool_calls"]:
                        parts.append(types.Part.from_function_call(
                            name=tc.function.name,
                            args=json.loads(tc.function.arguments)
                        ))
                history.append(types.ModelContent(parts=parts))
            elif role == "tool":
                history.append(types.Content(
                    role="user", 
                    parts=[types.Part.from_function_response(
                        name=msg.get("name"),
                        response={"result": msg.get("content")}
                    )]
                ))
        return system_instruction, history
        
    def _convert_gemini_response_to_openai(self, gemini_response):
        """Convert Gemini response to OpenAI-compatible format"""

        class OpenAIResponse:
            def __init__(self):
                self.choices = []

        class Choice:
            def __init__(self):
                self.message = Message()
                self.finish_reason = "stop"

        class Message:
            def __init__(self):
                self.role = "assistant"
                self.content = ""
                self.tool_calls = []

        class ToolCall:
            def __init__(self, name, args):
                self.id = f"call_{name}"
                self.type = "function"
                self.function = Function(name, args)

        class Function:
            def __init__(self, name, args):
                self.name = name
                self.arguments = json.dumps(args or {})

        response = OpenAIResponse()
        choice = Choice()

        # Defensive checks
        if not hasattr(gemini_response, "candidates") or not gemini_response.candidates:
            response.choices.append(choice)
            return response

        candidate = gemini_response.candidates[0]

        if not hasattr(candidate, "content") or not hasattr(candidate.content, "parts"):
            response.choices.append(choice)
            return response

        for part in candidate.content.parts:
            # ✅ Text part
            if hasattr(part, "text") and part.text:
                choice.message.content += part.text

            # ✅ Tool call part (ONLY if present)
            if hasattr(part, "function_call") and part.function_call is not None:
                fc = part.function_call

                tool_call = ToolCall(
                    fc.name,
                    dict(fc.args) if fc.args else {}
                )

                choice.message.tool_calls.append(tool_call)
                choice.finish_reason = "tool_calls"

        # OpenAI expects tool_calls omitted if empty
        if not choice.message.tool_calls:
            del choice.message.tool_calls

        response.choices.append(choice)
        return response



# Singleton instance
_llm_wrapper = None

def get_llm_wrapper() -> LLMWrapper:
    """Get or create the singleton LLMWrapper instance"""
    global _llm_wrapper
    if _llm_wrapper is None:
        _llm_wrapper = LLMWrapper()
    return _llm_wrapper
