"""
Excel to Interactive HTML Tables
Creates beautiful, scrollable, paginated tables from Excel data
Obsidian-style theming with dark mode support
"""

import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

def create_interactive_tables(excel_file, output_file, theme="obsidian"):
    """Generate interactive HTML tables from Excel with multiple sheet support"""
    
    print(f"\n{'='*70}")
    print(f"EXCEL TO INTERACTIVE TABLES")
    print(f"{'='*70}")
    print(f"Reading: {excel_file}")
    print(f"Output: {output_file}")
    print(f"Theme: {theme}")
    print(f"{'='*70}\n")
    
    # Read all sheets from Excel
    excel_data = pd.ExcelFile(excel_file)
    sheet_names = excel_data.sheet_names
    
    print(f"Found {len(sheet_names)} sheets: {', '.join(sheet_names)}\n")
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Theophysics Analytics - Interactive Data Tables</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        :root {{
            --bg-primary: #1e1e1e;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #383838;
            --text-primary: #dcddde;
            --text-secondary: #b9bbbe;
            --accent: #7c3aed;
            --accent-hover: #9333ea;
            --border: #4a4a4a;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0 auto;
        }}
        
        .header {{
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid var(--border);
        }}
        
        .header h1 {{
            color: var(--accent);
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            color: var(--text-secondary);
            font-size: 1.1em;
        }}
        
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }}
        
        .tab {{
            padding: 12px 24px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            color: var(--text-secondary);
            font-weight: 500;
        }}
        
        .tab:hover {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}
        
        .tab.active {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
        }}
        
        .sheet-container {{
            display: none;
            animation: fadeIn 0.3s ease;
        }}
        
        .sheet-container.active {{
            display: block;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .table-wrapper {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
            overflow: hidden;
        }}
        
        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .table-header h2 {{
            color: var(--accent);
            font-size: 1.8em;
        }}
        
        .table-info {{
            color: var(--text-secondary);
            font-size: 0.95em;
        }}
        
        .search-box {{
            padding: 10px 15px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 14px;
            width: 300px;
            transition: border-color 0.3s ease;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: var(--accent);
        }}
        
        .table-scroll {{
            overflow-x: auto;
            overflow-y: auto;
            max-height: 600px;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        thead {{
            position: sticky;
            top: 0;
            z-index: 10;
            background: var(--bg-tertiary);
        }}
        
        th {{
            background: var(--bg-tertiary);
            color: var(--accent);
            padding: 15px 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--accent);
            white-space: nowrap;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
        }}
        
        tr:hover {{
            background: var(--bg-tertiary);
        }}
        
        tr.hidden {{
            display: none;
        }}
        
        .number {{
            text-align: right;
            font-family: 'Courier New', monospace;
            color: var(--success);
        }}
        
        .highlight {{
            background: rgba(124, 58, 237, 0.2);
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
            padding: 15px;
            background: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        
        .pagination button {{
            padding: 8px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .pagination button:hover:not(:disabled) {{
            background: var(--accent);
            border-color: var(--accent);
        }}
        
        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .pagination span {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        
        .stats-bar {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .stat {{
            background: var(--bg-tertiary);
            padding: 15px 20px;
            border-radius: 8px;
            border: 1px solid var(--border);
            flex: 1;
            min-width: 150px;
        }}
        
        .stat-label {{
            color: var(--text-secondary);
            font-size: 0.85em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .stat-value {{
            color: var(--accent);
            font-size: 1.8em;
            font-weight: bold;
            margin-top: 5px;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.9em;
        }}
        
        /* Scrollbar styling */
        .table-scroll::-webkit-scrollbar {{
            width: 12px;
            height: 12px;
        }}
        
        .table-scroll::-webkit-scrollbar-track {{
            background: var(--bg-tertiary);
            border-radius: 6px;
        }}
        
        .table-scroll::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 6px;
        }}
        
        .table-scroll::-webkit-scrollbar-thumb:hover {{
            background: var(--accent);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Theophysics Analytics Data</h1>
            <p>Interactive data tables with search, sort, and pagination</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="tabs" id="tabs">
"""
    
    # Add tabs for each sheet
    for idx, sheet_name in enumerate(sheet_names):
        active_class = "active" if idx == 0 else ""
        html += f'            <div class="tab {active_class}" onclick="showSheet(\'{sheet_name}\')">{sheet_name}</div>\n'
    
    html += """
        </div>
        
"""
    
    # Add content for each sheet
    for idx, sheet_name in enumerate(sheet_names):
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        active_class = "active" if idx == 0 else ""
        
        html += f"""
        <div class="sheet-container {active_class}" id="sheet-{sheet_name}">
            <div class="table-wrapper">
                <div class="table-header">
                    <h2>{sheet_name}</h2>
                    <div class="table-info">
                        <span>{len(df)} rows × {len(df.columns)} columns</span>
                    </div>
                </div>
                
                <div class="stats-bar">
                    <div class="stat">
                        <div class="stat-label">Total Rows</div>
                        <div class="stat-value">{len(df):,}</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Columns</div>
                        <div class="stat-value">{len(df.columns)}</div>
                    </div>
"""
        
        # Add numeric stats if available
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            html += f"""
                    <div class="stat">
                        <div class="stat-label">Numeric Columns</div>
                        <div class="stat-value">{len(numeric_cols)}</div>
                    </div>
"""
        
        html += """
                </div>
                
                <input type="text" class="search-box" placeholder="🔍 Search table..." onkeyup="searchTable(this, 'table-""" + sheet_name + """')">
                
                <div class="table-scroll">
                    <table id="table-""" + sheet_name + """">
                        <thead>
                            <tr>
"""
        
        # Add column headers
        for col in df.columns:
            html += f"                                <th>{col}</th>\n"
        
        html += """
                            </tr>
                        </thead>
                        <tbody>
"""
        
        # Add data rows
        for _, row in df.iterrows():
            html += "                            <tr>\n"
            for col in df.columns:
                value = row[col]
                
                # Format value
                if pd.isna(value):
                    display_value = ""
                elif isinstance(value, (int, float)):
                    if isinstance(value, float):
                        display_value = f"{value:,.2f}" if value != int(value) else f"{int(value):,}"
                    else:
                        display_value = f"{value:,}"
                    html += f'                                <td class="number">{display_value}</td>\n'
                else:
                    display_value = str(value)
                    html += f"                                <td>{display_value}</td>\n"
            
            html += "                            </tr>\n"
        
        html += """
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
"""
    
    # Add JavaScript
    html += """
    </div>
    
    <div class="footer">
        <p>Theophysics Analytics | Interactive Data Tables</p>
        <p>Use tabs to switch between sheets | Search to filter data | Scroll to view all content</p>
    </div>
    
    <script>
        function showSheet(sheetName) {
            // Hide all sheets
            document.querySelectorAll('.sheet-container').forEach(sheet => {
                sheet.classList.remove('active');
            });
            
            // Remove active from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected sheet
            document.getElementById('sheet-' + sheetName).classList.add('active');
            
            // Activate selected tab
            event.target.classList.add('active');
        }
        
        function searchTable(input, tableId) {
            const filter = input.value.toLowerCase();
            const table = document.getElementById(tableId);
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const row = rows[i];
                const cells = row.getElementsByTagName('td');
                let found = false;
                
                for (let j = 0; j < cells.length; j++) {
                    const cell = cells[j];
                    if (cell.textContent.toLowerCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
                
                if (found) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            }
        }
    </script>
</body>
</html>
"""
    
    # Write HTML file
    Path(output_file).write_text(html, encoding='utf-8')
    
    print(f"✓ Interactive tables created\n")
    print(f"{'='*70}")
    print(f"COMPLETE")
    print(f"{'='*70}")
    print(f"Sheets included: {len(sheet_names)}")
    print(f"Output file: {output_file}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    excel_file = "Trinity_Analytics.xlsx"
    output_file = "Trinity_Data_Tables.html"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    create_interactive_tables(excel_file, output_file)
