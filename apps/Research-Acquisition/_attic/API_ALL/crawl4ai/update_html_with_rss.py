"""
Update HTML Dashboard with RSS Feed Link
Adds RSS feed auto-discovery and subscription link to HTML dashboard
"""

from pathlib import Path
import sys

def add_rss_to_html(html_file, rss_url="https://theophysics.pages.dev/feed.xml"):
    """Add RSS feed link to HTML dashboard"""
    
    print(f"\n{'='*70}")
    print(f"UPDATING HTML WITH RSS FEED")
    print(f"{'='*70}")
    print(f"HTML File: {html_file}")
    print(f"RSS URL: {rss_url}")
    print(f"{'='*70}\n")
    
    html_path = Path(html_file)
    
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_file}")
        return
    
    html_content = html_path.read_text(encoding='utf-8')
    
    # Add RSS auto-discovery link in <head>
    rss_discovery = f'    <link rel="alternate" type="application/rss+xml" title="Theophysics - Quantum-Spiritual Framework RSS Feed" href="{rss_url}">'
    
    if rss_discovery not in html_content:
        html_content = html_content.replace('</head>', f'{rss_discovery}\n</head>')
    
    # Add RSS subscription button in header
    rss_button = f'''
            <div style="margin-top: 15px;">
                <a href="{rss_url}" style="display: inline-block; background: #ff6600; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold;">
                    📡 Subscribe to RSS Feed
                </a>
                <span style="margin-left: 15px; color: #666; font-size: 0.9em;">
                    Import to Substack or any RSS reader
                </span>
            </div>
'''
    
    if '📡 Subscribe to RSS Feed' not in html_content:
        # Add after the header paragraph
        html_content = html_content.replace(
            '<p>Total Papers Analyzed:',
            f'{rss_button}\n            <p>Total Papers Analyzed:'
        )
    
    # Write updated HTML
    html_path.write_text(html_content, encoding='utf-8')
    
    print(f"✓ HTML updated with RSS feed link\n")
    print(f"{'='*70}")
    print(f"UPDATE COMPLETE")
    print(f"{'='*70}")
    print(f"RSS feed is now discoverable in the HTML dashboard")
    print(f"Users can subscribe via: {rss_url}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    html_file = "Trinity_Dashboard.html"
    rss_url = "https://theophysics.pages.dev/feed.xml"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    if len(sys.argv) > 2:
        rss_url = sys.argv[2]
    
    add_rss_to_html(html_file, rss_url)
