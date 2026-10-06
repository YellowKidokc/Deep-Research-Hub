# Philosophy Sites Downloader for Crawl4AI
# Pre-configured to download the philosophy sites to your specified folder

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Philosophy Sites Downloader" -ForegroundColor Cyan
Write-Host "   Pre-configured for World Views Research" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Pre-configured philosophy sites
$philosophySites = @(
    "Physicalism/Materialism - https://plato.stanford.edu/entries/physicalism/",
    "Idealism - https://plato.stanford.edu/entries/idealism/",
    "Dualism (Cartesian) - https://plato.stanford.edu/entries/dualism/",
    "Neutral Monism - https://plato.stanford.edu/entries/neutral-monism/",
    "Panpsychism - https://plato.stanford.edu/entries/panpsychism/",
    "Emergentism - https://plato.stanford.edu/entries/properties-emergent/",
    "Process Philosophy - https://plato.stanford.edu/entries/process-philosophy/",
    "Classical Theism - https://plato.stanford.edu/entries/classical-theism/",
    "Deism - https://plato.stanford.edu/entries/deism/",
    "Pantheism - https://plato.stanford.edu/entries/pantheism/",
    "Panentheism - https://plato.stanford.edu/entries/panentheism/",
    "Atheistic Naturalism - https://plato.stanford.edu/entries/naturalism/",
    "Nihilism - https://plato.stanford.edu/entries/nihilism/",
    "Existentialism - https://plato.stanford.edu/entries/existentialism/",
    "Determinism (Hard) - https://plato.stanford.edu/entries/determinism-causal/",
    "Eliminative Materialism - https://plato.stanford.edu/entries/materialism-eliminative/",
    "Functionalism - https://plato.stanford.edu/entries/functionalism/",
    "Epiphenomenalism - https://plato.stanford.edu/entries/epiphenomenalism/",
    "Buddhist Metaphysics - https://plato.stanford.edu/entries/buddha/",
    "Advaita Vedanta - https://plato.stanford.edu/entries/advaita-vedanta/"
)

Write-Host "📚 Pre-loaded Philosophy Sites:" -ForegroundColor Green
for ($i = 0; $i -lt $philosophySites.Count; $i++) {
    $number = "{0:D2}" -f ($i + 1)
    Write-Host "  $number. $($philosophySites[$i])" -ForegroundColor White
}

Write-Host ""
$outputDirDisplay = "O:\Theophysics_Master\TMSUB\GO FOLDER\00_Canonical\World Views"
Write-Host "🎯 Output Directory: $outputDirDisplay" -ForegroundColor Yellow
Write-Host ""

# Confirm before proceeding
$siteCount = $philosophySites.Count
$confirm = Read-Host "Download these $siteCount philosophy sites? (y/n, default: y)"
if ($confirm -eq 'n') {
    Write-Host "Download cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting philosophy sites download..." -ForegroundColor Green
Write-Host ""

# Use the smart batch downloader logic but pre-configured
$urls = $philosophySites
$inputMethod = "preloaded"  # Special flag for preloaded URLs

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

# Validate we have URLs to process
if ($parsedUrls.Count -eq 0) {
    Write-Host ""
    Write-Host "Error: No valid URLs found to process" -ForegroundColor Red
    exit 1
}

# Output directory setup
Write-Host ""
$outputDir = $outputDirDisplay

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "✓ Created directory: $outputDir" -ForegroundColor Green
} else {
    Write-Host "✓ Using existing directory: $outputDir" -ForegroundColor Green
}

# Pre-configured settings for philosophy research
$saveMarkdown = $true
$saveHtml = $true
$saveMetadata = $true
$extractLinks = "y"
$extractImages = "y"
$takeScreenshots = "n"
$maxConcurrency = "2"  # Conservative for philosophy sites
$delayBetween = "2"

Write-Host ""
Write-Host "Download Configuration:" -ForegroundColor Green
Write-Host "  URLs to process: $($parsedUrls.Count)" -ForegroundColor White
Write-Host "  Output directory: $outputDir" -ForegroundColor White
Write-Host "  Format: Markdown + HTML + Metadata" -ForegroundColor White
Write-Host "  Extract links: Yes" -ForegroundColor White
Write-Host "  Extract images: Yes" -ForegroundColor White
Write-Host "  Screenshots: No" -ForegroundColor White
Write-Host "  Concurrency: $maxConcurrency parallel downloads" -ForegroundColor White
Write-Host "  Delay: $delayBetween seconds between downloads" -ForegroundColor White

Write-Host ""
Write-Host "⚙️  Starting Python download process..." -ForegroundColor Yellow
Write-Host "   (This may take several minutes for all philosophy sites)" -ForegroundColor Gray
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
        # Clean label for filename - replace problematic characters
        safe_label = re.sub(r'[<>:"/\\\\|?*]', '_', label)
        safe_label = safe_label.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
    else:
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/')

        if not path or path == '/':
            safe_label = domain + '_index'
        else:
            safe_label = domain + '_' + path.replace('/', '_')

    # Replace any remaining invalid characters
    safe_label = re.sub(r'[<>:"/\\\\|?*]', '_', safe_label)

    # Limit length
    if len(safe_label) > 200:
        safe_label = safe_label[:200]

    return safe_label

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

    print(f"\\n🚀 Starting download of {total} philosophy sites")
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
                    result = await crawler.arun(url=url)

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
        if completed % 3 == 0 or completed == total:  # More frequent updates for philosophy sites
            print(f"\\n📊 Progress: {completed}/{total} completed ({successful} success, {failed} failed)")

    # Final summary
    print("\\n" + "="*80)
    print("🎉 PHILOSOPHY SITES DOWNLOAD COMPLETE!")
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

$downloadScript | Out-File -FilePath "temp_philosophy_download.py" -Encoding UTF8

# Run the download
python temp_philosophy_download.py

# Cleanup
Remove-Item "temp_philosophy_download.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "🎉 Philosophy Sites Download Completed!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Files saved to: $outputDir" -ForegroundColor White
Write-Host ""

# Show what was created
if (Test-Path $outputDir) {
    Write-Host "📊 Content Summary:" -ForegroundColor Cyan

    $mdFiles = Get-ChildItem $outputDir -Filter "*.md" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
    $htmlFiles = Get-ChildItem $outputDir -Filter "*.html" -Recurse | Measure-Object | Select-Object -ExpandProperty Count
    $jsonFiles = Get-ChildItem $outputDir -Filter "*.json" -Recurse | Measure-Object | Select-Object -ExpandProperty Count

    if ($mdFiles -gt 0) { Write-Host "   📄 $mdFiles Markdown files" -ForegroundColor White }
    if ($htmlFiles -gt 0) { Write-Host "   🌐 $htmlFiles HTML files" -ForegroundColor White }
    if ($jsonFiles -gt 0) { Write-Host "   📋 $jsonFiles metadata/link files" -ForegroundColor White }

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
Write-Host "💡 Philosophy Research Ready!" -ForegroundColor Cyan
Write-Host "   • Markdown files contain clean, readable content" -ForegroundColor White
Write-Host "   • HTML files preserve original formatting" -ForegroundColor White
Write-Host "   • Check metadata/ for download details" -ForegroundColor White
Write-Host "   • extracted_links/ contains all linked pages" -ForegroundColor White