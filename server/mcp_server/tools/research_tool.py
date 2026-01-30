"""Research tool - calls features.research.service"""
import os
from features.research.service import ResearchService
from features.reports.service import ReportService


async def research_tool(research_type: str, user_query: str) -> str:
    """
    Performs deep research on a topic. 
    research_type: 'report' for research or 'summary' for social media post.
    user_query: MUST contain the user's complete request verbatim.
    """
    research_service = ResearchService(os.getenv("GEMINI_API_KEY"))
    report_service = ReportService()
    
    print(f"[bold blue]Step 1: Researching '{user_query}'...[/bold blue]")
    research_output = research_service.research(research_type, user_query)
    
    if research_type == 'report':
        report_service.generateReport(research_output)
        return f"""SUCCESS: Full HTML Report generated.
        LOCATION: {report_service.report_path}/final_report.html
        INSTRUCTIONS: Inform the user the report is ready at the path above."""
    
    report_service._save_report(research_output, report_service.report_path + "report_draft.txt")
    return research_output
