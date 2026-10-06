# Interactive Website Downloader for Crawl4AI
# Auto-prompting script for easy website downloading

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Crawl4AI - Interactive Website Downloader" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Get the website URL
$url = Read-Host "Enter the website URL to download"

if ([string]::IsNullOrWhiteSpace($url)) {
    Write-Host "Error: URL cannot be empty" -ForegroundColor Red
    exit 1
}

# Validate URL format
if ($url -notmatch '^https?://') {
    Write-Host "Warning: URL should start with http:// or https://" -ForegroundColor Yellow
    $url = "https://$url"
    Write-Host "Using: $url" -ForegroundColor Green
}

Write-Host ""
Write-Host "Analyzing website..." -ForegroundColor Yellow

# Create a temporary Python script to analyze the site
$analyzeScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

async def analyze_site(url):
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)
        
        if not result.success:
            print(json.dumps({"error": "Failed to crawl the website"}))
            return
        
        # Parse links
        soup = BeautifulSoup(result.html, 'html.parser')
        links = []
        base_domain = urlparse(url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            link_domain = urlparse(full_url).netloc
            
            # Only include links from the same domain
            if link_domain == base_domain:
                links.append(full_url)
        
        # Remove duplicates
        unique_links = list(set(links))
        
        info = {
            "total_pages": len(unique_links),
            "links": unique_links[:50],  # First 50 for display
            "has_more": len(unique_links) > 50
        }
        
        print(json.dumps(info))

asyncio.run(analyze_site('$url'))
"@

$analyzeScript | Out-File -FilePath "temp_analyze.py" -Encoding UTF8

# Run the analysis
$analysisResult = python temp_analyze.py 2>&1 | Out-String
Remove-Item "temp_analyze.py" -ErrorAction SilentlyContinue

try {
    $siteInfo = $analysisResult | ConvertFrom-Json
    
    if ($siteInfo.error) {
        Write-Host "Error: $($siteInfo.error)" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Website Analysis:" -ForegroundColor Green
    Write-Host "  Found $($siteInfo.total_pages) internal pages" -ForegroundColor White
    
    if ($siteInfo.has_more) {
        Write-Host "  (Showing first 50 pages)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "Sample pages found:" -ForegroundColor Yellow
    $siteInfo.links[0..([Math]::Min(9, $siteInfo.links.Count - 1))] | ForEach-Object {
        Write-Host "  - $_" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "Note: Could not analyze page count. Will download the main page." -ForegroundColor Yellow
}

Write-Host ""
$downloadAll = Read-Host "Download all pages? (y/n, default: n)"

# Ask for output directory
Write-Host ""
$defaultDir = Join-Path (Get-Location) "crawl4ai_downloads"
$outputDir = Read-Host "Output directory (default: $defaultDir)"

if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

# Create output directory if it doesn't exist
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Created directory: $outputDir" -ForegroundColor Green
}

# Ask for format preference
Write-Host ""
Write-Host "Output format options:" -ForegroundColor Cyan
Write-Host "  1. Markdown only (clean, LLM-ready)" -ForegroundColor White
Write-Host "  2. Markdown + HTML backup" -ForegroundColor White
Write-Host "  3. HTML only" -ForegroundColor White

$formatChoice = Read-Host "Choose format (1-3, default: 1)"
if ([string]::IsNullOrWhiteSpace($formatChoice)) { $formatChoice = "1" }

$saveMarkdown = $formatChoice -in @("1", "2")
$saveHtml = $formatChoice -in @("2", "3")

Write-Host ""
Write-Host "Starting download..." -ForegroundColor Green
Write-Host ""

# Create the main download script
$downloadScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def sanitize_filename(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        path = 'index'
    
    # Replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', path)
    filename = filename.replace('/', '_')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

async def download_pages(url, output_dir, download_all, save_md, save_html):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        urls_to_download = [url]
        
        if download_all:
            print("Discovering all pages...")
            result = await crawler.arun(url=url)
            
            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')
                base_domain = urlparse(url).netloc
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    link_domain = urlparse(full_url).netloc
                    
                    if link_domain == base_domain:
                        urls_to_download.append(full_url)
                
                urls_to_download = list(set(urls_to_download))
                print(f"Found {len(urls_to_download)} pages to download")
        
        # Download each page
        for idx, page_url in enumerate(urls_to_download, 1):
            print(f"\n[{idx}/{len(urls_to_download)}] Downloading: {page_url}")
            
            result = await crawler.arun(url=page_url)
            
            if result.success:
                base_filename = sanitize_filename(page_url)
                
                if save_md:
                    md_file = output_path / f"{base_filename}.md"
                    md_file.write_text(result.markdown, encoding='utf-8')
                    print(f"  ✓ Saved markdown: {md_file.name}")
                
                if save_html:
                    html_file = output_path / f"{base_filename}.html"
                    html_file.write_text(result.html, encoding='utf-8')
                    print(f"  ✓ Saved HTML: {html_file.name}")
            else:
                print(f"  ✗ Failed to download {page_url}")
        
        print(f"\n✓ Download complete! Files saved to: {output_path}")

download_all = '$downloadAll'.lower() == 'y'
save_md = $saveMarkdown
save_html = $saveHtml

asyncio.run(download_pages('$url', r'$outputDir', download_all, save_md, save_html))
"@

$downloadScript | Out-File -FilePath "temp_download.py" -Encoding UTF8

# Run the download
python temp_download.py

# Cleanup
Remove-Item "temp_download.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Download process completed!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Files saved to: $outputDir" -ForegroundColor White
Write-Host ""

# Ask if user wants to open the folder
$openFolder = Read-Host "Open output folder? (y/n)"
if ($openFolder -eq 'y') {
    Invoke-Item $outputDir
}
