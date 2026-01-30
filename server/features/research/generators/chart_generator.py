import os
import json
import base64
from google import genai
from google.genai import types


class ChartGenerator:
    def __init__(self, api_key, output_dir):
        self.client = genai.Client(api_key=api_key)
        self.output_dir = output_dir
        # ✅ Anchor to SERVER root (two levels up from this file)
        server_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )

        # ✅ Resolve ASSET_PATH from server root
        self.output_dir = os.path.abspath(
            os.path.join(server_root, output_dir)
        )
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(
        self,
        chart_type,
        data,
        visual_intent,
        title,
        x_label,
        y_label,
        format="auto",
        filename="chart"
    ):
        """
        format: "svg" | "png" | "auto" (SVG first, fallback to PNG)
        """

        # Decide preferred formats
        if format == "svg":
            formats_to_try = ["svg"]
        elif format == "png":
            formats_to_try = ["png"]
        else:
            formats_to_try = ["svg", "png"]

        last_error = None

        for fmt in formats_to_try:
            try:
                result = self._generate_with_format(
                    chart_type,
                    data,
                    visual_intent,
                    title,
                    x_label,
                    y_label,
                    fmt,
                    filename
                )
                if result["status"] == "success":
                    return result
                else:
                    last_error = result["error"]
            except Exception as e:
                last_error = str(e)

        return {
            "status": "error",
            "error": f"All formats failed. Last error: {last_error}"
        }

    def _generate_with_format(
        self,
        chart_type,
        data,
        visual_intent,
        title,
        x_label,
        y_label,
        fmt,
        filename
    ):
        prompt = f"""
You are a Python data visualization assistant.

STRICT RULES:
- Output ONLY executable Python code
- DO NOT explain anything
- DO NOT wrap code in markdown
- You MUST run the code using the code execution tool

TASK:
Generate and run Python code to create a {chart_type} chart using matplotlib.

DATA (JSON):
{json.dumps(data, indent=2)}

VISUAL INTENT:
{visual_intent}

CHART SETTINGS:
- Title: {title}
- X label: {x_label}
- Y label: {y_label}
- Clean, professional styling
- No plt.show()

MANDATORY OUTPUT:
- Save the figure to a buffer
- Print ONLY base64 data between markers

Use this EXACT ending code:

import io, base64
buf = io.BytesIO()
plt.savefig(buf, format="{fmt}", bbox_inches="tight")
print("START_BASE64")
print(base64.b64encode(buf.getvalue()).decode())
print("END_BASE64")
"""

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=[types.Tool(code_execution=types.ToolCodeExecution())]
            ),
        )

        execution_output = ""

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.code_execution_result:
                    execution_output += part.code_execution_result.output

        if "START_BASE64" not in execution_output or "END_BASE64" not in execution_output:
            return {
                "status": "error",
                "error": f"No base64 output produced for format={fmt}"
            }

        b64_data = (
            execution_output
            .split("START_BASE64")[1]
            .split("END_BASE64")[0]
            .strip()
        )

        image_bytes = base64.b64decode(b64_data)

        filepath = os.path.join(self.output_dir, f"{filename}.{fmt}")
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        return {
            "status": "success",
            "file_path": filepath,
            "format": fmt
        }
