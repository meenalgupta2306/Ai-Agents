import json
import re
import os
from rich.console import Console
from features.research.assembler import Assembler
from features.research.generators.image_generator import ImageGenerator
from features.research.generators.chart_generator import ChartGenerator

console = Console(stderr=True)

class ReportService:
    def __init__(self):
        api_key =os.getenv("GEMINI_API_KEY")
         # Compute server root once
        server_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../")
        )

        image_path = os.path.join(server_root, os.getenv("DOCUMENT_PATH"), "images")
        chart_path = os.path.join(server_root, os.getenv("DOCUMENT_PATH"), "charts")
        self.report_path = os.path.join(server_root, os.getenv("DOCUMENT_PATH"), "reports/")

        self.image_gen = ImageGenerator(api_key= api_key,output_dir= image_path)
        self.chart_gen = ChartGenerator(api_key=api_key, output_dir=chart_path)
        self.assembler = Assembler()

    def generateReport(self, raw_output):
        html_content, visuals_json = self._parse_output(raw_output)
        
        if not visuals_json:
            self._save_report(html_content, self.report_path + "report.html")
            console.print("[yellow]No visuals requested.[/yellow]")
            # Still save the HTML even if no visuals
            return html_content
        
        self._save_report(html_content, self.report_path + "report_draft.html")
        self._save_json(
            visuals_json,
            output_path= self.report_path + "visuals.json"
        )

        console.print(f"[bold blue]Step 2: Generating {len(visuals_json)} visuals...[/bold blue]")

        asset_map = self._generate_assets(visuals_json)

        console.print("[bold blue]Step 3: Assembling final report...[/bold blue]", asset_map)
        final_html = self.assembler.replace_placeholders(html_content, asset_map, base_dir=self.report_path)
        
        self._save_report(final_html, output_path= self.report_path + "final_report.html")

        console.print(f"[bold blue]FINISH GENERATING REPORT")


    def _generate_assets(self, visuals):
        asset_map = {}
        for visual in visuals:
            v_id = visual["id"]
            v_type = visual["type"]
            content = visual["content"]
            
            console.print(f"Generating {v_type}: {v_id}...")
            
            if v_type == "image":
                result = self.image_gen.generate(
                    content.get("visual_intent", ""),
                    filename=f"{v_id}.png"
                )
                asset_map[v_id] = result
                
            elif v_type == "chart":
                result = self.chart_gen.generate(
                    content.get("chart_type", "line"),
                    content.get("data", {}),
                    content.get("visual_intent", ""),
                    content.get("title", "Chart"),
                    content.get("x_label", "X"),
                    content.get("y_label", "Y"),
                    format=visual.get("format", "auto"),
                    filename=v_id             # 👈 extension decided later
                )
                asset_map[v_id] = result

        return asset_map

    def _parse_output(self, raw_text):
        json_match = re.search(r"```json\s*(\{.*\})\s*```", raw_text, re.DOTALL)
        if not json_match:
            json_match = re.search(r"(\{.*\"visuals\".*\})\s*$", raw_text, re.DOTALL)
            
        if json_match:
            json_str = json_match.group(1)
            try:
                visuals_data = json.loads(json_str)
                html_content = raw_text.replace(json_match.group(0), "")
                return html_content, visuals_data.get("visuals", [])
            except json.JSONDecodeError:
                console.print("[red]Failed to parse JSON visuals.[/red]")
        
        return raw_text, []
    
    def _save_report(self, content,output_path):
        console.print(f"save report called {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(content)
        console.print(f"[bold green]Success! Report saved to {output_path}[/bold green]")

    def _save_json(self, data, output_path: str):
        console.print(f"save json called {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        console.print(f"[bold green]Success! Report saved to {output_path}[/bold green]")