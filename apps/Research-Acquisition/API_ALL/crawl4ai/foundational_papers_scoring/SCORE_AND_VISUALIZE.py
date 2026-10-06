#!/usr/bin/env python3
"""
THEOPHYSICS COHERENCE FRAMEWORK
One-Click Scoring & Visualization Pipeline (Python Version)

Run this single script to:
1. Score all canonical documents
2. Generate interactive HTML dashboard
3. Create enhanced Excel workbook
4. Open results in browser
"""

import sys
import subprocess
from pathlib import Path
import webbrowser

def print_header(text, color='gold'):
    """Print styled header"""
    colors = {
        'gold': '\033[93m',
        'cyan': '\033[96m',
        'green': '\033[92m',
        'red': '\033[91m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    c = colors.get(color, colors['white'])
    reset = colors['reset']
    
    print()
    print(f"{c}{'='*80}{reset}")
    print(f"{c}{text}{reset}")
    print(f"{c}{'='*80}{reset}")
    print()

def print_step(step_num, total_steps, text):
    """Print step indicator"""
    print(f"\033[93m[STEP {step_num}/{total_steps}]\033[0m \033[97m{text}\033[0m")

def main():
    script_dir = Path(__file__).parent
    scoring_script = script_dir / "score_all_canonical.py"
    dashboard_script = script_dir / "create_dashboard.py"
    output_dir = script_dir / "outputs" / "dashboard"
    dashboard_html = output_dir / "coherence_dashboard.html"
    excel_file = output_dir / "coherence_analysis_with_charts.xlsx"
    
    skip_scoring = '--skip-scoring' in sys.argv
    no_browser = '--no-browser' in sys.argv
    
    print_header("THEOPHYSICS COHERENCE FRAMEWORK", 'gold')
    print("\033[96mAutomated Scoring & Visualization Pipeline\033[0m")
    print()
    
    # Step 1: Scoring
    if not skip_scoring:
        print_step(1, 3, "Running Comprehensive Document Scoring...")
        print("  \033[96m- Theophysics Foundational Papers\033[0m")
        print("  \033[96m- US Founding Documents\033[0m")
        print("  \033[96m- Scientific Theories (118 documents)\033[0m")
        print("  \033[96m- World Religions Sacred Texts\033[0m")
        print()
        
        try:
            result = subprocess.run([sys.executable, str(scoring_script)], 
                                   check=True, 
                                   capture_output=True, 
                                   text=True,
                                   encoding='utf-8',
                                   errors='replace')
            print("\033[92m[OK] Scoring Complete!\033[0m")
        except subprocess.CalledProcessError as e:
            print(f"\033[91m[ERROR] Scoring failed: {e}\033[0m")
            return 1
    else:
        print_step(1, 3, "Skipping scoring (using existing data)")
    
    print()
    
    # Step 2: Dashboard Generation
    print_step(2, 3, "Generating Interactive HTML Dashboard...")
    print("  \033[96m- Category comparison charts\033[0m")
    print("  \033[96m- Top 20 documents ranking\033[0m")
    print("  \033[96m- 12 Fruits radar analysis\033[0m")
    print("  \033[96m- Grade distribution\033[0m")
    print("  \033[96m- Enhanced Excel workbook\033[0m")
    print()
    
    try:
        result = subprocess.run([sys.executable, str(dashboard_script)], 
                               check=True, 
                               capture_output=True, 
                               text=True,
                               encoding='utf-8',
                               errors='replace')
        
        if not dashboard_html.exists():
            raise FileNotFoundError("Dashboard file was not created")
        
        print("\033[92m[OK] Dashboard Generated!\033[0m")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\033[91m[ERROR] Dashboard generation failed: {e}\033[0m")
        return 1
    
    print()
    
    # Step 3: Open in Browser
    if not no_browser:
        print_step(3, 3, "Opening Dashboard in Browser...")
        try:
            webbrowser.open(str(dashboard_html))
            print("\033[92m[OK] Dashboard Opened!\033[0m")
        except Exception as e:
            print(f"\033[93m[WARNING] Could not open browser: {e}\033[0m")
    else:
        print_step(3, 3, "Dashboard ready (not auto-opening)")
    
    print()
    print_header("PIPELINE COMPLETE!", 'green')
    
    print("\033[97mOutput Files:\033[0m")
    print(f"  \033[96mHTML Dashboard:\033[0m {dashboard_html}")
    print(f"  \033[96mExcel Workbook:\033[0m {excel_file}")
    print()
    
    print("\033[93mNext Steps:\033[0m")
    print("  \033[97m1. Review the interactive charts in your browser\033[0m")
    print("  \033[97m2. Open the Excel file for detailed analysis\033[0m")
    print("  \033[97m3. Share findings with collaborators\033[0m")
    print()
    
    print("\033[96mTo re-run scoring:\033[0m python SCORE_AND_VISUALIZE.py")
    print("\033[96mTo regenerate dashboard only:\033[0m python SCORE_AND_VISUALIZE.py --skip-scoring")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
