import os
import webbrowser
from pathlib import Path

def view_test_report():
    # Get the test report path
    report_path = Path("test-reports/test_report.html")
    
    if not report_path.exists():
        print("Test report not found. Generating new report...")
        from run_tests import create_test_report
        report_path = create_test_report()
    
    # Convert to absolute path with correct slashes for the OS
    absolute_path = report_path.absolute().as_posix()
    
    # Print the path for manual opening if needed
    print(f"\nTest report location: {absolute_path}")
    
    try:
        # Try to open in browser
        webbrowser.open(f"file:///{absolute_path}")
        print("Opening test report in your default browser...")
    except Exception as e:
        print(f"\nError opening browser: {e}")
        print("\nPlease open the file manually using the path above.")

if __name__ == "__main__":
    view_test_report() 