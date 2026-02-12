"""
Scene Generator Service
Uses AI to generate pedagogical scene structure from config
"""

import json
import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from ..models import SceneStructure, Scene, SceneType, ActionDetails, SceneTiming


class SceneGeneratorService:
    """Generates scene structure using Gemini AI"""
    
    def __init__(self):
        """Initialize the scene generator"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=api_key,
            temperature=0.7
        )
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and parse config.json"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def create_prompt(self, config: Dict[str, Any]) -> str:
        """Create precise prompt for scene generation"""
        
        # The real config is under a 'config' key
        inner_config = config.get('config', {})
        
        # Extract items and zones from config
        draggable_items = inner_config.get('draggableItems', {}).get('items', [])
        dropzones = inner_config.get('dropzones', {}).get('zones', [])
        
        item_ids = [item.get('id') for item in draggable_items if item.get('id')]
        zone_ids = [zone.get('id') for zone in dropzones if zone.get('id')]
        
        # Extract the ORDERED list of drag operations from dropzones
        drag_operations = []
        for zone in dropzones:
            zone_id = zone.get('id')
            zone_items = zone.get('draggableItems', [])
            for item in zone_items:
                drag_operations.append({
                    'item_id': item.get('id', 'N/A'), # Some items (operators) might not have ID
                    'zone_id': zone_id,
                    'item_content': item.get('content', item.get('id', ''))
                })
        
        prompt = f"""You are an expert educational content designer for elementary mathematics.

CRITICAL INSTRUCTIONS:
1. The dropzones in the config represent the CORRECT MATHEMATICAL ORDER for solving this problem
2. You MUST create action scenes in the EXACT SAME ORDER as the drag operations listed below
3. Each action scene should explain WHY this step comes at this point in the mathematical process
4. Use your mathematical knowledge to explain place values, operators, and the solving sequence
5. Output ONLY valid JSON following the exact schema provided

AVAILABLE ITEMS: {item_ids}
AVAILABLE ZONES: {zone_ids}

ORDERED DRAG OPERATIONS (FOLLOW THIS EXACT SEQUENCE):
{json.dumps(drag_operations, indent=2)}

FULL CONFIG:
{json.dumps(config, indent=2)}

SCENE GENERATION RULES:
1. Create ONE "intro" scene (explain the problem and goal)
2. Create ONE "action" scene for EACH drag operation in the order listed above
3. Create ONE "conclusion" scene (summarize and celebrate)
4. Scene types: "intro", "action", or "conclusion" ONLY
5. Each action scene MUST use the exact item_id and zone_id from the drag operations list
6. Explain the mathematical reasoning for each step (e.g., "We start with the ones place because...")
7. Total duration should be 40-60 seconds

OUTPUT SCHEMA (follow exactly):
{{
  "question_type": "string (e.g., 'addition_with_place_values')",
  "total_duration": number (total video duration in seconds),
  "scenes": [
    {{
      "id": "intro",
      "type": "intro",
      "duration": number (3-5 seconds),
      "focus": "string (introduce the problem)",
      "teaching_strategy": "string (engage student with clear problem statement)"
    }},
    {{
      "id": "scene_1",
      "type": "action",
      "duration": number (6-10 seconds),
      "focus": "string (explain this specific drag operation and its mathematical significance)",
      "teaching_strategy": "string (connect the action to mathematical concepts like place value)",
      "action": {{
        "type": "drag",
        "item_id": "string (MUST match drag_operations[0].item_id)",
        "zone_id": "string (MUST match drag_operations[0].zone_id)"
      }},
      "timing": {{
        "pre_action": number (2-3 seconds to explain before dragging),
        "action": number (1-2 seconds for the drag animation),
        "post_action": number (2-3 seconds to reinforce after dragging)
      }}
    }},
    ... (repeat for ALL drag operations in order),
    {{
      "id": "conclusion",
      "type": "conclusion",
      "duration": number (3-5 seconds),
      "focus": "string (celebrate completion and reinforce learning)",
      "teaching_strategy": "string (positive reinforcement and summary)"
    }}
  ]
}}

Generate the scene structure now. Output ONLY the JSON, nothing else."""

        return prompt
    
    async def generate(self, config_path: str) -> SceneStructure:
        """
        Generate scene structure from config
        
        Args:
            config_path: Path to config.json
            
        Returns:
            SceneStructure object
        """
        # Load config
        config = self.load_config(config_path)
        
        # Create prompt
        prompt = self.create_prompt(config)
        
        # Generate with AI
        response = self.llm.invoke(prompt)
        
        # Parse response
        response_text = response.content.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])
        
        # Parse JSON
        scene_data = json.loads(response_text)
        
        # Convert to SceneStructure object
        scenes = []
        for scene_dict in scene_data['scenes']:
            action = None
            timing = None
            
            if scene_dict.get('action'):
                action = ActionDetails(**scene_dict['action'])
            
            if scene_dict.get('timing'):
                timing = SceneTiming(**scene_dict['timing'])
            
            scene = Scene(
                id=scene_dict['id'],
                type=SceneType(scene_dict['type']),
                duration=scene_dict['duration'],
                focus=scene_dict['focus'],
                teaching_strategy=scene_dict['teaching_strategy'],
                action=action,
                timing=timing
            )
            scenes.append(scene)
        
        scene_structure = SceneStructure(
            question_type=scene_data['question_type'],
            total_duration=scene_data['total_duration'],
            scenes=scenes
        )
        
        return scene_structure
    
    def save_scene_structure(self, scene_structure: SceneStructure, output_path: str):
        """Save scene structure to JSON file"""
        # Convert to dict
        data = {
            'question_type': scene_structure.question_type,
            'total_duration': scene_structure.total_duration,
            'scenes': []
        }
        
        for scene in scene_structure.scenes:
            scene_dict = {
                'id': scene.id,
                'type': scene.type.value,
                'duration': scene.duration,
                'focus': scene.focus,
                'teaching_strategy': scene.teaching_strategy
            }
            
            if scene.action:
                scene_dict['action'] = {
                    'type': scene.action.type,
                    'item_id': scene.action.item_id,
                    'zone_id': scene.action.zone_id
                }
            
            if scene.timing:
                scene_dict['timing'] = {
                    'pre_action': scene.timing.pre_action,
                    'action': scene.timing.action,
                    'post_action': scene.timing.post_action
                }
            
            data['scenes'].append(scene_dict)
        
        # Save to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
