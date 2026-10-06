# Biblical Mathematics Research Tool
# Specialized deep research for mathematical analyses of Biblical events

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "   Biblical Mathematics Research Tool" -ForegroundColor Cyan
Write-Host "   Powered by Crawl4AI Adaptive Crawling + GPT-4" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This tool searches the internet for mathematical and scientific" -ForegroundColor Yellow
Write-Host "analyses of Biblical events, miracles, and phenomena." -ForegroundColor Yellow
Write-Host ""

# Predefined research topics
Write-Host "Search Method:" -ForegroundColor Cyan
Write-Host "  1. Google Search (broad, finds many sources)" -ForegroundColor White
Write-Host "  2. Direct Academic URLs (targeted, quality sources)" -ForegroundColor White
Write-Host "  3. Both (comprehensive - recommended)" -ForegroundColor White
Write-Host ""

$searchMethod = Read-Host "Choose search method (1-3, default: 3)"
if ([string]::IsNullOrWhiteSpace($searchMethod)) { $searchMethod = "3" }

Write-Host ""
Write-Host "Select a research topic:" -ForegroundColor Cyan
Write-Host "  1. Mathematical analysis of the Resurrection" -ForegroundColor White
Write-Host "  2. Mathematical patterns in Biblical miracles" -ForegroundColor White
Write-Host "  3. Mathematical codes and patterns in Scripture" -ForegroundColor White
Write-Host "  4. Scientific/mathematical analysis of the Crucifixion" -ForegroundColor White
Write-Host "  5. Astronomical calculations in Biblical events" -ForegroundColor White
Write-Host "  6. All of the above (comprehensive search)" -ForegroundColor White
Write-Host "  7. Custom query" -ForegroundColor White
Write-Host ""
Write-Host "  (Prophecy topics removed - you already have that content)" -ForegroundColor DarkGray
Write-Host ""

$topicChoice = Read-Host "Choose topic (1-7)"

$queries = @()
$directUrls = @()
$topicName = ""

switch ($topicChoice) {
    "1" { 
        $queries = @("mathematical analysis resurrection Jesus", "statistical probability resurrection", "mathematical evidence resurrection Christ")
        $directUrls = @(
            "https://www.reasonablefaith.org/writings/scholarly-writings/historical-jesus/the-resurrection-of-jesus/",
            "https://philpapers.org/browse/resurrection",
            "https://www.bethinking.org/is-christianity-true/the-resurrection-of-jesus"
        )
        $topicName = "Resurrection_Mathematics"
    }
    "2" { 
        $queries = @("mathematical patterns Biblical miracles", "statistical analysis Jesus miracles", "mathematical probability miracles")
        $directUrls = @(
            "https://philpapers.org/browse/miracles",
            "https://plato.stanford.edu/entries/miracles/",
            "https://www.bethinking.org/is-christianity-true/are-miracles-possible"
        )
        $topicName = "Miracles_Mathematics"
    }
    "3" { 
        $queries = @("mathematical codes Bible", "numerical patterns Scripture", "mathematical structure Bible", "gematria Biblical mathematics")
        $directUrls = @(
            "https://www.bethinking.org/is-the-bible-reliable",
            "https://www.reasonablefaith.org/writings/scholarly-writings/"
        )
        $topicName = "Biblical_Codes_Mathematics"
    }
    "4" { 
        $queries = @("scientific analysis crucifixion", "mathematical evidence crucifixion", "medical mathematical analysis crucifixion Jesus")
        $directUrls = @(
            "https://www.bethinking.org/is-christianity-true/the-resurrection-of-jesus",
            "https://www.reasonablefaith.org/writings/scholarly-writings/historical-jesus/"
        )
        $topicName = "Crucifixion_Analysis"
    }
    "5" { 
        $queries = @("astronomical calculations Biblical events", "mathematical astronomy Bible", "celestial mathematics Biblical prophecy")
        $directUrls = @(
            "https://www.bethinking.org/is-the-bible-reliable/the-star-of-bethlehem",
            "https://www.biblicalarchaeology.org/daily/biblical-topics/new-testament/the-star-of-bethlehem/"
        )
        $topicName = "Astronomical_Mathematics"
    }
    "6" { 
        $queries = @(
            "mathematical analysis resurrection Jesus",
            "statistical analysis Biblical miracles",
            "numerical patterns Scripture mathematics",
            "scientific mathematical analysis crucifixion",
            "astronomical calculations Biblical events"
        )
        $directUrls = @(
            "https://www.reasonablefaith.org/writings/scholarly-writings/",
            "https://philpapers.org/browse/miracles",
            "https://philpapers.org/browse/resurrection",
            "https://www.bethinking.org/is-christianity-true",
            "https://plato.stanford.edu/entries/miracles/",
            "https://www.str.org/articles"
        )
        $topicName = "Comprehensive_Biblical_Mathematics"
    }
    "7" { 
        $customQuery = Read-Host "Enter your custom research query"
        $queries = @($customQuery)
        $directUrls = @()
        $topicName = "Custom_Research"
    }
    default {
        Write-Host "Invalid choice. Using comprehensive search." -ForegroundColor Yellow
        $queries = @(
            "mathematical analysis resurrection Jesus",
            "statistical analysis Biblical miracles"
        )
        $directUrls = @(
            "https://www.reasonablefaith.org/writings/scholarly-writings/",
            "https://philpapers.org/browse/miracles"
        )
        $topicName = "Comprehensive_Biblical_Mathematics"
    }
}

Write-Host ""
Write-Host "Research Configuration:" -ForegroundColor Cyan
Write-Host ""

# Advanced options
$maxPages = Read-Host "Maximum pages per query (default: 30, recommended: 30-50 for thorough research)"
if ([string]::IsNullOrWhiteSpace($maxPages)) { $maxPages = "30" }

$confidence = Read-Host "Confidence threshold 0-1 (default: 0.75, higher = more thorough)"
if ([string]::IsNullOrWhiteSpace($confidence)) { $confidence = "0.75" }

Write-Host ""
Write-Host "Content Filtering:" -ForegroundColor Cyan
Write-Host "  1. Academic/scholarly sources only (strict)" -ForegroundColor White
Write-Host "  2. Include reputable blogs and articles (balanced)" -ForegroundColor White
Write-Host "  3. All sources with mathematical content (broad)" -ForegroundColor White

$filterChoice = Read-Host "Choose filter level (1-3, default: 2)"
if ([string]::IsNullOrWhiteSpace($filterChoice)) { $filterChoice = "2" }

Write-Host ""
$defaultDir = Join-Path (Get-Location) "biblical_mathematics_research"
$outputDir = Read-Host "Output directory (default: $defaultDir)"

if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Created directory: $outputDir" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting comprehensive Biblical mathematics research..." -ForegroundColor Green
Write-Host "This will search multiple queries to find the best mathematical analyses." -ForegroundColor Yellow
Write-Host ""

# Create the specialized research script
$queriesJson = $queries | ConvertTo-Json -Compress
$directUrlsJson = $directUrls | ConvertTo-Json -Compress
$researchScript = @"
import asyncio
from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.content_filter_strategy import BM25ContentFilter
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load API keys
load_dotenv()

async def biblical_math_research(queries, direct_urls, search_method, topic_name, max_pages, confidence, filter_level, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create master report
    master_report_file = output_path / f"{topic_name}_MasterReport_{timestamp}.md"
    
    all_results = []
    
    print("="*70)
    print("BIBLICAL MATHEMATICS RESEARCH")
    print("="*70)
    print(f"Topic: {topic_name}")
    print(f"Search Method: {search_method}")
    if search_method in ['1', '3']:
        print(f"Google queries: {len(queries)}")
    if search_method in ['2', '3']:
        print(f"Direct URLs: {len(direct_urls)}")
    print(f"Max pages per source: {max_pages}")
    print(f"Confidence threshold: {confidence}")
    print("="*70)
    print()
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        
        # PART 1: Crawl direct academic URLs if selected
        if search_method in ['2', '3'] and direct_urls:
            print()
            print("="*70)
            print("PART 1: CRAWLING DIRECT ACADEMIC SOURCES")
            print("="*70)
            print()
            
            for url_idx, direct_url in enumerate(direct_urls, 1):
                print()
                print(f"[{url_idx}/{len(direct_urls)}] Crawling: {direct_url}")
                print("-"*70)
                
                try:
                    result = await crawler.arun(url=direct_url)
                    
                    if result.success:
                        content = result.markdown
                        
                        # Score for mathematical content
                        math_keywords = [
                            'probability', 'statistical', 'mathematics', 'calculation',
                            'equation', 'formula', 'quantitative', 'numerical',
                            'analysis', 'odds', 'percentage', 'ratio', 'theorem',
                            'proof', 'evidence', 'scientific', 'empirical'
                        ]
                        
                        content_lower = content.lower()
                        math_score = sum(1 for keyword in math_keywords if keyword in content_lower)
                        
                        # Apply filter
                        should_include = False
                        if filter_level == '1':  # Academic only
                            if math_score >= 5 and any(domain in direct_url.lower() for domain in [
                                'edu', 'scholar', 'academic', 'journal', 'research', 'university', 'stanford', 'philpapers'
                            ]):
                                should_include = True
                        elif filter_level == '2':  # Balanced
                            if math_score >= 3:
                                should_include = True
                        else:  # Broad
                            if math_score >= 1:
                                should_include = True
                        
                        if should_include:
                            page_data = {
                                'url': direct_url,
                                'title': result.title or 'Untitled',
                                'markdown': content,
                                'score': 1.0,  # Direct URLs get high relevance
                                'math_score': math_score,
                                'source': 'direct_url'
                            }
                            all_results.append(page_data)
                            print(f"  ✓ Added (Math Score: {math_score}/10)")
                        else:
                            print(f"  ✗ Filtered out (Math Score: {math_score}/10)")
                    else:
                        print(f"  ✗ Failed to crawl")
                        
                except Exception as e:
                    print(f"  ✗ Error: {str(e)}")
            
            print()
            print(f"Direct URLs processed: {len([r for r in all_results if r['source'] == 'direct_url'])}")
        
        # PART 2: Google search if selected
        if search_method in ['1', '3'] and queries:
            print()
            print("="*70)
            print("PART 2: GOOGLE SEARCH & ADAPTIVE CRAWLING")
            print("="*70)
            print()
            
    async with AsyncWebCrawler(verbose=True) as crawler:
        for query_idx, query in enumerate(queries, 1):
            print()
            print("="*70)
            print(f"QUERY {query_idx}/{len(queries)}: {query}")
            print("="*70)
            print()
            
            # Configure adaptive crawler with content filtering
            config = AdaptiveConfig(
                strategy="statistical",  # Fast, no extra API calls
                confidence_threshold=float(confidence),
                max_pages=int(max_pages),
                top_k_links=7,  # More links for thorough research
                min_gain_threshold=0.03  # Lower threshold for more coverage
            )
            
            adaptive = AdaptiveCrawler(crawler, config)
            
            # Use Google Scholar and academic search as starting points
            search_urls = [
                f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}",
                f"https://www.google.com/search?q={query.replace(' ', '+')}+mathematics+analysis",
                f"https://www.google.com/search?q={query.replace(' ', '+')}+statistical+probability"
            ]
            
            query_results = []
            
            for search_idx, start_url in enumerate(search_urls, 1):
                try:
                    print(f"\nSearching from: {start_url}")
                    print("-"*70)
                    
                    result = await adaptive.digest(
                        start_url=start_url,
                        query=query + " mathematics statistics probability analysis"
                    )
                    
                    print("\nCrawl Statistics:")
                    adaptive.print_stats()
                    
                    # Get relevant content
                    relevant_pages = adaptive.get_relevant_content(top_k=15)
                    
                    # Filter for mathematical content
                    math_keywords = [
                        'probability', 'statistical', 'mathematics', 'calculation',
                        'equation', 'formula', 'quantitative', 'numerical',
                        'analysis', 'odds', 'percentage', 'ratio', 'theorem',
                        'proof', 'evidence', 'scientific', 'empirical'
                    ]
                    
                    filtered_pages = []
                    for page in relevant_pages:
                        content_lower = page.get('markdown', '').lower()
                        math_score = sum(1 for keyword in math_keywords if keyword in content_lower)
                        
                        # Filter based on user's choice
                        if filter_level == '1':  # Academic only
                            if math_score >= 5 and any(domain in page['url'].lower() for domain in [
                                'edu', 'scholar', 'academic', 'journal', 'research', 'university'
                            ]):
                                page['math_score'] = math_score
                                filtered_pages.append(page)
                        elif filter_level == '2':  # Balanced
                            if math_score >= 3:
                                page['math_score'] = math_score
                                filtered_pages.append(page)
                        else:  # Broad
                            if math_score >= 1:
                                page['math_score'] = math_score
                                page['source'] = 'google_search'
                                filtered_pages.append(page)
                    
                    # Sort by math score
                    filtered_pages.sort(key=lambda x: (x['math_score'], x['score']), reverse=True)
                    
                    query_results.extend(filtered_pages[:10])  # Top 10 from each search
                    
                    print(f"\nFound {len(filtered_pages)} pages with mathematical content")
                    
                except Exception as e:
                    print(f"Error searching {start_url}: {str(e)}")
                    continue
            
            # Remove duplicates by URL
            seen_urls = set()
            unique_results = []
            for page in query_results:
                if page['url'] not in seen_urls:
                    seen_urls.add(page['url'])
                    unique_results.append(page)
            
            all_results.extend(unique_results)
            
            # Save query-specific report
            if unique_results:
                query_report_file = output_path / f"Query_{query_idx:02d}_{timestamp}.md"
                
                with open(query_report_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Query {query_idx}: {query}\n\n")
                    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"**Pages Found:** {len(unique_results)}\n\n")
                    f.write("---\n\n")
                    
                    for idx, page in enumerate(unique_results, 1):
                        f.write(f"## {idx}. {page.get('title', 'Untitled')}\n\n")
                        f.write(f"**URL:** {page['url']}\n\n")
                        f.write(f"**Source:** {page.get('source', 'unknown')}\n\n")
                        f.write(f"**Relevance Score:** {page['score']:.3f}\n\n")
                        f.write(f"**Math Content Score:** {page['math_score']}/10\n\n")
                        
                        content = page.get('markdown', '')
                        if content:
                            f.write(f"**Content:**\n\n{content}\n\n")
                        
                        f.write("---\n\n")
                
                print(f"\n✓ Query report saved: {query_report_file.name}")
    
    # Create master comprehensive report
    print()
    print("="*70)
    print("CREATING MASTER REPORT")
    print("="*70)
    
    # Remove duplicates from all results
    seen_urls = set()
    final_results = []
    for page in all_results:
        if page['url'] not in seen_urls:
            seen_urls.add(page['url'])
            final_results.append(page)
    
    # Sort by combined score
    final_results.sort(key=lambda x: (x['math_score'], x['score']), reverse=True)
    
    with open(master_report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Biblical Mathematics Research: {topic_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Unique Pages Found:** {len(final_results)}\n\n")
        f.write(f"**Queries Searched:** {len(queries)}\n\n")
        f.write("---\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"This comprehensive research searched {len(queries)} different queries ")
        f.write(f"to find mathematical and statistical analyses of Biblical events. ")
        f.write(f"A total of {len(final_results)} unique sources with mathematical content were identified.\n\n")
        f.write("---\n\n")
        
        f.write("## Top Mathematical Analyses\n\n")
        
        for idx, page in enumerate(final_results[:50], 1):  # Top 50 results
            f.write(f"### {idx}. {page.get('title', 'Untitled')}\n\n")
            f.write(f"**URL:** {page['url']}\n\n")
            f.write(f"**Source:** {page.get('source', 'unknown')}\n\n")
            f.write(f"**Relevance Score:** {page['score']:.3f}\n\n")
            f.write(f"**Mathematical Content Score:** {page['math_score']}/10\n\n")
            
            content = page.get('markdown', '')
            if content:
                # Extract mathematical snippets
                lines = content.split('\n')
                math_lines = [line for line in lines if any(kw in line.lower() for kw in [
                    'probability', 'statistical', 'calculation', 'equation', 'odds', '%', 'ratio'
                ])]
                
                if math_lines:
                    f.write("**Key Mathematical Content:**\n\n")
                    for line in math_lines[:10]:  # First 10 mathematical lines
                        f.write(f"- {line.strip()}\n")
                    f.write("\n")
                
                f.write(f"**Full Content:**\n\n{content}\n\n")
            
            f.write("---\n\n")
    
    print(f"\n✓ Master report saved: {master_report_file.name}")
    
    # Save metadata
    metadata = {
        'topic': topic_name,
        'timestamp': timestamp,
        'total_queries': len(queries),
        'queries': queries,
        'total_pages_found': len(final_results),
        'filter_level': filter_level,
        'max_pages_per_query': max_pages,
        'confidence_threshold': confidence,
        'top_results': [
            {
                'url': p['url'],
                'title': p.get('title', 'Untitled'),
                'relevance_score': p['score'],
                'math_score': p['math_score']
            }
            for p in final_results[:20]
        ]
    }
    
    metadata_file = output_path / f"{topic_name}_Metadata_{timestamp}.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✓ Metadata saved: {metadata_file.name}")
    
    print()
    print("="*70)
    print("RESEARCH COMPLETE!")
    print("="*70)
    print(f"\nTotal unique sources found: {len(final_results)}")
    print(f"All files saved to: {output_path}")
    print()
    print("Top 5 sources by mathematical content:")
    for idx, page in enumerate(final_results[:5], 1):
        print(f"  {idx}. [{page['math_score']}/10] {page.get('title', 'Untitled')}")
        print(f"     {page['url']}")

queries = json.loads('$queriesJson')
direct_urls = json.loads('$directUrlsJson')
filter_level = '$filterChoice'
search_method = '$searchMethod'

asyncio.run(biblical_math_research(
    queries=queries,
    direct_urls=direct_urls,
    search_method=search_method,
    topic_name='$topicName',
    max_pages='$maxPages',
    confidence='$confidence',
    filter_level=filter_level,
    output_dir=r'$outputDir'
))
"@

$researchScript | Out-File -FilePath "temp_biblical_research.py" -Encoding UTF8

# Run the research
python temp_biblical_research.py

# Cleanup
Remove-Item "temp_biblical_research.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "Biblical Mathematics Research Complete!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Results saved to: $outputDir" -ForegroundColor White
Write-Host ""

$openFolder = Read-Host "Open results folder? (y/n)"
if ($openFolder -eq 'y') {
    Invoke-Item $outputDir
}
