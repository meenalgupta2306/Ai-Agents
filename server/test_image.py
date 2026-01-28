import os
from dotenv import load_dotenv
from research.generators.image_generator import ImageGenerator

load_dotenv()

def test_image():
    api_key = os.getenv("GEMINI_API_KEY")

    ig = ImageGenerator(
        api_key=api_key,
        output_dir=os.getenv("DOCUMENT_PATH")
    )

    result = ig.generate(
        visual_intent="A futuristic robot reading a book in a library",
        filename="test_image.png"
    )

    print(result)

if __name__ == "__main__":
    test_image()
