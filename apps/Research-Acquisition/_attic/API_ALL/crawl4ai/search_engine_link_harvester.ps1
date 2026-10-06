# Link Harvester & Preview Tool
# Search multiple engines, preview links, then selectively download

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   Link Harvester & Preview Tool" -ForegroundColor Cyan
Write-Host "   Multi-Engine Search with Preview Before Download" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This tool helps you:" -ForegroundColor Yellow
Write-Host "  1. Search multiple engines (avoid IP bans)" -ForegroundColor White
Write-Host "  2. Harvest and preview links before downloading" -ForegroundColor White
Write-Host "  3. Select which links to actually crawl" -ForegroundColor White
Write-Host ""

# Search engine selection
Write-Host "Select search engines to use:" -ForegroundColor Cyan
Write-Host "  1. Google only" -ForegroundColor White
Write-Host "  2. Bing only" -ForegroundColor White
Write-Host "  3. SearXNG (privacy-focused, no tracking)" -ForegroundColor White
Write-Host "  4. Google + Bing (recommended for coverage)" -ForegroundColor White
Write-Host "  5. All engines (maximum coverage, slower)" -ForegroundColor White
Write-Host ""

$engineChoice = Read-Host "Choose engines (1-5, default: 4)"
if ([string]::IsNullOrWhiteSpace($engineChoice)) { $engineChoice = "4" }

$searchEngines = @()
switch ($engineChoice) {
    "1" { $searchEngines = @("google") }
    "2" { $searchEngines = @("bing") }
    "3" { $searchEngines = @("searxng") }
    "4" { $searchEngines = @("google", "bing") }
    "5" { $searchEngines = @("google", "bing", "searxng") }
    default { $searchEngines = @("google", "bing") }
}

Write-Host ""
Write-Host "Using search engines: $($searchEngines -join ', ')" -ForegroundColor Green
Write-Host ""

# Get search query
$searchQuery = Read-Host "Enter your search query"

if ([string]::IsNullOrWhiteSpace($searchQuery)) {
    Write-Host "Error: Search query cannot be empty" -ForegroundColor Red
    exit 1
}

# Advanced search options
Write-Host ""
Write-Host "Advanced Options:" -ForegroundColor Cyan
$maxResults = Read-Host "Maximum results per engine (default: 20)"
if ([string]::IsNullOrWhiteSpace($maxResults)) { $maxResults = "20" }

$includeFilters = Read-Host "Include only specific domains? (e.g., edu,org,gov - leave blank for all)"
$excludeFilters = Read-Host "Exclude domains? (e.g., youtube,facebook - leave blank for none)"

Write-Host ""
Write-Host "Harvesting links from search engines..." -ForegroundColor Green
Write-Host "This may take a minute..." -ForegroundColor Yellow
Write-Host ""

# Create the link harvesting script
$searchEnginesJson = $searchEngines | ConvertTo-Json -Compress
$harvestScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
import json
import re
from datetime import datetime

async def harvest_links(query, search_engines, max_results, include_filters, exclude_filters):
    all_links = []
    
    # Parse filters
    include_domains = [d.strip() for d in include_filters.split(',') if d.strip()] if include_filters else []
    exclude_domains = [d.strip() for d in exclude_filters.split(',') if d.strip()] if exclude_filters else []
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        
        for engine in search_engines:
            print(f"\n{'='*70}")
            print(f"Searching: {engine.upper()}")
            print('='*70)
            
            search_url = ""
            if engine == "google":
                search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            elif engine == "bing":
                search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={max_results}"
            elif engine == "searxng":
                # Using public SearXNG instance
                search_url = f"https://searx.be/search?q={quote_plus(query)}&categories=general&language=en"
            
            print(f"URL: {search_url}")
            
            try:
                result = await crawler.arun(url=search_url)
                
                if result.success:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    links_found = 0
                    
                    # Extract links based on search engine
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        # Clean up the URL
                        if engine == "google":
                            # Google wraps URLs in /url?q=
                            if '/url?q=' in href:
                                href = href.split('/url?q=')[1].split('&')[0]
                        elif engine == "bing":
                            # Bing uses direct links mostly
                            pass
                        elif engine == "searxng":
                            # SearXNG uses direct links
                            pass
                        
                        # Skip internal search engine links
                        if any(x in href.lower() for x in ['google.com', 'bing.com', 'searx', 'webcache', 'translate.google']):
                            continue
                        
                        # Must be a valid URL
                        if not href.startswith('http'):
                            continue
                        
                        # Parse domain
                        try:
                            domain = urlparse(href).netloc
                        except:
                            continue
                        
                        # Apply filters
                        if include_domains:
                            if not any(inc in domain for inc in include_domains):
                                continue
                        
                        if exclude_domains:
                            if any(exc in domain for exc in exclude_domains):
                                continue
                        
                        # Get link text
                        link_text = link.get_text(strip=True)
                        
                        # Add to results
                        link_data = {
                            'url': href,
                            'title': link_text[:100] if link_text else 'No title',
                            'domain': domain,
                            'source_engine': engine
                        }
                        
                        # Check if already added
                        if not any(l['url'] == href for l in all_links):
                            all_links.append(link_data)
                            links_found += 1
                    
                    print(f"Found {links_found} unique links from {engine}")
                else:
                    print(f"Failed to search {engine}")
                    
            except Exception as e:
                print(f"Error searching {engine}: {str(e)}")
        
        print(f"\n{'='*70}")
        print(f"TOTAL UNIQUE LINKS FOUND: {len(all_links)}")
        print('='*70)
        
        # Save to CSV for easy Excel editing
        import csv
        output_file = f"harvested_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header row
            writer.writerow(['Search_Term', 'Link', 'Title', 'Domain', 'Search_Engine', 'Downloaded', 'Notes'])
            
            # Data rows
            for link in all_links:
                writer.writerow([
                    query,
                    link['url'],
                    link['title'],
                    link['domain'],
                    link['source_engine'],
                    'No',  # Downloaded status - user can change to Yes
                    ''     # Empty notes column for user
                ])
        
        print(f"\nLinks saved to: {output_file}")
        
        # Display preview
        print(f"\n{'='*70}")
        print("LINK PREVIEW (First 30)")
        print('='*70)
        
        for idx, link in enumerate(all_links[:30], 1):
            print(f"\n{idx}. {link['title']}")
            print(f"   URL: {link['url']}")
            print(f"   Domain: {link['domain']}")
            print(f"   Source: {link['source_engine']}")
        
        if len(all_links) > 30:
            print(f"\n... and {len(all_links) - 30} more links")
        
        return output_file

search_engines = json.loads('$searchEnginesJson')
output_file = asyncio.run(harvest_links(
    query='$searchQuery',
    search_engines=search_engines,
    max_results=$maxResults,
    include_filters='$includeFilters',
    exclude_filters='$excludeFilters'
))

print(f"\n{'='*70}")
print("NEXT STEPS")
print('='*70)
print(f"1. Review the links in: {output_file}")
print("2. Open in Excel and delete unwanted rows")
print("3. Run the download script to crawl remaining links")
print("4. Script will update 'Downloaded' column to 'Yes' after crawling")
print('='*70)
"@

$harvestScript | Out-File -FilePath "temp_harvest.py" -Encoding UTF8

# Run the harvesting
python temp_harvest.py

# Cleanup
Remove-Item "temp_harvest.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Link Harvesting Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

# Find the generated CSV file
$csvFiles = Get-ChildItem -Filter "harvested_links_*.csv" | Sort-Object LastWriteTime -Descending
if ($csvFiles.Count -eq 0) {
    Write-Host "No links file found. Exiting." -ForegroundColor Red
    exit 1
}

$linksFile = $csvFiles[0].FullName
Write-Host "Links saved to: $linksFile" -ForegroundColor White
Write-Host ""

# Ask user what to do next
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "  1. Open in Excel (recommended - easy editing)" -ForegroundColor White
Write-Host "  2. Download ALL links now (no filtering)" -ForegroundColor White
Write-Host "  3. Exit (review manually later)" -ForegroundColor White
Write-Host ""

$nextAction = Read-Host "Choose action (1-3, default: 1)"
if ([string]::IsNullOrWhiteSpace($nextAction)) { $nextAction = "1" }

if ($nextAction -eq "1") {
    Write-Host ""
    Write-Host "Opening CSV in Excel..." -ForegroundColor Green
    Write-Host "Delete unwanted rows, then save and close Excel." -ForegroundColor Yellow
    Write-Host "The 'Downloaded' and 'Notes' columns are for your tracking." -ForegroundColor Yellow
    Write-Host ""
    
    Start-Process $linksFile
    
    Write-Host ""
    $proceed = Read-Host "Ready to download the edited links? (y/n)"
    if ($proceed -ne 'y') {
        Write-Host "Exiting. Run this script again when ready." -ForegroundColor Yellow
        exit 0
    }
    
    $nextAction = "2"
}

if ($nextAction -eq "2") {
    Write-Host ""
    Write-Host "Starting download of selected links..." -ForegroundColor Green
    Write-Host ""
    
    # Output options
    $defaultDir = Join-Path (Get-Location) "harvested_downloads"
    $outputDir = Read-Host "Output directory (default: $defaultDir)"
    if ([string]::IsNullOrWhiteSpace($outputDir)) {
        $outputDir = $defaultDir
    }
    
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    Write-Host ""
    Write-Host "Output format:" -ForegroundColor Cyan
    Write-Host "  1. Markdown only" -ForegroundColor White
    Write-Host "  2. Markdown + HTML" -ForegroundColor White
    Write-Host "  3. HTML only" -ForegroundColor White
    
    $formatChoice = Read-Host "Choose format (1-3, default: 1)"
    if ([string]::IsNullOrWhiteSpace($formatChoice)) { $formatChoice = "1" }
    
    $saveMarkdown = $formatChoice -in @("1", "2")
    $saveHtml = $formatChoice -in @("2", "3")
    
    # Create download script
    $downloadScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import csv
import re
from urllib.parse import urlparse

def sanitize_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/')
    
    if not path:
        filename = domain + '_index'
    else:
        filename = domain + '_' + path
    
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.replace('/', '_')
    
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

async def download_links(links_file, output_dir, save_md, save_html):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load links from CSV
    links = []
    with open(links_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            links.append(row)
    
    print(f"Loaded {len(links)} links to download")
    print()
    
    # Track download status
    updated_rows = []
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for idx, link_data in enumerate(links, 1):
            url = link_data['Link']
            
            print(f"\n{'='*70}")
            print(f"[{idx}/{len(links)}] Downloading: {url}")
            print('='*70)
            
            try:
                result = await crawler.arun(url=url)
                
                if result.success:
                    base_filename = sanitize_filename(url)
                    
                    if save_md:
                        md_file = output_path / f"{base_filename}.md"
                        
                        # Add metadata header
                        metadata = f"# {link_data.get('Title', 'Untitled')}\n\n"
                        metadata += f"**URL:** {url}\n\n"
                        metadata += f"**Domain:** {link_data.get('Domain', 'unknown')}\n\n"
                        metadata += f"**Source Engine:** {link_data.get('Search_Engine', 'unknown')}\n\n"
                        metadata += f"**Search Term:** {link_data.get('Search_Term', 'unknown')}\n\n"
                        metadata += "---\n\n"
                        
                        md_file.write_text(metadata + result.markdown, encoding='utf-8')
                        print(f"  ✓ Saved markdown: {md_file.name}")
                    
                    if save_html:
                        html_file = output_path / f"{base_filename}.html"
                        html_file.write_text(result.html, encoding='utf-8')
                        print(f"  ✓ Saved HTML: {html_file.name}")
                    
                    # Update status
                    link_data['Downloaded'] = 'Yes'
                else:
                    print(f"  ✗ Failed: {result.error_message or 'Unknown error'}")
                    link_data['Downloaded'] = 'Failed'
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                link_data['Downloaded'] = 'Error'
            
            updated_rows.append(link_data)
    
    # Save updated CSV with download status
    with open(links_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Search_Term', 'Link', 'Title', 'Domain', 'Search_Engine', 'Downloaded', 'Notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
    
    print(f"\n{'='*70}")
    print("DOWNLOAD COMPLETE!")
    print('='*70)
    print(f"Files saved to: {output_path}")
    print(f"CSV updated with download status: {links_file}")

asyncio.run(download_links(
    links_file=r'$linksFile',
    output_dir=r'$outputDir',
    save_md=$saveMarkdown,
    save_html=$saveHtml
))
"@

    $downloadScript | Out-File -FilePath "temp_download_links.py" -Encoding UTF8
    python temp_download_links.py
    Remove-Item "temp_download_links.py" -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host "All downloads complete!" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $openFolder = Read-Host "Open output folder? (y/n)"
    if ($openFolder -eq 'y') {
        Invoke-Item $outputDir
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
