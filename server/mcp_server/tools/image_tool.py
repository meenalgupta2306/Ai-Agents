"""Image generation tool"""
import os
from features.research.generators.image_generator import ImageGenerator


def image_tool(prompt: str, filename: str) -> str:
    """
    Generates an image based on a text prompt and saves it to a local file.
    
    Args:
        prompt: A detailed description of the image to generate.
        filename: The desired name of the file (e.g., 'robot_research.png').
        
    Returns:
        The absolute local file path of the generated image. 
    """
    api_key = os.getenv("GEMINI_API_KEY")
    server_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    from config.settings import DOCUMENT_PATH
    image_path = os.path.join(server_root, DOCUMENT_PATH, "images")
    
    generator = ImageGenerator(api_key=api_key, output_dir=image_path)
    result = generator.generate(prompt, filename)
    
    return result["file_path"]
