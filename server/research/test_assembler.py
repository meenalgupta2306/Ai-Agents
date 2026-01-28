import os
import sys

# Add the current directory to sys.path to import Assembler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from assembler import Assembler

def test_assembler():
    assembler = Assembler()
    
    html_content = """
    <h1>Research Report</h1>
    <p>Here is an image:</p>
    [[VISUAL_PLACEHOLDER:img1]]
    <p>And here is a chart:</p>
    [[VISUAL_PLACEHOLDER:chart1]]
    """
    
    # Mock asset_map with absolute paths (similar to what generators return)
    # Assuming server root is /home/meenal/poc/ai-agents/server
    server_root = "/home/meenal/poc/ai-agents/server"
    asset_map = {
        "img1": {
            "status": "success",
            "file_path": os.path.join(server_root, "documents/images/img1.png")
        },
        "chart1": {
            "status": "success",
            "file_path": os.path.join(server_root, "documents/charts/chart1.svg")
        }
    }
    
    # Report path
    report_path = os.path.join(server_root, "documents/reports/")
    
    print(f"Report Path: {report_path}")
    
    final_html = assembler.replace_placeholders(html_content, asset_map, base_dir=report_path)
    
    print("\nGenerated HTML:")
    print(final_html)
    
    # Assertions
    assert '../images/img1.png' in final_html
    assert '../charts/chart1.svg' in final_html
    print("\n✅ Verification Successful: Relative paths are correctly generated!")

if __name__ == "__main__":
    test_assembler()
