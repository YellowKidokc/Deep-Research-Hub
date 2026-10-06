import sys
sys.path.insert(0, r'd:\GitHub\crawl4ai')

from paper_analytics_processor import process_papers

# Run on Trinity folder
process_papers(
    scan_dir=r"O:\_Theophysics\05_Logos_Papers\Core_Papers\Trinity",
    template_dir=r"O:\_Theophysics\999_Exclude\Obsidian Data Analytics\Data_Analytics",
    output_dir=r"d:\GitHub\crawl4ai\Trinity_paper_dashboards"
)
