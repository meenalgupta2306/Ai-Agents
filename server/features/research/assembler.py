import re
import os
from rich.console import Console


console = Console(stderr=True)
class Assembler:
    def __init__(self):
        pass

    def replace_placeholders(self, html_content, asset_map, base_dir=None):
        """
        Replaces [[VISUAL_PLACEHOLDER:id]] with <img> tags.
        """
        def replacement_func(match):
            placeholder_id = match.group(1)
            asset_info = asset_map.get(placeholder_id)
            
            if not asset_info:
                return f"<!-- Visual {placeholder_id} not found -->"
            console.print(asset_info)
            if asset_info["status"] == "success":
                file_path = asset_info["file_path"]
                
                if base_dir:
                    # Calculate relative path from the report directory to the asset
                    rel_path = os.path.relpath(file_path, base_dir)
                    src = rel_path
                # else:
                #     filename = os.path.basename(file_path)
                #     src = f"assets/{filename}"
                
                return f'<img src="{src}" alt="Visual {placeholder_id}" style="max-width:100%; height:auto; margin: 20px 0; display: block; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">'
            else:
                error_msg = asset_info.get("error", "Unknown error")
                return f'<div style="border:1px solid #ff4d4d; padding:15px; color:#cc0000; background:#fff5f5; border-radius:8px; margin:20px 0;"><strong>Visual Generation Failed ({placeholder_id}):</strong><br>{error_msg}</div>'

        pattern = r"\[\[VISUAL_PLACEHOLDER:([a-zA-Z0-9_-]+)\]\]"
        return re.sub(pattern, replacement_func, html_content)
