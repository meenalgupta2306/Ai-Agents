import time
from google import genai
from rich.console import Console

console = Console(stderr=True)

class SpecializedDeepResearchAgent:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.agent_name = 'deep-research-pro-preview-12-2025'

    def research(self, prompt: str):
        try:
            interaction = self.client.interactions.create(
                input=prompt,
                agent=self.agent_name,
                background=True
            )
        except Exception as e:
            raise RuntimeError(f"Failed to start research: {e}") from e

        console.print(f"[green]Research started. Interaction ID:[/green] {interaction.id}")
        
        while True:
            try:
                interaction = self.client.interactions.get(interaction.id)
            except Exception as e:
                console.print(f"[red]Error polling status:[/red] {e}")
                time.sleep(10)
                continue

            status = interaction.status
            console.print(f"Status: {status}", end="\r")
    
            if status == "completed":
                console.print("\n[bold green]Research Completed![/bold green]")
                if interaction.outputs:
                    return interaction.outputs[-1].text
                else:
                    return "No output generated."
            elif status == "failed":
                console.print("\n[bold red]Research Failed![/bold red]")
                return f"Error: {interaction.error}"
            
            time.sleep(10)
