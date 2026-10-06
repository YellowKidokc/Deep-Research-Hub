"""
RSS Feed Generator for Trinity Papers
Creates RSS 2.0 feed from analytics data for Substack import
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_rss_feed(excel_file, output_file, base_url="https://theophysics.pages.dev"):
    """Generate RSS 2.0 feed from Excel analytics data"""
    
    print(f"\n{'='*70}")
    print(f"RSS FEED GENERATOR")
    print(f"{'='*70}")
    print(f"Reading: {excel_file}")
    print(f"Output: {output_file}")
    print(f"Base URL: {base_url}")
    print(f"{'='*70}\n")
    
    # Read Excel data
    df = pd.read_excel(excel_file, sheet_name='All Papers')
    
    # Sort by importance score (most important first)
    df = df.sort_values('importance_score', ascending=False)
    
    # Create RSS root element
    rss = ET.Element('rss', version='2.0', attrib={
        'xmlns:atom': 'http://www.w3.org/2005/Atom',
        'xmlns:content': 'http://purl.org/rss/1.0/modules/content/'
    })
    
    channel = ET.SubElement(rss, 'channel')
    
    # Channel metadata
    ET.SubElement(channel, 'title').text = 'Theophysics - Quantum-Spiritual Framework'
    ET.SubElement(channel, 'link').text = base_url
    ET.SubElement(channel, 'description').text = 'Theophysics: Mathematical analyses of Biblical events, Trinity theology, and quantum-spiritual dynamics. Unifying physics and faith through rigorous academic research.'
    ET.SubElement(channel, 'language').text = 'en-us'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    ET.SubElement(channel, 'generator').text = 'Theophysics Analytics Processor'
    
    # Add copyright and managing editor
    ET.SubElement(channel, 'copyright').text = f'Copyright {datetime.now().year} Theophysics'
    ET.SubElement(channel, 'webMaster').text = 'webmaster@theophysics.com'
    
    # Atom self-reference
    atom_link = ET.SubElement(channel, 'atom:link', attrib={
        'href': f'{base_url}/feed.xml',
        'rel': 'self',
        'type': 'application/rss+xml'
    })
    
    # Add items (papers)
    for idx, row in df.iterrows():
        item = ET.SubElement(channel, 'item')
        
        # Title
        paper_title = row['filename']
        ET.SubElement(item, 'title').text = paper_title
        
        # Link (to dashboard)
        dashboard_filename = row['filename'] + '_dashboard.html'
        paper_url = f"{base_url}/_paper_analytics/{dashboard_filename}"
        ET.SubElement(item, 'link').text = paper_url
        
        # GUID
        ET.SubElement(item, 'guid', isPermaLink='true').text = paper_url
        
        # Publication date (use current date, or extract from frontmatter if available)
        pub_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        ET.SubElement(item, 'pubDate').text = pub_date
        
        # Description (summary of analytics)
        description = f"""
<h3>Paper Analytics Summary</h3>
<ul>
<li><strong>Size:</strong> {int(row['size_chars']):,} characters, {int(row['words']):,} words</li>
<li><strong>Structure:</strong> {int(row['headings'])} headings, {int(row['lines'])} lines</li>
<li><strong>Links:</strong> {int(row['links_internal'])} internal, {int(row['links_external'])} external</li>
<li><strong>Mathematical Content:</strong> {int(row['equations'])} equations</li>
<li><strong>Importance Score:</strong> {row['importance_score']:.1f}</li>
</ul>
"""
        
        # Add key concepts if available
        concept_cols = [col for col in df.columns if col.startswith('concept_')]
        if concept_cols:
            concepts_found = []
            for col in concept_cols:
                if row[col] > 0:
                    concept_name = col.replace('concept_', '').capitalize()
                    concepts_found.append(f"{concept_name} ({int(row[col])})")
            
            if concepts_found:
                description += "<h4>Key Concepts:</h4><ul>"
                for concept in concepts_found[:10]:  # Top 10 concepts
                    description += f"<li>{concept}</li>"
                description += "</ul>"
        
        # Add content flags
        flags = []
        if row['has_dataview']:
            flags.append('Dataview Queries')
        if row['has_charts']:
            flags.append('Charts/Graphs')
        if row['has_statistics']:
            flags.append('Statistics')
        if row['has_metrics']:
            flags.append('Metrics/KPIs')
        
        if flags:
            description += f"<p><strong>Features:</strong> {', '.join(flags)}</p>"
        
        description += f'<p><a href="{paper_url}">View Full Analytics Dashboard →</a></p>'
        
        ET.SubElement(item, 'description').text = description
        
        # Content:encoded (full HTML content)
        content_encoded = ET.SubElement(item, 'content:encoded')
        content_encoded.text = description
        
        # Categories (based on key concepts)
        if concept_cols:
            for col in concept_cols:
                if row[col] > 0:
                    concept_name = col.replace('concept_', '').capitalize()
                    ET.SubElement(item, 'category').text = concept_name
    
    # Pretty print XML
    xml_str = minidom.parseString(ET.tostring(rss)).toprettyxml(indent='  ')
    
    # Remove extra blank lines
    xml_lines = [line for line in xml_str.split('\n') if line.strip()]
    xml_str = '\n'.join(xml_lines)
    
    # Write to file
    Path(output_file).write_text(xml_str, encoding='utf-8')
    
    print(f"✓ RSS feed created with {len(df)} items\n")
    print(f"{'='*70}")
    print(f"RSS FEED COMPLETE")
    print(f"{'='*70}")
    print(f"Feed URL: {base_url}/feed.xml")
    print(f"Total Papers: {len(df)}")
    print(f"{'='*70}\n")
    
    return xml_str

if __name__ == "__main__":
    excel_file = "Trinity_Analytics.xlsx"
    output_file = "feed.xml"
    base_url = "https://theophysics.pages.dev"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        base_url = sys.argv[3]
    
    create_rss_feed(excel_file, output_file, base_url)
