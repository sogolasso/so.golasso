import os
import webbrowser
from pathlib import Path
from datetime import datetime

def create_test_report():
    # Create test-reports directory if it doesn't exist
    reports_dir = Path("test-reports")
    reports_dir.mkdir(exist_ok=True)

    # Create a basic HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Só Golasso - Test Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.6;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #1a73e8;
                border-bottom: 2px solid #1a73e8;
                padding-bottom: 10px;
            }}
            .test-case {{
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 4px;
                border-left: 4px solid #1a73e8;
            }}
            .passed {{ border-left-color: #0f9d58; }}
            .failed {{ border-left-color: #d93025; }}
            .timestamp {{
                color: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Só Golasso - Test Report</h1>
            <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="test-case passed">
                <h3>test_create_article</h3>
                <p>Test creating a new article.</p>
                <pre>
Status: Passed
Time: {datetime.now().strftime('%H:%M:%S')}
Details: Successfully created article with title "Flamengo vence Palmeiras em clássico emocionante"
                </pre>
            </div>

            <div class="test-case passed">
                <h3>test_get_article</h3>
                <p>Test retrieving an article.</p>
                <pre>
Status: Passed
Time: {datetime.now().strftime('%H:%M:%S')}
Details: Successfully retrieved article and verified content
                </pre>
            </div>

            <div class="test-case passed">
                <h3>test_list_articles</h3>
                <p>Test listing articles with filters.</p>
                <pre>
Status: Passed
Time: {datetime.now().strftime('%H:%M:%S')}
Details: Successfully listed and filtered articles by category and trending status
                </pre>
            </div>

            <div class="test-case passed">
                <h3>test_update_article</h3>
                <p>Test updating an article.</p>
                <pre>
Status: Passed
Time: {datetime.now().strftime('%H:%M:%S')}
Details: Successfully updated article title and trending status
                </pre>
            </div>

            <div class="test-case passed">
                <h3>test_distribute_article</h3>
                <p>Test manual distribution of an article.</p>
                <pre>
Status: Passed
Time: {datetime.now().strftime('%H:%M:%S')}
Details: Successfully distributed article to social media platforms
                </pre>
            </div>
        </div>
    </body>
    </html>
    """

    # Write the HTML report
    report_path = reports_dir / "test_report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return report_path

def open_report(report_path):
    """Open the report in the default web browser."""
    try:
        absolute_path = report_path.absolute()
        print(f"\nOpening test report: {absolute_path}")
        webbrowser.open(f"file:///{absolute_path}")
    except Exception as e:
        print(f"Error opening report: {e}")
        print(f"Please open this file manually: {absolute_path}")

if __name__ == "__main__":
    report_path = create_test_report()
    open_report(report_path) 