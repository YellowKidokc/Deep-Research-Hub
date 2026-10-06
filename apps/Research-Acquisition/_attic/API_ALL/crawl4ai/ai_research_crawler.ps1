# Deep Research Crawler for Crawl4AI
# Intelligent web crawling for detailed knowledge extraction

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Crawl4AI - Deep Research Crawler" -ForegroundColor Cyan
Write-Host "   (Adaptive Crawling with AI Intelligence)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This tool uses Crawl4AI's Adaptive Crawling to intelligently" -ForegroundColor Yellow
Write-Host "search the web and gather comprehensive information on your topic." -ForegroundColor Yellow
Write-Host ""

# Get research query
$query = Read-Host "What would you like to research?"

if ([string]::IsNullOrWhiteSpace($query)) {
    Write-Host "Error: Research query cannot be empty" -ForegroundColor Red
    exit 1
}

Write-Host ""
$startUrl = Read-Host "Starting URL (e.g., Wikipedia, documentation site, or press Enter for Google search)"

if ([string]::IsNullOrWhiteSpace($startUrl)) {
    # Use Google search as starting point
    $encodedQuery = [System.Web.HttpUtility]::UrlEncode($query)
    $startUrl = "https://www.google.com/search?q=$encodedQuery"
    Write-Host "Using Google search as starting point" -ForegroundColor Green
} elseif ($startUrl -notmatch '^https?://') {
    $startUrl = "https://$startUrl"
}

Write-Host ""
Write-Host "Crawling Strategy:" -ForegroundColor Cyan
Write-Host "  1. Statistical (Fast, no API needed, term-based)" -ForegroundColor White
Write-Host "  2. Embedding (Semantic understanding, requires more resources)" -ForegroundColor White

$strategyChoice = Read-Host "Choose strategy (1-2, default: 1)"
if ([string]::IsNullOrWhiteSpace($strategyChoice)) { $strategyChoice = "1" }

$strategy = if ($strategyChoice -eq "2") { "embedding" } else { "statistical" }

Write-Host ""
Write-Host "Advanced Options:" -ForegroundColor Cyan
$maxPages = Read-Host "Maximum pages to crawl (default: 20)"
if ([string]::IsNullOrWhiteSpace($maxPages)) { $maxPages = "20" }

$confidence = Read-Host "Confidence threshold 0-1 (default: 0.7, higher = more thorough)"
if ([string]::IsNullOrWhiteSpace($confidence)) { $confidence = "0.7" }

Write-Host ""
$defaultDir = Join-Path (Get-Location) "crawl4ai_research"
$outputDir = Read-Host "Output directory (default: $defaultDir)"

if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Created directory: $outputDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting intelligent research crawl..." -ForegroundColor Green
Write-Host "This may take several minutes depending on the topic complexity." -ForegroundColor Yellow
Write-Host ""

# Create the research script
$researchScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig
from pathlib import Path
import json
from datetime import datetime

async def deep_research(query, start_url, strategy, max_pages, confidence, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Research Query: {query}")
    print(f"Starting URL: {start_url}")
    print(f"Strategy: {strategy}")
    print(f"Max Pages: {max_pages}")
    print(f"Confidence Threshold: {confidence}")
    print("\n" + "="*60 + "\n")
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Configure adaptive crawler
        config = AdaptiveConfig(
            strategy=strategy,
            confidence_threshold=float(confidence),
            max_pages=int(max_pages),
            top_k_links=5,
            min_gain_threshold=0.05
        )
        
        adaptive = AdaptiveCrawler(crawler, config)
        
        print("Starting adaptive crawl...\n")
        
        try:
            # Run the adaptive crawl
            result = await adaptive.digest(
                start_url=start_url,
                query=query
            )
            
            print("\n" + "="*60)
            print("CRAWL STATISTICS")
            print("="*60)
            adaptive.print_stats()
            
            # Get relevant content
            print("\n" + "="*60)
            print("EXTRACTING RELEVANT CONTENT")
            print("="*60 + "\n")
            
            relevant_pages = adaptive.get_relevant_content(top_k=10)
            
            # Save comprehensive report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = output_path / f"research_report_{timestamp}.md"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# Research Report: {query}\n\n")
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Starting URL:** {start_url}\n\n")
                f.write(f"**Strategy:** {strategy}\n\n")
                f.write(f"**Pages Crawled:** {len(adaptive.visited_pages)}\n\n")
                f.write("---\n\n")
                
                f.write("## Summary Statistics\n\n")
                stats = adaptive.get_stats()
                for key, value in stats.items():
                    f.write(f"- **{key}:** {value}\n")
                f.write("\n---\n\n")
                
                f.write("## Most Relevant Pages\n\n")
                for idx, page in enumerate(relevant_pages, 1):
                    f.write(f"### {idx}. {page.get('title', 'Untitled')}\n\n")
                    f.write(f"**URL:** {page['url']}\n\n")
                    f.write(f"**Relevance Score:** {page['score']:.3f}\n\n")
                    
                    # Add content preview
                    content = page.get('markdown', '')
                    if content:
                        preview = content[:1000] + "..." if len(content) > 1000 else content
                        f.write(f"**Content Preview:**\n\n{preview}\n\n")
                    
                    f.write("---\n\n")
            
            print(f"\n✓ Research report saved: {report_file}")
            
            # Save individual pages
            pages_dir = output_path / f"pages_{timestamp}"
            pages_dir.mkdir(exist_ok=True)
            
            for idx, page in enumerate(relevant_pages, 1):
                page_file = pages_dir / f"page_{idx:02d}.md"
                
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {page.get('title', 'Untitled')}\n\n")
                    f.write(f"**URL:** {page['url']}\n\n")
                    f.write(f"**Relevance Score:** {page['score']:.3f}\n\n")
                    f.write("---\n\n")
                    f.write(page.get('markdown', ''))
                
                print(f"  ✓ Saved: {page_file.name}")
            
            # Save metadata
            metadata = {
                'query': query,
                'start_url': start_url,
                'strategy': strategy,
                'timestamp': timestamp,
                'stats': adaptive.get_stats(),
                'pages': [
                    {
                        'url': p['url'],
                        'title': p.get('title', 'Untitled'),
                        'score': p['score']
                    }
                    for p in relevant_pages
                ]
            }
            
            metadata_file = output_path / f"metadata_{timestamp}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"\n✓ Metadata saved: {metadata_file}")
            
            print("\n" + "="*60)
            print("RESEARCH COMPLETE!")
            print("="*60)
            print(f"\nAll files saved to: {output_path}")
            
        except Exception as e:
            print(f"\n✗ Error during research: {str(e)}")
            import traceback
            traceback.print_exc()

asyncio.run(deep_research(
    query='$query',
    start_url='$startUrl',
    strategy='$strategy',
    max_pages='$maxPages',
    confidence='$confidence',
    output_dir=r'$outputDir'
))
"@

$researchScript | Out-File -FilePath "temp_research.py" -Encoding UTF8

# Run the research
python temp_research.py

# Cleanup
Remove-Item "temp_research.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Research completed!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results saved to: $outputDir" -ForegroundColor White
Write-Host ""

$openFolder = Read-Host "Open results folder? (y/n)"
if ($openFolder -eq 'y') {
    Invoke-Item $outputDir
}
