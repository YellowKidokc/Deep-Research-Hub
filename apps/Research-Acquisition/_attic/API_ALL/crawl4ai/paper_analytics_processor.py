"""
Individual Paper Analytics Processor
Processes each markdown file individually and creates separate analytics dashboards
Uses templates from Data_Analytics folder
"""

from pathlib import Path
from datetime import datetime
import shutil
import re
import sys

def load_analytics_templates(template_dir):
    """Load analytics templates from Data_Analytics folder"""
    templates = {}
    template_path = Path(template_dir)
    
    if not template_path.exists():
        print(f"Warning: Template directory not found: {template_dir}")
        return templates
    
    for template_file in template_path.glob('*.md'):
        templates[template_file.stem] = template_file.read_text(encoding='utf-8')
    
    print(f"Loaded {len(templates)} analytics templates")
    return templates

def analyze_paper(paper_path, templates):
    """Analyze a single paper and extract data points"""
    content = paper_path.read_text(encoding='utf-8')
    
    analysis = {
        'file': paper_path.name,
        'path': str(paper_path),
        'size': len(content),
        'lines': content.count('\n'),
        'words': len(content.split()),
        'characters': len(content)
    }
    
    # Extract frontmatter
    frontmatter = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            for line in fm_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
    
    analysis['frontmatter'] = frontmatter
    
    # Count structural elements
    analysis['headings'] = len(re.findall(r'^#+\s', content, re.MULTILINE))
    analysis['links'] = len(re.findall(r'\[\[.*?\]\]', content))
    analysis['external_links'] = len(re.findall(r'\[.*?\]\(http.*?\)', content))
    analysis['tags'] = len(re.findall(r'#\w+', content))
    analysis['code_blocks'] = len(re.findall(r'```', content)) // 2
    analysis['equations'] = len(re.findall(r'\$.*?\$', content))
    analysis['tables'] = content.count('|')
    
    # Extract specific data points
    content_lower = content.lower()
    
    # Detect content types
    analysis['has_dataview'] = 'dataview' in content_lower or '```dataviewjs' in content
    analysis['has_charts'] = 'chart' in content_lower or 'graph' in content_lower
    analysis['has_statistics'] = 'statistic' in content_lower or 'data' in content_lower
    analysis['has_metrics'] = 'metric' in content_lower or 'kpi' in content_lower
    
    # Extract key concepts (simple keyword extraction)
    key_concepts = []
    concept_keywords = ['trinity', 'logos', 'coherence', 'entropy', 'grace', 'resurrection', 
                       'axiom', 'theorem', 'proof', 'equation', 'law', 'principle']
    
    for keyword in concept_keywords:
        if keyword in content_lower:
            count = content_lower.count(keyword)
            key_concepts.append(f"{keyword} ({count})")
    
    analysis['key_concepts'] = key_concepts
    
    return analysis

def create_dashboard(paper_analysis, templates, output_dir):
    """Create individual dashboard for a paper"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create dashboard filename
    paper_name = Path(paper_analysis['file']).stem
    dashboard_file = output_path / f"{paper_name}_dashboard.md"
    
    # Build dashboard content
    dashboard = f"# Analytics Dashboard: {paper_analysis['file']}\n\n"
    dashboard += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    dashboard += f"**Source File:** `{paper_analysis['path']}`\n\n"
    dashboard += "---\n\n"
    
    # Metrics Section
    dashboard += "## 📊 Content Metrics\n\n"
    dashboard += f"- **Size:** {paper_analysis['size']:,} characters\n"
    dashboard += f"- **Lines:** {paper_analysis['lines']:,}\n"
    dashboard += f"- **Words:** {paper_analysis['words']:,}\n"
    dashboard += f"- **Headings:** {paper_analysis['headings']}\n"
    dashboard += f"- **Links:** {paper_analysis['links']} internal, {paper_analysis['external_links']} external\n"
    dashboard += f"- **Tags:** {paper_analysis['tags']}\n"
    dashboard += f"- **Equations:** {paper_analysis['equations']}\n"
    dashboard += f"- **Code Blocks:** {paper_analysis['code_blocks']}\n"
    dashboard += f"- **Tables:** {paper_analysis['tables']} table markers\n\n"
    
    # Frontmatter Section
    if paper_analysis['frontmatter']:
        dashboard += "## 📋 Metadata\n\n"
        for key, value in paper_analysis['frontmatter'].items():
            dashboard += f"- **{key}:** {value}\n"
        dashboard += "\n"
    
    # Content Analysis
    dashboard += "## 🔍 Content Analysis\n\n"
    dashboard += f"- **Has Dataview Queries:** {'Yes' if paper_analysis['has_dataview'] else 'No'}\n"
    dashboard += f"- **Has Charts/Graphs:** {'Yes' if paper_analysis['has_charts'] else 'No'}\n"
    dashboard += f"- **Has Statistics:** {'Yes' if paper_analysis['has_statistics'] else 'No'}\n"
    dashboard += f"- **Has Metrics/KPIs:** {'Yes' if paper_analysis['has_metrics'] else 'No'}\n\n"
    
    # Key Concepts
    if paper_analysis['key_concepts']:
        dashboard += "## 🎯 Key Concepts Detected\n\n"
        for concept in paper_analysis['key_concepts']:
            dashboard += f"- {concept}\n"
        dashboard += "\n"
    
    # Add template sections if available
    if templates:
        dashboard += "## 📊 Analytics Templates Applied\n\n"
        for template_name in templates.keys():
            dashboard += f"- {template_name}\n"
        dashboard += "\n"
    
    dashboard += "---\n\n"
    dashboard += f"*Dashboard generated by Paper Analytics Processor*\n"
    
    # Save dashboard
    dashboard_file.write_text(dashboard, encoding='utf-8')
    
    return dashboard_file

def process_papers(scan_dir, template_dir, output_dir=None):
    """Process all papers in directory recursively"""
    scan_path = Path(scan_dir)
    
    if not scan_path.exists():
        print(f"Error: Scan directory does not exist: {scan_dir}")
        return
    
    # If no output_dir specified, create it inside the scanned folder
    if output_dir is None:
        output_dir = scan_path / "_paper_analytics"
    else:
        output_dir = Path(output_dir)
    
    print(f"\n{'='*70}")
    print(f"PAPER ANALYTICS PROCESSOR")
    print(f"{'='*70}")
    print(f"Scanning: {scan_path}")
    print(f"Templates: {template_dir}")
    print(f"Output: {output_dir}")
    print(f"{'='*70}\n")
    
    # Load templates
    templates = load_analytics_templates(template_dir)
    
    # Find all markdown files recursively
    md_files = list(scan_path.rglob('*.md'))
    
    print(f"Found {len(md_files)} markdown files to process\n")
    
    if len(md_files) == 0:
        print("No markdown files found!")
        return
    
    # Process each file
    dashboards_created = []
    
    for idx, paper_path in enumerate(md_files, 1):
        print(f"[{idx}/{len(md_files)}] Processing: {paper_path.name}")
        
        try:
            # Analyze paper
            analysis = analyze_paper(paper_path, templates)
            
            # Create dashboard
            dashboard_file = create_dashboard(analysis, templates, output_dir)
            
            dashboards_created.append({
                'paper': paper_path.name,
                'dashboard': dashboard_file.name,
                'path': str(paper_path)
            })
            
            print(f"  ✓ Created: {dashboard_file.name}")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
    
    # Create master index
    print(f"\nCreating master index...")
    
    index_file = Path(output_dir) / "00_MASTER_INDEX.md"
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# Paper Analytics Master Index\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Source Directory:** {scan_path}\n\n")
        f.write(f"**Total Papers Processed:** {len(dashboards_created)}\n\n")
        f.write("---\n\n")
        f.write("## Individual Paper Dashboards\n\n")
        
        for item in sorted(dashboards_created, key=lambda x: x['paper']):
            f.write(f"- [{item['paper']}]({item['dashboard']})\n")
            f.write(f"  - Source: `{item['path']}`\n\n")
    
    print(f"\n{'='*70}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Processed: {len(dashboards_created)} papers")
    print(f"✓ Dashboards created: {len(dashboards_created)}")
    print(f"✓ Master index: {index_file.name}")
    print(f"✓ Output directory: {output_dir}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    # Default paths
    scan_dir = r"O:\_Theophysics\05_Logos_Papers"
    template_dir = r"O:\_Theophysics\999_Exclude\Obsidian Data Analytics\Data_Analytics"
    output_dir = "paper_analytics_dashboards"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        scan_dir = sys.argv[1]
    if len(sys.argv) > 2:
        template_dir = sys.argv[2]
    if len(sys.argv) > 3:
        output_dir = sys.argv[3]
    
    process_papers(scan_dir, template_dir, output_dir)
