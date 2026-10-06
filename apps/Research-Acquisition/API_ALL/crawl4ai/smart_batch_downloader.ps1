# Enhanced Batch Link Downloader for Crawl4AI
# Download multiple URLs with smart parsing, progress tracking, and content identification

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Crawl4AI - Enhanced Batch Link Downloader" -ForegroundColor Cyan
Write-Host "   Smart URL parsing • Progress tracking • Content identification" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "How would you like to provide URLs?" -ForegroundColor Yellow
Write-Host "  1. Paste URLs now (supports 'Name – URL' format, one per line)" -ForegroundColor White
Write-Host "  2. Load from a text file (supports various formats)" -ForegroundColor White
Write-Host "  3. Paste philosophy/religion links (like your Stanford example)" -ForegroundColor White
Write-Host ""

$inputMethod = Read-Host "Choose method (1-3, default: 1)"
if ([string]::IsNullOrWhiteSpace($inputMethod)) { $inputMethod = "1" }

$urls = @()
$urlLabels = @{}  # Store human-readable labels for URLs

if ($inputMethod -eq "1" -or $inputMethod -eq "3") {
    if ($inputMethod -eq "3") {
        Write-Host ""
        Write-Host "Paste your philosophy/religion links in format:" -ForegroundColor Green
        Write-Host "  Topic Name – https://url" -ForegroundColor Gray
        Write-Host "  (The '–' can be dash, hyphen, or em-dash)" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "Paste your URLs or 'Name – URL' pairs (one per line):" -ForegroundColor Green
        Write-Host "  Examples:" -ForegroundColor Gray
        Write-Host "    https://example.com" -ForegroundColor Gray
        Write-Host "    My Site – https://example.com" -ForegroundColor Gray
        Write-Host ""
    }

    Write-Host "Press Enter on empty line when finished:" -ForegroundColor Yellow
    Write-Host ""

    while ($true) {
        $line = Read-Host
        if ([string]::IsNullOrWhiteSpace($line)) {
            break
        }
        $urls += $line.Trim()
    }
} elseif ($inputMethod -eq "2") {
    $filePath = Read-Host "Enter the path to your text file"

    if (Test-Path $filePath) {
        $urls = Get-Content $filePath | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() }
    } else {
        Write-Host "Error: File not found: $filePath" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Invalid choice. Using method 1." -ForegroundColor Yellow
    $inputMethod = "1"
}

# Smart URL parsing with label extraction
$parsedUrls = @()
$skippedLines = @()

foreach ($line in $urls) {
    # Skip comments and empty lines
    if ($line -match '^\s*#' -or [string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $url = $line
    $label = ""

    # Check for "Name – URL" format (various dash types)
    if ($line -match '^\s*(.+?)\s*[-–—]\s*(.+?)\s*$') {
        $label = $matches[1].Trim()
        $url = $matches[2].Trim()
    }

    # Flexible URL validation and correction
    $originalUrl = $url

    # Handle common typos in https/http
    if ($url -match '^ttps?://' -or $url -match '^ttps://') {
        # Missing 'h' - add it
        $url = "h$url"
    } elseif ($url -match '^h?ttps?://') {
        # Handle variations like 'htps://' -> 'https://'
        $url = $url -replace '^h?ttp', 'http'
        if ($url -notmatch '^https://') {
            $url = $url -replace '^http://', 'https://'
        }
    } elseif ($url -notmatch '^https?://') {
        # No protocol at all - add https://
        $url = "https://$url"
    }

    # Basic URL validation
    try {
        $uri = [System.Uri]$url
        if ($uri.Host -and $uri.Scheme) {
            $parsedUrls += @{
                Url = $url
                Label = $label
                OriginalLine = $line
            }

            if ($label) {
                $urlLabels[$url] = $label
            }
        } else {
            throw "Invalid URL structure"
        }
    } catch {
        $skippedLines += "INVALID: $line (could not parse as URL)"
        continue
    }
}

# Show parsing results
Write-Host ""
Write-Host "URL Parsing Results:" -ForegroundColor Cyan
Write-Host "  Found $($parsedUrls.Count) valid URLs" -ForegroundColor Green

if ($skippedLines.Count -gt 0) {
    Write-Host "  Skipped $($skippedLines.Count) invalid lines:" -ForegroundColor Yellow
    $skippedLines | ForEach-Object { Write-Host "    ✗ $_" -ForegroundColor Red }
}

Write-Host ""
Write-Host "Parsed URLs:" -ForegroundColor Green
for ($i = 0; $i -lt $parsedUrls.Count; $i++) {
    $item = $parsedUrls[$i]
    $number = "{0:D2}" -f ($i + 1)
    if ($item.Label) {
        Write-Host "  $number. $($item.Label)" -ForegroundColor White
        Write-Host "      $($item.Url)" -ForegroundColor Gray
    } else {
        Write-Host "  $number. $($item.Url)" -ForegroundColor White
    }
}

if ($validUrls.Count -eq 0) {
    Write-Host "Error: No valid URLs found" -ForegroundColor Red
    exit 1
}

# Validate we have URLs to process
if ($parsedUrls.Count -eq 0) {
    Write-Host ""
    Write-Host "Error: No valid URLs found to process" -ForegroundColor Red
    exit 1
}

# Output directory setup
Write-Host ""
$defaultDir = Join-Path (Get-Location) "crawl4ai_batch_downloads_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$suggestedName = Read-Host "Custom folder name (press Enter for timestamped folder)"

if (-not [string]::IsNullOrWhiteSpace($suggestedName)) {
    $defaultDir = Join-Path (Get-Location) "crawl4ai_$suggestedName"
}

$outputDir = Read-Host "Output directory (default: $(Split-Path $defaultDir -Leaf))"

if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

# Resolve relative paths
if (-not [System.IO.Path]::IsPathRooted($outputDir)) {
    $outputDir = Join-Path (Get-Location) $outputDir
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "✓ Created directory: $outputDir" -ForegroundColor Green
} else {
    Write-Host "✓ Using existing directory: $outputDir" -ForegroundColor Green
}

# Content identification and format options
Write-Host ""
Write-Host "Content Processing Options:" -ForegroundColor Cyan
Write-Host "  1. Markdown only (clean, LLM-ready, fast)" -ForegroundColor White
Write-Host "  2. Markdown + HTML backup (recommended)" -ForegroundColor White
Write-Host "  3. HTML only (preserves original formatting)" -ForegroundColor White
Write-Host "  4. Full extraction (Markdown + HTML + metadata)" -ForegroundColor White

$formatChoice = Read-Host "Choose format (1-4, default: 2)"
if ([string]::IsNullOrWhiteSpace($formatChoice)) { $formatChoice = "2" }

$saveMarkdown = $formatChoice -in @("1", "2", "4")
$saveHtml = $formatChoice -in @("2", "3", "4")
$saveMetadata = $formatChoice -eq "4"

# Additional extraction options
Write-Host ""
Write-Host "Additional Content Extraction:" -ForegroundColor Cyan
$extractLinks = Read-Host "Extract all links from each page? (y/n, default: y)"
if ([string]::IsNullOrWhiteSpace($extractLinks)) { $extractLinks = "y" }

$extractImages = Read-Host "Extract image references? (y/n, default: n)"
if ([string]::IsNullOrWhiteSpace($extractImages)) { $extractImages = "n" }

$takeScreenshots = Read-Host "Take screenshots of each page? (y/n, default: n)"
if ([string]::IsNullOrWhiteSpace($takeScreenshots)) { $takeScreenshots = "n" }

# Processing options
Write-Host ""
Write-Host "Processing Options:" -ForegroundColor Cyan
$maxConcurrency = Read-Host "Max concurrent downloads (1-5, default: 3)"
if ([string]::IsNullOrWhiteSpace($maxConcurrency)) { $maxConcurrency = "3" }
$maxConcurrency = [math]::Max(1, [math]::Min(5, [int]$maxConcurrency))

$delayBetween = Read-Host "Delay between downloads in seconds (0-5, default: 1)"
if ([string]::IsNullOrWhiteSpace($delayBetween)) { $delayBetween = "1" }
$delayBetween = [math]::Max(0, [math]::Min(5, [int]$delayBetween))

Write-Host ""
Write-Host "Download Configuration Summary:" -ForegroundColor Green
Write-Host "  URLs to process: $($parsedUrls.Count)" -ForegroundColor White
Write-Host "  Output directory: $(Split-Path $outputDir -Leaf)" -ForegroundColor White
Write-Host "  Format: $(if ($saveMarkdown) {'Markdown'} else {''}) $(if ($saveHtml) {'HTML'} else {''}) $(if ($saveMetadata) {'Metadata'} else {''})".Trim() -ForegroundColor White
Write-Host "  Extract links: $(if ($extractLinks -eq 'y') {'Yes'} else {'No'})" -ForegroundColor White
Write-Host "  Extract images: $(if ($extractImages -eq 'y') {'Yes'} else {'No'})" -ForegroundColor White
Write-Host "  Screenshots: $(if ($takeScreenshots -eq 'y') {'Yes'} else {'No'})" -ForegroundColor White
Write-Host "  Concurrency: $maxConcurrency parallel downloads" -ForegroundColor White
Write-Host "  Delay: $delayBetween seconds between downloads" -ForegroundColor White

Write-Host ""
$confirm = Read-Host "Start download? (y/n, default: y)"
if ($confirm -eq 'n') {
    Write-Host "Download cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting enhanced batch download..." -ForegroundColor Green
Write-Host ""

# Prepare data for Python script
$urlsData = $parsedUrls | ForEach-Object {
    @{
        url = $_.Url
        label = $_.Label
        original_line = $_.OriginalLine
    }
}
$urlsJson = $urlsData | ConvertTo-Json -Compress

# Create the enhanced download script
$downloadScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import re
import json
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from datetime import datetime
import time

def sanitize_filename(url, label=""):
    parsed = urlparse(url)

    # Use label if available, otherwise domain + path
    if label:
        # Clean label for filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', label)
        filename = filename.replace(' ', '_').replace('/', '_')
    else:
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/')

        if not path or path == '/':
            filename = domain + '_index'
        else:
            filename = domain + '_' + path.replace('/', '_')

    # Replace any remaining invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Limit length
    if len(filename) > 200:
        filename = filename[:200]

    return filename

def extract_image_info(soup, base_url):
    """Extract image information from the page"""
    images = []
    for img in soup.find_all('img', src=True):
        src = img['src']
        full_url = urljoin(base_url, src)
        alt = img.get('alt', '')
        title = img.get('title', '')

        images.append({
            'url': full_url,
            'alt': alt,
            'title': title,
            'original_src': src
        })

    return images

async def download_batch(urls_data, output_dir, save_md, save_html, save_metadata, extract_links, extract_images, take_screenshots, max_concurrency, delay_between):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    if extract_links:
        links_dir = output_path / 'extracted_links'
        links_dir.mkdir(exist_ok=True)

    if extract_images:
        images_dir = output_path / 'extracted_images'
        images_dir.mkdir(exist_ok=True)

    if take_screenshots:
        screenshots_dir = output_path / 'screenshots'
        screenshots_dir.mkdir(exist_ok=True)

    if save_metadata:
        metadata_dir = output_path / 'metadata'
        metadata_dir.mkdir(exist_ok=True)

    # Progress tracking
    total = len(urls_data)
    successful = 0
    failed = 0

    print(f"\\n🚀 Starting download of {total} URLs")
    print(f"📁 Output directory: {output_path}")
    print(f"⚡ Max concurrency: {max_concurrency}")
    print(f"⏱️  Delay between downloads: {delay_between}s")
    print("="*80)

    # Semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_concurrency)

    async def download_single(item, idx):
        async with semaphore:
            url = item['url']
            label = item.get('label', '')
            original_line = item.get('original_line', '')

            print(f"\\n[{idx:2d}/{total}] {'💡' if label else '🔗'} {label or url}")
            if label:
                print(f"           URL: {url}")

            try:
                async with AsyncWebCrawler(verbose=False) as crawler:
                    result = await crawler.arun(
                        url=url,
                        screenshot=take_screenshots
                    )

                if result.success:
                    nonlocal successful
                    successful += 1

                    base_filename = sanitize_filename(url, label)
                    content_size = len(result.markdown) if result.markdown else 0

                    print(f"           ✓ Downloaded ({content_size:,} chars)")

                    # Save markdown
                    if save_md:
                        md_file = output_path / f"{base_filename}.md"

                        # Add header with metadata
                        header = f"---\\n"
                        header += f"URL: {url}\\n"
                        if label:
                            header += f"Label: {label}\\n"
                        header += f"Downloaded: {datetime.now().isoformat()}\\n"
                        header += f"Content-Length: {content_size}\\n"
                        header += f"---\\n\\n"

                        md_file.write_text(header + result.markdown, encoding='utf-8')
                        print(f"           📄 Markdown: {md_file.name}")

                    # Save HTML
                    if save_html:
                        html_file = output_path / f"{base_filename}.html"
                        html_file.write_text(result.html, encoding='utf-8')
                        print(f"           🌐 HTML: {html_file.name}")

                    # Extract and save links
                    if extract_links:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        links = []

                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(url, href)
                            link_text = link.get_text(strip=True)
                            links.append({
                                'url': full_url,
                                'text': link_text[:100] if link_text else '',
                                'original_href': href
                            })

                        links_file = links_dir / f"{base_filename}_links.json"
                        links_file.write_text(json.dumps(links, indent=2, ensure_ascii=False), encoding='utf-8')
                        print(f"           🔗 Links extracted: {len(links)}")

                    # Extract and save image info
                    if extract_images:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        images = extract_image_info(soup, url)

                        images_file = images_dir / f"{base_filename}_images.json"
                        images_file.write_text(json.dumps(images, indent=2, ensure_ascii=False), encoding='utf-8')
                        print(f"           🖼️  Images found: {len(images)}")

                    # Save screenshot
                    if take_screenshots and result.screenshot:
                        screenshot_file = screenshots_dir / f"{base_filename}.png"
                        screenshot_file.write_bytes(result.screenshot)
                        print(f"           📸 Screenshot: {screenshot_file.name}")

                    # Save metadata
                    if save_metadata:
                        metadata = {
                            'url': url,
                            'label': label,
                            'original_line': original_line,
                            'downloaded_at': datetime.now().isoformat(),
                            'content_length': content_size,
                            'markdown_saved': save_md,
                            'html_saved': save_html,
                            'links_extracted': len(links) if extract_links else 0,
                            'images_found': len(images) if extract_images else 0,
                            'screenshot_taken': take_screenshots and result.screenshot is not None
                        }

                        metadata_file = metadata_dir / f"{base_filename}_metadata.json"
                        metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
                        print(f"           📋 Metadata: {metadata_file.name}")

                else:
                    nonlocal failed
                    failed += 1
                    print(f"           ✗ Failed: {result.error_message or 'Unknown error'}")

            except Exception as e:
                nonlocal failed
                failed += 1
                print(f"           ✗ Error: {str(e)}")

            # Delay between downloads
            if delay_between > 0:
                await asyncio.sleep(delay_between)

    # Create download tasks
    tasks = []
    for idx, item in enumerate(urls_data, 1):
        task = download_single(item, idx)
        tasks.append(task)

    # Execute with progress tracking
    completed = 0
    for coro in asyncio.as_completed(tasks):
        await coro
        completed += 1
        if completed % 5 == 0 or completed == total:
            print(f"\\n📊 Progress: {completed}/{total} completed ({successful} success, {failed} failed)")

    # Final summary
    print("\\n" + "="*80)
    print("🎉 BATCH DOWNLOAD COMPLETE!")
    print("="*80)
    print(f"📁 Files saved to: {output_path}")
    print(f"✅ Successful downloads: {successful}")
    print(f"❌ Failed downloads: {failed}")
    print(f"📊 Total processed: {total}")
    print(f"📈 Success rate: {(successful/total*100):.1f}%" if total > 0 else "No URLs processed")

    # Show directory contents
    print("\\n📂 Directory contents:")
    try:
        items = list(output_path.rglob("*"))
        dirs = [p for p in items if p.is_dir()]
        files = [p for p in items if p.is_file()]

        if dirs:
            print(f"   📁 {len(dirs)} directories:")
            for d in sorted(dirs):
                rel_path = d.relative_to(output_path)
                print(f"      {rel_path}/")

        if files:
            print(f"   📄 {len(files)} files:")
            # Group by extension
            ext_groups = {}
            for f in files:
                ext = f.suffix.lower() if f.suffix else 'no_ext'
                ext_groups[ext] = ext_groups.get(ext, 0) + 1

            for ext, count in sorted(ext_groups.items()):
                ext_name = ext if ext != 'no_ext' else '(no extension)'
                print(f"      {count} {ext_name} files")

    except Exception as e:
        print(f"   Could not list directory contents: {e}")

    print("="*80)

urls_data = json.loads('$urlsJson')
save_md = $saveMarkdown
save_html = $saveHtml
save_metadata = $saveMetadata
extract_links = '$extractLinks'.lower() == 'y'
extract_images = '$extractImages'.lower() == 'y'
take_screenshots = '$takeScreenshots'.lower() == 'y'
max_concurrency = $maxConcurrency
delay_between = $delayBetween

asyncio.run(download_batch(urls_data, r'$outputDir', save_md, save_html, save_metadata, extract_links, extract_images, take_screenshots, max_concurrency, delay_between))
"@

$downloadScript | Out-File -FilePath "temp_enhanced_batch_download.py" -Encoding UTF8

Write-Host ""
Write-Host "⚙️  Starting Python download process..." -ForegroundColor Yellow
Write-Host "   (This may take a while depending on URL count and content size)" -ForegroundColor Gray
Write-Host ""

# Run the download
$startTime = Get-Date
python temp_enhanced_batch_download.py
$endTime = Get-Date
$duration = $endTime - $startTime

# Cleanup
Remove-Item "temp_enhanced_batch_download.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎉 Enhanced Batch Download Completed!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Files saved to: $outputDir" -ForegroundColor White
Write-Host "⏱️  Total time: $([math]::Round($duration.TotalMinutes, 1)) minutes" -ForegroundColor White
Write-Host ""

# Show what was created
if (Test-Path $outputDir) {
    Write-Host "📊 Content Summary:" -ForegroundColor Cyan

    $mdFiles = Get-ChildItem $outputDir -Filter "*.md" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
    $htmlFiles = Get-ChildItem $outputDir -Filter "*.html" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
    $jsonFiles = Get-ChildItem $outputDir -Filter "*.json" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
    $pngFiles = Get-ChildItem $outputDir -Filter "*.png" -Recurse | Measure-Object | Select-Object -ExpandProperty Count

    if ($mdFiles -gt 0) { Write-Host "   📄 $mdFiles Markdown files" -ForegroundColor White }
    if ($htmlFiles -gt 0) { Write-Host "   🌐 $htmlFiles HTML files" -ForegroundColor White }
    if ($jsonFiles -gt 0) { Write-Host "   📋 $jsonFiles metadata/link files" -ForegroundColor White }
    if ($pngFiles -gt 0) { Write-Host "   📸 $pngFiles screenshots" -ForegroundColor White }

    # Show subdirectories
    $subdirs = Get-ChildItem $outputDir -Directory
    if ($subdirs.Count -gt 0) {
        Write-Host "   📁 Subdirectories:" -ForegroundColor Gray
        foreach ($dir in $subdirs) {
            $fileCount = Get-ChildItem $dir.FullName -File -Recurse | Measure-Object | Select-Object -ExpandProperty Count
            Write-Host "      $($dir.Name)/ ($fileCount files)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
$openFolder = Read-Host "Open output folder in Explorer? (y/n, default: y)"
if ([string]::IsNullOrWhiteSpace($openFolder) -or $openFolder -eq 'y') {
    Invoke-Item $outputDir
}

Write-Host ""
Write-Host "💡 Tip: Check the 'metadata' folder for download details if you enabled full extraction" -ForegroundColor Cyan
