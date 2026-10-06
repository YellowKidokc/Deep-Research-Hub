# Excel File Converter - Interactive Multi-Format Converter
# Works from any directory, converts to CSV, Markdown, HTML, JSON, TSV

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   Excel File Converter" -ForegroundColor Cyan
Write-Host "   Multi-format conversion with interactive selection" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$currentDir = Get-Location
Write-Host "Searching for Excel files in: $currentDir" -ForegroundColor Yellow
Write-Host ""

# Find all Excel files
$excelFiles = Get-ChildItem -Path $currentDir -Filter "*.xlsx" -File
$excelFiles += Get-ChildItem -Path $currentDir -Filter "*.xls" -File

if ($excelFiles.Count -eq 0) {
    Write-Host "No Excel files found in this directory." -ForegroundColor Red
    Write-Host "Make sure you have .xlsx or .xls files here." -ForegroundColor Yellow
    exit 1
}

# Display found files
Write-Host "Found $($excelFiles.Count) Excel file(s):" -ForegroundColor Green
Write-Host ""
for ($i = 0; $i -lt $excelFiles.Count; $i++) {
    $num = $i + 1
    $file = $excelFiles[$i]
    $sizeKB = [math]::Round($file.Length / 1KB, 1)
    Write-Host "  [$num] $($file.Name) ($sizeKB KB)" -ForegroundColor White
}

Write-Host ""
Write-Host "Selection options:" -ForegroundColor Cyan
Write-Host "  - Enter numbers separated by commas: 1,2,3" -ForegroundColor Gray
Write-Host "  - Enter ranges: 1-3,5,7-9" -ForegroundColor Gray
Write-Host "  - Enter 'all' for all files" -ForegroundColor Gray
Write-Host ""

# Get file selection
$selection = Read-Host "Which files do you want to convert?"

# Parse selection
$selectedIndices = @()

if ($selection.ToLower() -eq "all") {
    $selectedIndices = 0..($excelFiles.Count - 1)
} else {
    # Parse comma-separated values and ranges
    $parts = $selection -split ','
    foreach ($part in $parts) {
        $part = $part.Trim()
        
        # Check for range (e.g., "1-3")
        if ($part -match '^(\d+)-(\d+)$') {
            $start = [int]$matches[1] - 1
            $end = [int]$matches[2] - 1
            
            if ($start -ge 0 -and $end -lt $excelFiles.Count -and $start -le $end) {
                $selectedIndices += $start..$end
            }
        }
        # Single number
        elseif ($part -match '^\d+$') {
            $index = [int]$part - 1
            if ($index -ge 0 -and $index -lt $excelFiles.Count) {
                $selectedIndices += $index
            }
        }
    }
}

# Remove duplicates and sort
$selectedIndices = $selectedIndices | Select-Object -Unique | Sort-Object

if ($selectedIndices.Count -eq 0) {
    Write-Host "Error: No valid files selected" -ForegroundColor Red
    exit 1
}

# Show selected files
Write-Host ""
Write-Host "Selected $($selectedIndices.Count) file(s):" -ForegroundColor Green
foreach ($idx in $selectedIndices) {
    Write-Host "  ✓ $($excelFiles[$idx].Name)" -ForegroundColor White
}

# Format selection
Write-Host ""
Write-Host "Available output formats:" -ForegroundColor Cyan
Write-Host "  [1] CSV (Comma-Separated Values)" -ForegroundColor White
Write-Host "  [2] TSV (Tab-Separated Values)" -ForegroundColor White
Write-Host "  [3] Markdown (Tables)" -ForegroundColor White
Write-Host "  [4] HTML (Web tables)" -ForegroundColor White
Write-Host "  [5] JSON (JavaScript Object Notation)" -ForegroundColor White
Write-Host ""
Write-Host "Selection options:" -ForegroundColor Cyan
Write-Host "  - Enter numbers: 1,3,5" -ForegroundColor Gray
Write-Host "  - Enter 'all' for all formats" -ForegroundColor Gray
Write-Host ""

$formatSelection = Read-Host "Which format(s) do you want?"

# Parse format selection
$formats = @()
$formatMap = @{
    "1" = "CSV"
    "2" = "TSV"
    "3" = "Markdown"
    "4" = "HTML"
    "5" = "JSON"
}

if ($formatSelection.ToLower() -eq "all") {
    $formats = @("CSV", "TSV", "Markdown", "HTML", "JSON")
} else {
    $parts = $formatSelection -split ','
    foreach ($part in $parts) {
        $part = $part.Trim()
        if ($formatMap.ContainsKey($part)) {
            $formats += $formatMap[$part]
        }
    }
}

if ($formats.Count -eq 0) {
    Write-Host "Error: No valid formats selected" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Selected format(s): $($formats -join ', ')" -ForegroundColor Green

# Create output directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = Join-Path $currentDir "excel_converted_$timestamp"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

Write-Host ""
Write-Host "Output directory: $outputDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting conversion..." -ForegroundColor Green
Write-Host ""

# Create Python conversion script
$pythonScript = @"
import sys
import os
from pathlib import Path
import pandas as pd
import json

def convert_excel_to_formats(excel_path, output_dir, formats):
    """Convert Excel file to multiple formats"""
    
    file_name = Path(excel_path).stem
    print(f"Converting: {Path(excel_path).name}")
    
    # Check if file exists
    if not os.path.exists(excel_path):
        print(f"  ✗ Error: File not found: {excel_path}")
        return False
    
    # Check if file is locked
    try:
        with open(excel_path, 'rb') as f:
            pass
    except PermissionError:
        print(f"  ✗ Error: File is locked (might be open in Excel)")
        return False
    except Exception as e:
        print(f"  ✗ Error accessing file: {str(e)}")
        return False
    
    try:
        # Read Excel file (all sheets)
        print(f"  Reading Excel file...")
        excel_data = pd.read_excel(excel_path, sheet_name=None, engine='openpyxl')
        print(f"  Found {len(excel_data)} sheet(s)")
        
        results = []
        
        for sheet_name, df in excel_data.items():
            print(f"  Processing sheet: {sheet_name} ({len(df)} rows, {len(df.columns)} columns)")
            
            # Clean sheet name for filename
            safe_sheet_name = sheet_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
            base_name = f"{file_name}_{safe_sheet_name}" if len(excel_data) > 1 else file_name
            
            # CSV
            if 'CSV' in formats:
                csv_path = os.path.join(output_dir, f"{base_name}.csv")
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                results.append(f"    ✓ CSV: {base_name}.csv")
            
            # TSV
            if 'TSV' in formats:
                tsv_path = os.path.join(output_dir, f"{base_name}.tsv")
                df.to_csv(tsv_path, sep='\t', index=False, encoding='utf-8-sig')
                results.append(f"    ✓ TSV: {base_name}.tsv")
            
            # Markdown
            if 'Markdown' in formats:
                md_path = os.path.join(output_dir, f"{base_name}.md")
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {file_name} - {sheet_name}\n\n")
                    f.write(df.to_markdown(index=False))
                results.append(f"    ✓ Markdown: {base_name}.md")
            
            # HTML
            if 'HTML' in formats:
                html_path = os.path.join(output_dir, f"{base_name}.html")
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(f"<!DOCTYPE html>\n<html>\n<head>\n")
                    f.write(f"<title>{file_name} - {sheet_name}</title>\n")
                    f.write("<style>\n")
                    f.write("table { border-collapse: collapse; width: 100%; }\n")
                    f.write("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n")
                    f.write("th { background-color: #4CAF50; color: white; }\n")
                    f.write("tr:nth-child(even) { background-color: #f2f2f2; }\n")
                    f.write("</style>\n</head>\n<body>\n")
                    f.write(f"<h1>{file_name} - {sheet_name}</h1>\n")
                    f.write(df.to_html(index=False, border=0))
                    f.write("\n</body>\n</html>")
                results.append(f"    ✓ HTML: {base_name}.html")
            
            # JSON
            if 'JSON' in formats:
                json_path = os.path.join(output_dir, f"{base_name}.json")
                df.to_json(json_path, orient='records', indent=2, force_ascii=False)
                results.append(f"    ✓ JSON: {base_name}.json")
        
        for result in results:
            print(result)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        import traceback
        print(f"  Details: {traceback.format_exc()}")
        return False

# Main conversion
if __name__ == "__main__":
    excel_files = sys.argv[1].split('|')
    output_dir = sys.argv[2]
    formats = sys.argv[3].split(',')
    
    successful = 0
    failed = 0
    
    for excel_file in excel_files:
        if convert_excel_to_formats(excel_file, output_dir, formats):
            successful += 1
        else:
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Conversion complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")
"@

# Save Python script
$pythonScript | Out-File -FilePath "temp_excel_converter.py" -Encoding UTF8

# Prepare file list
$fileList = ($selectedIndices | ForEach-Object { $excelFiles[$_].FullName }) -join '|'
$formatList = $formats -join ','

# Check if Python is available
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check for required packages
Write-Host "Checking Python packages..." -ForegroundColor Yellow
$packagesNeeded = @()

$checkPandas = python -c "import pandas" 2>&1
if ($LASTEXITCODE -ne 0) { 
    $packagesNeeded += "pandas" 
    Write-Host "  Need to install: pandas" -ForegroundColor Yellow
}

$checkOpenpyxl = python -c "import openpyxl" 2>&1
if ($LASTEXITCODE -ne 0) { 
    $packagesNeeded += "openpyxl" 
    Write-Host "  Need to install: openpyxl" -ForegroundColor Yellow
}

if ("Markdown" -in $formats) {
    $checkTabulate = python -c "import tabulate" 2>&1
    if ($LASTEXITCODE -ne 0) { 
        $packagesNeeded += "tabulate" 
        Write-Host "  Need to install: tabulate" -ForegroundColor Yellow
    }
}

if ($packagesNeeded.Count -gt 0) {
    Write-Host ""
    Write-Host "Installing required packages..." -ForegroundColor Yellow
    foreach ($package in $packagesNeeded) {
        Write-Host "  Installing $package..." -ForegroundColor Gray
        python -m pip install $package 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ $package installed" -ForegroundColor Green
        } else {
            Write-Host "  ✗ Failed to install $package" -ForegroundColor Red
        }
    }
    Write-Host ""
} else {
    Write-Host "✓ All required packages are installed" -ForegroundColor Green
    Write-Host ""
}

# Run conversion with error handling
Write-Host "Running Python converter..." -ForegroundColor Yellow
Write-Host ""

try {
    $output = python temp_excel_converter.py "$fileList" "$outputDir" "$formatList" 2>&1
    $exitCode = $LASTEXITCODE
    
    # Show output
    $output | ForEach-Object { Write-Host $_ }
    
    if ($exitCode -ne 0) {
        Write-Host ""
        Write-Host "✗ Python script exited with error code: $exitCode" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "  1. Make sure Excel files are not open in Excel" -ForegroundColor Gray
        Write-Host "  2. Check if files are not corrupted" -ForegroundColor Gray
        Write-Host "  3. Try with a single file first" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Press any key to continue..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} catch {
    Write-Host ""
    Write-Host "✗ Error running Python script:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Cleanup
Remove-Item "temp_excel_converter.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Conversion Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Show what was created
if (Test-Path $outputDir) {
    $outputFiles = Get-ChildItem $outputDir -File
    Write-Host "Created $($outputFiles.Count) file(s):" -ForegroundColor Cyan
    
    # Group by extension
    $byExtension = $outputFiles | Group-Object Extension
    foreach ($group in $byExtension) {
        Write-Host "  $($group.Count) $($group.Name) files" -ForegroundColor White
    }
}

Write-Host ""
$openFolder = Read-Host "Open output folder? (y/n, default: y)"
if ([string]::IsNullOrWhiteSpace($openFolder) -or $openFolder -eq 'y') {
    Invoke-Item $outputDir
}