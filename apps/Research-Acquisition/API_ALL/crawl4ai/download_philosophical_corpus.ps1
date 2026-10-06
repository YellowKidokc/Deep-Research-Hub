# Philosophical Corpus Batch Downloader
# Downloads comprehensive collection of philosophical, religious, and scientific texts

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   Philosophical Corpus Batch Downloader" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

$csvFile = "philosophical_corpus_urls.csv"

if (-not (Test-Path $csvFile)) {
    Write-Host "Error: $csvFile not found!" -ForegroundColor Red
    Write-Host "Make sure the CSV file is in the same directory." -ForegroundColor Yellow
    exit 1
}

# Load the CSV
$urls = Import-Csv $csvFile

Write-Host "Loaded $($urls.Count) URLs from corpus" -ForegroundColor Green
Write-Host ""

# Show summary by tier
$tiers = $urls | Group-Object Tier | Sort-Object Name
Write-Host "Corpus Summary:" -ForegroundColor Cyan
foreach ($tier in $tiers) {
    Write-Host "  $($tier.Name): $($tier.Count) texts" -ForegroundColor White
}
Write-Host ""

# Filter options
Write-Host "Download options:" -ForegroundColor Cyan
Write-Host "  1. Priority only (HIGH priority items - ~20 texts)" -ForegroundColor White
Write-Host "  2. Priority + Medium (~40 texts)" -ForegroundColor White
Write-Host "  3. Everything (~70 texts)" -ForegroundColor White
Write-Host "  4. Specific tier only" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Choose option (1-4, default: 1)"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

$filteredUrls = @()

switch ($choice) {
    "1" {
        $filteredUrls = $urls | Where-Object { $_.Priority -eq "HIGH" }
        Write-Host "Downloading $($filteredUrls.Count) HIGH priority texts" -ForegroundColor Green
    }
    "2" {
        $filteredUrls = $urls | Where-Object { $_.Priority -in @("HIGH", "MEDIUM") }
        Write-Host "Downloading $($filteredUrls.Count) HIGH + MEDIUM priority texts" -ForegroundColor Green
    }
    "3" {
        $filteredUrls = $urls
        Write-Host "Downloading ALL $($filteredUrls.Count) texts" -ForegroundColor Green
    }
    "4" {
        Write-Host ""
        Write-Host "Available tiers:" -ForegroundColor Cyan
        $tiers | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor White }
        Write-Host ""
        $tierChoice = Read-Host "Enter tier number or name"
        $filteredUrls = $urls | Where-Object { $_.Tier -eq $tierChoice }
        Write-Host "Downloading $($filteredUrls.Count) texts from tier $tierChoice" -ForegroundColor Green
    }
    default {
        $filteredUrls = $urls | Where-Object { $_.Priority -eq "HIGH" }
    }
}

if ($filteredUrls.Count -eq 0) {
    Write-Host "No URLs matched your filter!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Output directory
$defaultDir = Join-Path (Get-Location) "philosophical_corpus"
$outputDir = Read-Host "Output directory (default: $defaultDir)"
if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host ""
Write-Host "Output format:" -ForegroundColor Cyan
Write-Host "  1. Markdown only (recommended)" -ForegroundColor White
Write-Host "  2. Markdown + HTML" -ForegroundColor White
Write-Host "  3. HTML only" -ForegroundColor White
Write-Host ""

$formatChoice = Read-Host "Choose format (1-3, default: 1)"
if ([string]::IsNullOrWhiteSpace($formatChoice)) { $formatChoice = "1" }

$saveMarkdown = $formatChoice -in @("1", "2")
$saveHtml = $formatChoice -in @("2", "3")

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "CONFIGURATION COMPLETE" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "  Texts to download: $($filteredUrls.Count)" -ForegroundColor White
Write-Host "  Output directory: $outputDir" -ForegroundColor White
Write-Host "  Format: $(if($saveMarkdown){'Markdown'}else{''})$(if($saveMarkdown -and $saveHtml){' + '})$(if($saveHtml){'HTML'})" -ForegroundColor White
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Creating Python download script..." -ForegroundColor Yellow

# Create download script
$urlsJson = $filteredUrls | ConvertTo-Json -Compress
$downloadScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import json
import re
from urllib.parse import urlparse
from datetime import datetime

def sanitize_filename(text, category):
    # Create filename from text name and category
    filename = f"{category}_{text}"
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.replace(' ', '_')
    
    if len(filename) > 150:
        filename = filename[:150]
    
    return filename

async def download_corpus(urls_data, output_dir, save_md, save_html):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Parse JSON
    urls = json.loads(urls_data)
    
    print(f"{'='*70}")
    print(f"DOWNLOADING {len(urls)} TEXTS")
    print(f"{'='*70}")
    print()
    
    results = {
        'success': [],
        'failed': []
    }
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for idx, item in enumerate(urls, 1):
            url = item['URL']
            text_name = item['Text']
            category = item['Category']
            tier = item['Tier']
            
            print(f"\n{'='*70}")
            print(f"[{idx}/{len(urls)}] {text_name}")
            print(f"Category: {category} | Tier: {tier}")
            print(f"URL: {url}")
            print(f"{'='*70}")
            
            try:
                result = await crawler.arun(url=url)
                
                if result.success:
                    base_filename = sanitize_filename(text_name, category)
                    
                    if save_md:
                        md_file = output_path / f"{base_filename}.md"
                        
                        # Create header with metadata
                        header = f"# {text_name}\n\n"
                        header += f"**Category:** {category}\n\n"
                        header += f"**Tier:** {tier}\n\n"
                        header += f"**Priority:** {item.get('Priority', 'N/A')}\n\n"
                        header += f"**URL:** {url}\n\n"
                        header += f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        header += f"**Notes:** {item.get('Notes', 'N/A')}\n\n"
                        header += "---\n\n"
                        
                        md_file.write_text(header + result.markdown, encoding='utf-8')
                        print(f"  ✓ Saved markdown: {md_file.name}")
                    
                    if save_html:
                        html_file = output_path / f"{base_filename}.html"
                        html_file.write_text(result.html, encoding='utf-8')
                        print(f"  ✓ Saved HTML: {html_file.name}")
                    
                    results['success'].append({
                        'text': text_name,
                        'url': url,
                        'category': category,
                        'tier': tier
                    })
                else:
                    print(f"  ✗ Failed: {result.error_message or 'Unknown error'}")
                    results['failed'].append({
                        'text': text_name,
                        'url': url,
                        'error': result.error_message or 'Unknown error'
                    })
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                results['failed'].append({
                    'text': text_name,
                    'url': url,
                    'error': str(e)
                })
    
    # Create summary report
    print()
    print(f"{'='*70}")
    print("DOWNLOAD COMPLETE - GENERATING REPORT")
    print(f"{'='*70}")
    
    report_file = output_path / f"download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Philosophical Corpus Download Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Attempted:** {len(urls)}\n\n")
        f.write(f"**Successful:** {len(results['success'])}\n\n")
        f.write(f"**Failed:** {len(results['failed'])}\n\n")
        f.write("---\n\n")
        
        if results['success']:
            f.write("## Successfully Downloaded\n\n")
            
            # Group by tier
            by_tier = {}
            for item in results['success']:
                tier = item['tier']
                if tier not in by_tier:
                    by_tier[tier] = []
                by_tier[tier].append(item)
            
            for tier in sorted(by_tier.keys()):
                f.write(f"### Tier {tier}\n\n")
                for item in by_tier[tier]:
                    f.write(f"- **{item['text']}** ({item['category']})\n")
                    f.write(f"  - URL: {item['url']}\n\n")
        
        if results['failed']:
            f.write("## Failed Downloads\n\n")
            for item in results['failed']:
                f.write(f"- **{item['text']}**\n")
                f.write(f"  - URL: {item['url']}\n")
                f.write(f"  - Error: {item['error']}\n\n")
    
    print(f"\n✓ Report saved: {report_file.name}")
    print(f"✓ Successfully downloaded: {len(results['success'])}/{len(urls)}")
    print(f"✓ Files saved to: {output_path}")
    
    if results['failed']:
        print(f"\n⚠ {len(results['failed'])} downloads failed - see report for details")

asyncio.run(download_corpus(
    urls_data='''$urlsJson''',
    output_dir=r'$outputDir',
    save_md=$(if($saveMarkdown){'True'}else{'False'}),
    save_html=$(if($saveHtml){'True'}else{'False'})
))
"@

$downloadScript | Out-File -FilePath "temp_corpus_download.py" -Encoding UTF8

Write-Host "Python script created successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "STARTING DOWNLOAD - This will take 30-60 minutes" -ForegroundColor Yellow
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Run the download
python temp_corpus_download.py

# Cleanup
Remove-Item "temp_corpus_download.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Corpus Download Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

$openFolder = Read-Host "Open output folder? (y/n)"
if ($openFolder -eq 'y') {
    Invoke-Item $outputDir
}
