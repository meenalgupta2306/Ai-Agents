import os
from google import genai
from google.genai import types
from io import BytesIO
import base64

class ImageGenerator:
    def __init__(self, output_dir, api_key=None):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        
        # ✅ Anchor to SERVER root (two levels up from this file)
        server_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )

        # ✅ Resolve ASSET_PATH from server root
        self.output_dir = os.path.abspath(
            os.path.join(server_root, output_dir)
        )

        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, visual_intent, filename):
        try:
            image_bytes = self._call_image_model(visual_intent)

            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            return {
                "status": "success",
                "file_path": filepath
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _call_image_model(self, prompt):
        response = self.client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images= 4,
            )
        )

        if not response.generated_images:
            raise RuntimeError("No image returned from Imagen")

        image_base64 = response.generated_images[0].image.image_bytes
        return image_base64
