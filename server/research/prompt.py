def getResearchPrompt(type, user_query):
    # Define the specific instructions based on type
    if type == 'report':
        body = """
        INSTRUCTIONS:
        1. Write the research report in clean HTML format (use <h2>, <p>, <ul> tags).
        2. When a visual (image or chart) is needed to support the text, insert this exact placeholder: [[VISUAL_PLACEHOLDER:unique_id]]
        3. Do not attempt to generate the image or chart yourself.

        JSON SCHEMA FOR VISUALS:
        {{
            "visuals": [
                {{
                    "id": "unique_id",
                    "type": "image",
                    "caption": "brief description",
                    "content": {{
                        "visual_intent": "Detailed description for an image generator...",
                        "aspect_ratio": "16:9"
                    }}
                }},
                {{
                    "id": "unique_id",
                    "type": "chart",
                    "format": "svg",
                    "caption": "brief description",
                    "content": {{
                        "chart_type": "line",
                        "title": "Chart Title",
                        "x_label": "X Axis",
                        "y_label": "Y Axis",
                        "data": {{ "label1": 10, "label2": 20 }},
                        "visual_intent": "Styling instructions..."
                    }}
                }}
            ]
        }}

        IMPORTANT: 
        - Ensure every "unique_id" in the JSON matches a placeholder in your text.
        - The JSON block must be inside a fenced code block: ```json ... ```
        - The JSON block must be the VERY LAST thing in your response.

        """
    elif type == 'summary':
        body = """
        INSTRUCTIONS:
        1. Write a compelling blog post in Markdown or HTML.
        2. Use placeholders [[VISUAL_PLACEHOLDER:unique_id]] where images should go.
        """
    else:
        body = "Provide a detailed research summary."

    # Use double {{ }} to escape JSON braces in a Python f-string
    prompt = f'''
        You are a Deep Research Agent. Your goal is to write a high-quality {type}.
        
        CRITICAL CONSTRAINT: You CANNOT generate images or execute code directly.
        You must separate "CONTENT" from "VISUAL SPECIFICATIONS".

        {body}

        
        User Query: {user_query}
    '''
    return prompt