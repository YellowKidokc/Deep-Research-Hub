# Simplified Biblical Mathematics Researcher
# Direct approach - crawls known academic sources without search engines

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   Biblical Mathematics - Direct Crawler" -ForegroundColor Cyan
Write-Host "   (Simplified - No Search Engines)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This tool crawls KNOWN academic sources directly." -ForegroundColor Yellow
Write-Host "No search engines = No IP bans = Actual content" -ForegroundColor Green
Write-Host ""

# Predefined high-quality sources
Write-Host "Select topic:" -ForegroundColor Cyan
Write-Host "  1. Resurrection - Mathematical Analysis" -ForegroundColor White
Write-Host "  2. Prophecy Fulfillment - Statistical Probability" -ForegroundColor White
Write-Host "  3. Miracles - Bayesian Analysis" -ForegroundColor White
Write-Host "  4. All Topics (comprehensive)" -ForegroundColor White
Write-Host ""

$topicChoice = Read-Host "Choose topic (1-4, default: 4)"
if ([string]::IsNullOrWhiteSpace($topicChoice)) { $topicChoice = "4" }

$urls = @()
$topicName = ""

switch ($topicChoice) {
    "1" {
        $urls = @(
            "https://www.reasonablefaith.org/writings/scholarly-writings/historical-jesus/the-resurrection-of-jesus/",
            "https://www.bethinking.org/is-christianity-true/the-resurrection-of-jesus",
            "https://www.str.org/w/the-resurrection-of-jesus-a-rational-inquiry",
            "https://www.bethinking.org/did-jesus-rise-from-the-dead",
            "https://www.reasonablefaith.org/writings/popular-writings/jesus-of-nazareth/the-resurrection-of-jesus/"
        )
        $topicName = "Resurrection_Mathematics"
    }
    "2" {
        $urls = @(
            "https://www.reasonablefaith.org/writings/popular-writings/jesus-of-nazareth/prophecies-of-the-messiah/",
            "https://www.bethinking.org/is-the-bible-reliable/old-testament-prophecies-of-jesus",
            "https://www.str.org/w/messianic-prophecies",
            "https://www.carm.org/about-jesus/prophecies-fulfilled-by-jesus/"
        )
        $topicName = "Prophecy_Probability"
    }
    "3" {
        $urls = @(
            "https://plato.stanford.edu/entries/miracles/",
            "https://www.bethinking.org/is-christianity-true/are-miracles-possible",
            "https://www.str.org/w/the-case-for-miracles",
            "https://www.reasonablefaith.org/writings/scholarly-writings/divine-action-and-natural-law/the-problem-of-miracles-a-historical-and-philosophical-perspective/"
        )
        $topicName = "Miracles_Analysis"
    }
    "4" {
        $urls = @(
            # Resurrection
            "https://www.reasonablefaith.org/writings/scholarly-writings/historical-jesus/the-resurrection-of-jesus/",
            "https://www.bethinking.org/is-christianity-true/the-resurrection-of-jesus",
            "https://www.str.org/w/the-resurrection-of-jesus-a-rational-inquiry",
            # Prophecy
            "https://www.reasonablefaith.org/writings/popular-writings/jesus-of-nazareth/prophecies-of-the-messiah/",
            "https://www.bethinking.org/is-the-bible-reliable/old-testament-prophecies-of-jesus",
            "https://www.str.org/w/messianic-prophecies",
            # Miracles
            "https://plato.stanford.edu/entries/miracles/",
            "https://www.bethinking.org/is-christianity-true/are-miracles-possible",
            # General apologetics
            "https://www.reasonablefaith.org/writings/scholarly-writings/",
            "https://www.str.org/articles",
            "https://www.bethinking.org/is-christianity-true"
        )
        $topicName = "Comprehensive_Biblical_Mathematics"
    }
    default {
        $urls = @(
            "https://www.reasonablefaith.org/writings/scholarly-writings/",
            "https://www.bethinking.org/is-christianity-true"
        )
        $topicName = "Biblical_Mathematics"
    }
}

Write-Host ""
Write-Host "Will crawl $($urls.Count) academic sources" -ForegroundColor Green
Write-Host ""

$defaultDir = Join-Path (Get-Location) "biblical_math_results"
$outputDir = Read-Host "Output directory (default: $defaultDir)"
if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Write-Host ""
Write-Host "Starting direct crawl of academic sources..." -ForegroundColor Green
Write-Host ""

# Create simplified crawler script
$urlsJson = $urls | ConvertTo-Json -Compress
$crawlScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import re
from urllib.parse import urlparse
from datetime import datetime

def sanitize_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/').replace('/', '_')
    
    if not path:
        filename = domain + '_index'
    else:
        filename = domain + '_' + path[:100]
    
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return filename

async def crawl_sources(urls, output_dir, topic_name):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    print("="*70)
    print(f"CRAWLING {len(urls)} ACADEMIC SOURCES")
    print("="*70)
    print()
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] Crawling: {url}")
            print("-"*70)
            
            try:
                result = await crawler.arun(url=url)
                
                if result.success:
                    content = result.markdown
                    
                    # Score for mathematical content
                    math_keywords = [
                        'probability', 'statistical', 'mathematics', 'calculation',
                        'equation', 'formula', 'quantitative', 'numerical',
                        'analysis', 'odds', 'percentage', 'ratio', 'theorem',
                        'proof', 'evidence', 'scientific', 'empirical',
                        'bayesian', 'likelihood', 'inference'
                    ]
                    
                    content_lower = content.lower()
                    math_score = sum(1 for keyword in math_keywords if keyword in content_lower)
                    
                    print(f"  Math Content Score: {math_score}/20")
                    
                    if math_score >= 2:  # At least some mathematical content
                        # Save individual file
                        filename = sanitize_filename(url)
                        md_file = output_path / f"{filename}.md"
                        
                        # Add header
                        header = f"# {result.title or 'Untitled'}\n\n"
                        header += f"**URL:** {url}\n\n"
                        header += f"**Math Score:** {math_score}/20\n\n"
                        header += f"**Crawled:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        header += "---\n\n"
                        
                        md_file.write_text(header + content, encoding='utf-8')
                        
                        results.append({
                            'url': url,
                            'title': result.title or 'Untitled',
                            'math_score': math_score,
                            'filename': md_file.name
                        })
                        
                        print(f"  ✓ Saved: {md_file.name}")
                    else:
                        print(f"  ✗ Skipped (low math content)")
                else:
                    print(f"  ✗ Failed to crawl")
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
    
    # Create master report
    print()
    print("="*70)
    print("CREATING MASTER REPORT")
    print("="*70)
    
    if results:
        report_file = output_path / f"{topic_name}_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Biblical Mathematics Research: {topic_name}\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Sources Crawled:** {len(urls)}\n\n")
            f.write(f"**Sources with Math Content:** {len(results)}\n\n")
            f.write("---\n\n")
            
            f.write("## Sources Found\n\n")
            
            # Sort by math score
            results.sort(key=lambda x: x['math_score'], reverse=True)
            
            for idx, res in enumerate(results, 1):
                f.write(f"### {idx}. {res['title']}\n\n")
                f.write(f"**URL:** {res['url']}\n\n")
                f.write(f"**Math Score:** {res['math_score']}/20\n\n")
                f.write(f"**File:** {res['filename']}\n\n")
                f.write("---\n\n")
        
        print(f"\n✓ Master report saved: {report_file.name}")
        print(f"\n✓ Found {len(results)} sources with mathematical content")
        print(f"✓ All files saved to: {output_path}")
        
        print("\nTop 5 sources by math content:")
        for idx, res in enumerate(results[:5], 1):
            print(f"  {idx}. [{res['math_score']}/20] {res['title']}")
    else:
        print("\n✗ No sources with mathematical content found")
        print("This might indicate:")
        print("  - Sites are blocking the crawler")
        print("  - Network issues")
        print("  - Content doesn't contain mathematical terms")

urls = json.loads('$urlsJson')

asyncio.run(crawl_sources(
    urls=urls,
    output_dir=r'$outputDir',
    topic_name='$topicName'
))
"@

$crawlScript | Out-File -FilePath "temp_simple_crawl.py" -Encoding UTF8

# Run the crawler
python temp_simple_crawl.py

# Cleanup
Remove-Item "temp_simple_crawl.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Crawling Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

$openFolder = Read-Host "Open results folder? (y/n)"
if ($openFolder -eq 'y') {
    Invoke-Item $outputDir
}
