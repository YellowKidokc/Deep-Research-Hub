"""
Obsidian Analytics Processor
Processes local Obsidian vault files and extracts analytics data
"""

from pathlib import Path
from datetime import datetime
import re
import sys

def process_markdown_file(file_path):
    """Process a single markdown file and extract metadata"""
    try:
        content = file_path.read_text(encoding='utf-8', errors='replace')
        
        # Extract frontmatter if exists
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                for line in fm_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
        
        # Count various elements
        stats = {
            'file': file_path.name,
            'path': str(file_path),
            'size': len(content),
            'lines': content.count('\n'),
            'headings': len(re.findall(r'^#+\s', content, re.MULTILINE)),
            'links': len(re.findall(r'\[\[.*?\]\]', content)),
            'tags': len(re.findall(r'#\w+', content)),
            'code_blocks': len(re.findall(r'```', content)) // 2,
            'tables': content.count('|'),
            'equations': len(re.findall(r'\$\$[\s\S]*?\$\$|\$[^$\n]+\$', content)),
            'frontmatter': frontmatter
        }
        
        # Check for dashboard indicators
        content_lower = content.lower()
        stats['is_dashboard'] = any(word in content_lower for word in ['dashboard', 'analytics', 'statistics', 'metrics'])
        stats['has_dataview'] = 'dataview' in content_lower or '```dataviewjs' in content
        stats['has_charts'] = 'chart' in content_lower or 'graph' in content_lower
        
        return stats
        
    except Exception as e:
        return {
            'file': file_path.name,
            'path': str(file_path),
            'error': str(e)
        }

def scan_obsidian_vault(vault_path, output_dir):
    """Scan entire Obsidian vault and create analytics report"""
    vault = Path(vault_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not vault.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"OBSIDIAN ANALYTICS PROCESSOR")
    print(f"{'='*70}")
    print(f"Vault: {vault}")
    print(f"Output: {output_path}")
    print(f"{'='*70}\n")
    
    # Find all markdown files
    md_files = list(vault.rglob('*.md'))
    
    print(f"Found {len(md_files)} markdown files")
    print("Processing...\n")
    
    all_stats = []
    dashboard_files = []
    
    for idx, file_path in enumerate(md_files, 1):
        if idx % 10 == 0:
            print(f"  Processed {idx}/{len(md_files)} files...")
        
        stats = process_markdown_file(file_path)
        all_stats.append(stats)
        
        if stats.get('is_dashboard'):
            dashboard_files.append(stats)
    
    print(f"\n✓ Processed {len(md_files)} files")
    print(f"✓ Found {len(dashboard_files)} dashboard files\n")
    
    # Create comprehensive report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_path / f"obsidian_analytics_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Obsidian Vault Analytics Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Vault Path:** {vault}\n\n")
        f.write(f"**Total Files:** {len(md_files)}\n\n")
        f.write("---\n\n")
        
        # Overall statistics
        f.write("## Overall Statistics\n\n")
        
        total_size = sum(s.get('size', 0) for s in all_stats if 'error' not in s)
        total_lines = sum(s.get('lines', 0) for s in all_stats if 'error' not in s)
        total_headings = sum(s.get('headings', 0) for s in all_stats if 'error' not in s)
        total_links = sum(s.get('links', 0) for s in all_stats if 'error' not in s)
        total_tags = sum(s.get('tags', 0) for s in all_stats if 'error' not in s)
        total_equations = sum(s.get('equations', 0) for s in all_stats if 'error' not in s)
        
        f.write(f"- **Total Content:** {total_size:,} characters\n")
        f.write(f"- **Total Lines:** {total_lines:,}\n")
        f.write(f"- **Total Headings:** {total_headings:,}\n")
        f.write(f"- **Total Links:** {total_links:,}\n")
        f.write(f"- **Total Tags:** {total_tags:,}\n")
        f.write(f"- **Total Equations:** {total_equations:,}\n")
        f.write(f"- **Dashboard Files:** {len(dashboard_files)}\n")
        f.write(f"- **Files with Dataview:** {sum(1 for s in all_stats if s.get('has_dataview'))}\n")
        f.write(f"- **Files with Charts:** {sum(1 for s in all_stats if s.get('has_charts'))}\n\n")
        
        # Dashboard files section
        if dashboard_files:
            f.write("## Dashboard Files\n\n")
            f.write(f"Found {len(dashboard_files)} files identified as dashboards:\n\n")
            
            for stats in sorted(dashboard_files, key=lambda x: x.get('size', 0), reverse=True):
                f.write(f"### {stats['file']}\n\n")
                f.write(f"- **Path:** `{stats['path']}`\n")
                f.write(f"- **Size:** {stats.get('size', 0):,} characters\n")
                f.write(f"- **Lines:** {stats.get('lines', 0):,}\n")
                f.write(f"- **Headings:** {stats.get('headings', 0)}\n")
                f.write(f"- **Links:** {stats.get('links', 0)}\n")
                f.write(f"- **Tags:** {stats.get('tags', 0)}\n")
                f.write(f"- **Equations:** {stats.get('equations', 0)}\n")
                f.write(f"- **Has Dataview:** {'Yes' if stats.get('has_dataview') else 'No'}\n")
                f.write(f"- **Has Charts:** {'Yes' if stats.get('has_charts') else 'No'}\n\n")
        
        # Top files by size
        f.write("## Largest Files (Top 20)\n\n")
        
        sorted_by_size = sorted([s for s in all_stats if 'error' not in s], 
                               key=lambda x: x.get('size', 0), reverse=True)[:20]
        
        for idx, stats in enumerate(sorted_by_size, 1):
            f.write(f"{idx}. **{stats['file']}** - {stats.get('size', 0):,} characters\n")
            f.write(f"   - Path: `{stats['path']}`\n\n")
        
        # Files by folder
        f.write("## Files by Folder\n\n")
        
        folders = {}
        for stats in all_stats:
            if 'error' not in stats:
                folder = str(Path(stats['path']).parent)
                folders[folder] = folders.get(folder, 0) + 1
        
        for folder, count in sorted(folders.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{folder}** - {count} files\n")
        
        # Errors if any
        errors = [s for s in all_stats if 'error' in s]
        if errors:
            f.write("\n## Processing Errors\n\n")
            for stats in errors:
                f.write(f"- **{stats['file']}**: {stats['error']}\n")
    
    # Create dashboard-specific report
    if dashboard_files:
        dashboard_report = output_path / f"dashboard_files_{timestamp}.md"
        
        with open(dashboard_report, 'w', encoding='utf-8') as f:
            f.write("# Dashboard Files Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Dashboards:** {len(dashboard_files)}\n\n")
            f.write("---\n\n")
            
            for idx, stats in enumerate(sorted(dashboard_files, key=lambda x: x['file']), 1):
                f.write(f"## {idx}. {stats['file']}\n\n")
                f.write(f"**Full Path:** `{stats['path']}`\n\n")
                
                # Read and include the actual content
                try:
                    content = Path(stats['path']).read_text(encoding='utf-8')
                    f.write("### Content Preview\n\n")
                    f.write("```markdown\n")
                    # Include first 50 lines
                    lines = content.split('\n')[:50]
                    f.write('\n'.join(lines))
                    if len(content.split('\n')) > 50:
                        f.write("\n\n... (truncated)")
                    f.write("\n```\n\n")
                except:
                    f.write("*Could not read file content*\n\n")
                
                f.write("---\n\n")
    
    print(f"{'='*70}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Main report: {report_file.name}")
    if dashboard_files:
        print(f"✓ Dashboard report: dashboard_files_{timestamp}.md")
    print(f"✓ Output directory: {output_path}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    vault_path = r"O:\_Theophysics\999_Exclude\Obsidian Data Analytics"
    output_dir = "obsidian_analytics_output"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    scan_obsidian_vault(vault_path, output_dir)
