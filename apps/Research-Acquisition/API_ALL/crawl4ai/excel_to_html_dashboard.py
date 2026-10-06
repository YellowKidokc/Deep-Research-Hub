"""
Excel to HTML Dashboard Converter
Creates interactive HTML dashboard from Excel analytics data
"""

import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

def create_html_dashboard(excel_file, output_file):
    """Generate HTML dashboard from Excel data"""
    
    print(f"\n{'='*70}")
    print(f"EXCEL TO HTML DASHBOARD GENERATOR")
    print(f"{'='*70}")
    print(f"Reading: {excel_file}")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")
    
    # Read Excel sheets
    df_all = pd.read_excel(excel_file, sheet_name='All Papers')
    df_summary = pd.read_excel(excel_file, sheet_name='Summary')
    df_top_size = pd.read_excel(excel_file, sheet_name='Top by Size')
    df_top_links = pd.read_excel(excel_file, sheet_name='Top by Links')
    df_top_equations = pd.read_excel(excel_file, sheet_name='Top by Equations')
    df_top_importance = pd.read_excel(excel_file, sheet_name='Top by Importance')
    
    # Try to read concept analysis if it exists
    try:
        df_concepts = pd.read_excel(excel_file, sheet_name='Concept Analysis')
    except:
        df_concepts = None
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trinity Papers Analytics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover {{
            background: #f8f9ff;
        }}
        
        .importance-high {{
            color: #27ae60;
            font-weight: bold;
        }}
        
        .importance-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        
        .importance-low {{
            color: #e74c3c;
        }}
        
        .chart-container {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 10px;
        }}
        
        .bar {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 30px;
            margin: 5px 0;
            border-radius: 5px;
            display: flex;
            align-items: center;
            padding-left: 10px;
            color: white;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 30px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Trinity Papers Analytics Dashboard</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total Papers Analyzed: {len(df_all)}</p>
        </div>
        
        <div class="stats-grid">
"""
    
    # Add summary statistics cards
    for _, row in df_summary.iterrows():
        metric = row['Metric']
        value = row['Value']
        
        # Format large numbers
        if isinstance(value, (int, float)) and value > 1000:
            display_value = f"{int(value):,}"
        else:
            display_value = str(value)
        
        html += f"""
            <div class="stat-card">
                <h3>{metric}</h3>
                <div class="value">{display_value}</div>
            </div>
"""
    
    html += """
        </div>
        
        <div class="section">
            <h2>🏆 Top Papers by Importance Score</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Paper</th>
                        <th>Importance</th>
                        <th>Size (chars)</th>
                        <th>Links</th>
                        <th>Equations</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for idx, row in df_top_importance.iterrows():
        importance = row['importance_score']
        importance_class = 'importance-high' if importance > 100 else ('importance-medium' if importance > 50 else 'importance-low')
        
        html += f"""
                    <tr>
                        <td>{idx + 1}</td>
                        <td>{row['filename']}</td>
                        <td class="{importance_class}">{importance:.1f}</td>
                        <td>{int(row['size_chars']):,}</td>
                        <td>{int(row['links_total'])}</td>
                        <td>{int(row['equations'])}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>📏 Largest Papers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Paper</th>
                        <th>Characters</th>
                        <th>Words</th>
                        <th>Importance</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for idx, row in df_top_size.iterrows():
        html += f"""
                    <tr>
                        <td>{idx + 1}</td>
                        <td>{row['filename']}</td>
                        <td>{int(row['size_chars']):,}</td>
                        <td>{int(row['words']):,}</td>
                        <td>{row['importance_score']:.1f}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🔗 Most Connected Papers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Paper</th>
                        <th>Total Links</th>
                        <th>Internal</th>
                        <th>External</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for idx, row in df_top_links.iterrows():
        html += f"""
                    <tr>
                        <td>{idx + 1}</td>
                        <td>{row['filename']}</td>
                        <td><strong>{int(row['links_total'])}</strong></td>
                        <td>{int(row['links_internal'])}</td>
                        <td>{int(row['links_external'])}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🔢 Most Mathematical Papers</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Paper</th>
                        <th>Equations</th>
                        <th>Words</th>
                        <th>Importance</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for idx, row in df_top_equations.iterrows():
        html += f"""
                    <tr>
                        <td>{idx + 1}</td>
                        <td>{row['filename']}</td>
                        <td><strong>{int(row['equations'])}</strong></td>
                        <td>{int(row['words']):,}</td>
                        <td>{row['importance_score']:.1f}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
"""
    
    # Add concept analysis if available
    if df_concepts is not None:
        html += """
        <div class="section">
            <h2>🎯 Key Concepts Frequency</h2>
            <div class="chart-container">
"""
        
        max_mentions = df_concepts['Total Mentions'].max()
        
        for _, row in df_concepts.head(15).iterrows():
            concept = row['Concept']
            mentions = int(row['Total Mentions'])
            width = (mentions / max_mentions) * 100
            
            html += f"""
                <div class="bar" style="width: {width}%">
                    {concept.capitalize()}: {mentions}
                </div>
"""
        
        html += """
            </div>
        </div>
"""
    
    html += f"""
        <div class="footer">
            <p>Trinity Papers Analytics Dashboard</p>
            <p>Generated by Paper Analytics Processor | {datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    Path(output_file).write_text(html, encoding='utf-8')
    
    print(f"✓ HTML dashboard created: {output_file}\n")
    print(f"{'='*70}")
    print(f"DASHBOARD COMPLETE")
    print(f"{'='*70}")
    print(f"Open {output_file} in your browser to view the dashboard")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    excel_file = "Trinity_Analytics.xlsx"
    output_file = "Trinity_Dashboard.html"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    create_html_dashboard(excel_file, output_file)
