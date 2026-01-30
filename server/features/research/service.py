"""Research service - orchestration wrapper"""
import os
from .agent import SpecializedDeepResearchAgent
from .prompt import getResearchPrompt


class ResearchService:
    """Research orchestration service"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.agent = SpecializedDeepResearchAgent(self.api_key)
    
    def research(self, research_type: str, user_query: str):
        """Perform research"""
        prompt = getResearchPrompt(research_type, user_query)
        return self.agent.research(prompt)
