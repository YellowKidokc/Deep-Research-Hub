"""
Dashboard to Excel Converter
Extracts all metrics from individual dashboards into consolidated Excel spreadsheet
"""

import re
from pathlib import Path
import pandas as pd
from datetime import datetime
import sys

def parse_dashboard(dashboard_file):
    """Extract all metrics from a dashboard markdown file"""
    content = dashboard_file.read_text(encoding='utf-8')
    
    data = {
        'filename': dashboard_file.stem.replace('_dashboard', ''),
        'dashboard_path': str(dashboard_file)
    }
    
    # Extract source file path
    source_match = re.search(r'\*\*Source File:\*\* `(.+?)`', content)
    if source_match:
        data['source_path'] = source_match.group(1)
    
    # Extract content metrics
    size_match = re.search(r'\*\*Size:\*\* ([\d,]+) characters', content)
    if size_match:
        data['size_chars'] = int(size_match.group(1).replace(',', ''))
    
    lines_match = re.search(r'\*\*Lines:\*\* ([\d,]+)', content)
    if lines_match:
        data['lines'] = int(lines_match.group(1).replace(',', ''))
    
    words_match = re.search(r'\*\*Words:\*\* ([\d,]+)', content)
    if words_match:
        data['words'] = int(words_match.group(1).replace(',', ''))
    
    headings_match = re.search(r'\*\*Headings:\*\* (\d+)', content)
    if headings_match:
        data['headings'] = int(headings_match.group(1))
    
    links_match = re.search(r'\*\*Links:\*\* (\d+) internal, (\d+) external', content)
    if links_match:
        data['links_internal'] = int(links_match.group(1))
        data['links_external'] = int(links_match.group(2))
        data['links_total'] = data['links_internal'] + data['links_external']
    
    tags_match = re.search(r'\*\*Tags:\*\* (\d+)', content)
    if tags_match:
        data['tags'] = int(tags_match.group(1))
    
    equations_match = re.search(r'\*\*Equations:\*\* (\d+)', content)
    if equations_match:
        data['equations'] = int(equations_match.group(1))
    
    code_blocks_match = re.search(r'\*\*Code Blocks:\*\* (\d+)', content)
    if code_blocks_match:
        data['code_blocks'] = int(code_blocks_match.group(1))
    
    tables_match = re.search(r'\*\*Tables:\*\* (\d+)', content)
    if tables_match:
        data['tables'] = int(tables_match.group(1))
    
    # Extract content analysis flags
    data['has_dataview'] = 'Has Dataview Queries:** Yes' in content
    data['has_charts'] = 'Has Charts/Graphs:** Yes' in content
    data['has_statistics'] = 'Has Statistics:** Yes' in content
    data['has_metrics'] = 'Has Metrics/KPIs:** Yes' in content
    
    # Extract key concepts
    concepts_section = re.search(r'## 🎯 Key Concepts Detected\n\n(.+?)\n\n', content, re.DOTALL)
    if concepts_section:
        concepts_text = concepts_section.group(1)
        concept_lines = concepts_text.strip().split('\n')
        
        for line in concept_lines:
            match = re.match(r'- (\w+) \((\d+)\)', line)
            if match:
                concept_name = match.group(1)
                concept_count = int(match.group(2))
                data[f'concept_{concept_name}'] = concept_count
    
    # Calculate derived metrics
    if 'words' in data and 'size_chars' in data and data['size_chars'] > 0:
        data['avg_word_length'] = round(data['size_chars'] / data['words'], 2)
    
    if 'words' in data and 'headings' in data and data['headings'] > 0:
        data['words_per_heading'] = round(data['words'] / data['headings'], 1)
    
    # Calculate importance score (composite metric)
    importance = 0
    if 'size_chars' in data:
        importance += min(data['size_chars'] / 1000, 50)  # Max 50 points for size
    if 'links_total' in data:
        importance += data['links_total'] * 2  # 2 points per link
    if 'equations' in data:
        importance += data['equations'] * 3  # 3 points per equation
    if 'headings' in data:
        importance += data['headings']  # 1 point per heading
    
    data['importance_score'] = round(importance, 1)
    
    return data

def process_dashboards_to_excel(dashboard_dir, output_file):
    """Process all dashboards and create Excel file"""
    dashboard_path = Path(dashboard_dir)
    
    if not dashboard_path.exists():
        print(f"Error: Dashboard directory not found: {dashboard_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"DASHBOARD TO EXCEL CONVERTER")
    print(f"{'='*70}")
    print(f"Processing: {dashboard_path}")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")
    
    # Find all dashboard files (exclude master index)
    dashboard_files = [f for f in dashboard_path.glob('*_dashboard.md')]
    
    print(f"Found {len(dashboard_files)} dashboard files\n")
    
    if len(dashboard_files) == 0:
        print("No dashboard files found!")
        return
    
    # Process each dashboard
    all_data = []
    
    for idx, dashboard_file in enumerate(dashboard_files, 1):
        if idx % 20 == 0:
            print(f"  Processed {idx}/{len(dashboard_files)} dashboards...")
        
        try:
            data = parse_dashboard(dashboard_file)
            all_data.append(data)
        except Exception as e:
            print(f"  Error processing {dashboard_file.name}: {str(e)}")
    
    print(f"\n✓ Processed {len(all_data)} dashboards successfully\n")
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Fill NaN values
    df = df.fillna(0)
    
    # Sort by importance score
    df = df.sort_values('importance_score', ascending=False)
    
    # Create Excel file with multiple sheets
    print("Creating Excel file with multiple sheets...")
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Main data sheet
        df.to_excel(writer, sheet_name='All Papers', index=False)
        
        # Summary statistics sheet
        summary_data = {
            'Metric': [
                'Total Papers',
                'Total Characters',
                'Total Words',
                'Total Lines',
                'Total Headings',
                'Total Internal Links',
                'Total External Links',
                'Total Equations',
                'Total Code Blocks',
                'Total Tables',
                'Avg Paper Size (chars)',
                'Avg Paper Size (words)',
                'Avg Links per Paper',
                'Avg Equations per Paper',
                'Papers with Dataview',
                'Papers with Charts',
                'Papers with Statistics',
                'Papers with Metrics/KPIs'
            ],
            'Value': [
                len(df),
                int(df['size_chars'].sum()),
                int(df['words'].sum()),
                int(df['lines'].sum()),
                int(df['headings'].sum()),
                int(df['links_internal'].sum()),
                int(df['links_external'].sum()),
                int(df['equations'].sum()),
                int(df['code_blocks'].sum()),
                int(df['tables'].sum()),
                int(df['size_chars'].mean()),
                int(df['words'].mean()),
                round(df['links_total'].mean(), 1),
                round(df['equations'].mean(), 1),
                int(df['has_dataview'].sum()),
                int(df['has_charts'].sum()),
                int(df['has_statistics'].sum()),
                int(df['has_metrics'].sum())
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Top papers by different metrics
        top_by_size = df.nlargest(20, 'size_chars')[['filename', 'size_chars', 'words', 'importance_score']]
        top_by_size.to_excel(writer, sheet_name='Top by Size', index=False)
        
        top_by_links = df.nlargest(20, 'links_total')[['filename', 'links_total', 'links_internal', 'links_external']]
        top_by_links.to_excel(writer, sheet_name='Top by Links', index=False)
        
        top_by_equations = df.nlargest(20, 'equations')[['filename', 'equations', 'words', 'importance_score']]
        top_by_equations.to_excel(writer, sheet_name='Top by Equations', index=False)
        
        top_by_importance = df.nlargest(20, 'importance_score')[['filename', 'importance_score', 'size_chars', 'links_total', 'equations']]
        top_by_importance.to_excel(writer, sheet_name='Top by Importance', index=False)
        
        # Concept analysis (if concept columns exist)
        concept_cols = [col for col in df.columns if col.startswith('concept_')]
        if concept_cols:
            concept_totals = df[concept_cols].sum().sort_values(ascending=False)
            concept_df = pd.DataFrame({
                'Concept': [col.replace('concept_', '') for col in concept_totals.index],
                'Total Mentions': concept_totals.values
            })
            concept_df.to_excel(writer, sheet_name='Concept Analysis', index=False)
    
    print(f"✓ Excel file created: {output_file}\n")
    
    # Print summary
    print(f"{'='*70}")
    print(f"SUMMARY STATISTICS")
    print(f"{'='*70}")
    print(f"Total Papers: {len(df)}")
    print(f"Total Words: {int(df['words'].sum()):,}")
    print(f"Total Characters: {int(df['size_chars'].sum()):,}")
    print(f"Total Equations: {int(df['equations'].sum())}")
    print(f"Total Links: {int(df['links_total'].sum())}")
    print(f"\nAverage Paper Size: {int(df['words'].mean()):,} words")
    print(f"Largest Paper: {int(df['size_chars'].max()):,} characters")
    print(f"Most Connected: {int(df['links_total'].max())} links")
    print(f"Most Mathematical: {int(df['equations'].max())} equations")
    print(f"{'='*70}\n")
    
    return df

if __name__ == "__main__":
    dashboard_dir = "Trinity_paper_dashboards"
    output_file = "Trinity_Analytics.xlsx"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        dashboard_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    df = process_dashboards_to_excel(dashboard_dir, output_file)
