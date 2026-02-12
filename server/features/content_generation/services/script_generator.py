"""
Script Generator Service
Uses AI to generate teacher-like explanations for each scene
"""

import os
import asyncio
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from ..models import Scene, SceneScript, SceneType


class ScriptGeneratorService:
    """Generates scripts using Gemini AI"""
    
    def __init__(self):
        """Initialize the script generator"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=api_key,
            temperature=0.9
        )
    
    def create_prompt(self, scene: Scene, question_type: str) -> str:
        """Create precise prompt for script generation"""
        
        # Base prompt
        prompt = f"""You are an enthusiastic elementary school math teacher recording a video lesson.

STRICT RULES:
1. Generate ONLY the spoken script (no formatting, no markdown)
2. 2-3 sentences maximum
3. Conversational, natural tone (like talking to a student)
4. Age-appropriate language for elementary students
5. Do NOT mention things not visible on screen
6. Target duration: {scene.duration} seconds (about {int(scene.duration * 2.5)} words)

Question Type: {question_type}
Scene: {scene.id}
Focus: {scene.focus}
Teaching Strategy: {scene.teaching_strategy}
"""
        
        # Add scene-specific context
        if scene.type == SceneType.INTRO:
            prompt += "\nThis is the INTRODUCTION. Engage the student and explain what problem we'll solve."
        
        elif scene.type == SceneType.ACTION:
            if scene.action:
                prompt += f"\nThis is an ACTION scene. We're dragging item '{scene.action.item_id}' to zone '{scene.action.zone_id}'."
                prompt += "\nExplain what we're doing and why it matters."
        
        elif scene.type == SceneType.CONCLUSION:
            prompt += "\nThis is the CONCLUSION. Celebrate success and summarize what we learned."
        
        prompt += "\n\nGenerate the script now. Output ONLY the plain text script, nothing else."
        
        return prompt
    
    async def generate_script(self, scene: Scene, question_type: str) -> SceneScript:
        """
        Generate script for a single scene
        
        Args:
            scene: Scene object
            question_type: Type of question (e.g., 'addition_with_place_values')
            
        Returns:
            SceneScript object
        """
        # Create prompt
        prompt = self.create_prompt(scene, question_type)
        
        # Generate with AI
        response = self.llm.invoke(prompt)
        script_text = response.content.strip()
        
        # Remove any markdown or formatting
        script_text = script_text.replace('```', '').replace('**', '').strip()
        
        # Calculate word count and estimated duration
        word_count = len(script_text.split())
        estimated_duration = word_count / 2.5  # Average speaking rate: 150 words/min = 2.5 words/sec
        
        return SceneScript(
            scene_id=scene.id,
            script=script_text,
            word_count=word_count,
            estimated_duration=estimated_duration
        )
    
    async def generate_all(self, scenes: List[Scene], question_type: str) -> List[SceneScript]:
        """
        Generate scripts for all scenes in parallel
        
        Args:
            scenes: List of Scene objects
            question_type: Type of question
            
        Returns:
            List of SceneScript objects
        """
        # Create tasks for parallel execution
        tasks = [
            self.generate_script(scene, question_type)
            for scene in scenes
        ]
        
        # Execute all tasks in parallel
        scripts = await asyncio.gather(*tasks)
        
        return scripts
