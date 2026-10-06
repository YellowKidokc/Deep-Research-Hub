# Continuous Research Crawler for Crawl4AI
# Long-term web crawling with search terms and category-based discovery

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Crawl4AI - Continuous Research Crawler" -ForegroundColor Cyan
Write-Host "   Long-term Search & Category Discovery" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This tool performs continuous web research by:" -ForegroundColor Yellow
Write-Host "  • Searching across multiple engines for your topics" -ForegroundColor White
Write-Host "  • Categorizing and filtering results by domain types" -ForegroundColor White
Write-Host "  • Running for extended periods to discover comprehensive results" -ForegroundColor White
Write-Host "  • Saving results in organized categories for analysis" -ForegroundColor White
Write-Host ""

# Research configuration
$researchQuery = Read-Host "Main research query/topic"

if ([string]::IsNullOrWhiteSpace($researchQuery)) {
    Write-Host "Error: Research query cannot be empty" -ForegroundColor Red
    exit 1
}

# Category definitions
Write-Host ""
Write-Host "Define search categories (e.g., academic, news, blogs, etc.):" -ForegroundColor Cyan
Write-Host "Enter category names one per line, press Enter twice when done:" -ForegroundColor Yellow
Write-Host ""

$categories = @()
while ($true) {
    $category = Read-Host "Category (or Enter to finish)"
    if ([string]::IsNullOrWhiteSpace($category)) {
        break
    }
    $categories += $category.Trim()
}

if ($categories.Count -eq 0) {
    # Default categories
    $categories = @("academic", "news", "blogs", "organizations", "research")
    Write-Host "Using default categories: $($categories -join ', ')" -ForegroundColor Green
}

# Domain filters for each category
$categoryDomains = @{}
foreach ($category in $categories) {
    Write-Host ""
    Write-Host "Domain filters for '$category' category:" -ForegroundColor Cyan
    Write-Host "Enter domains (e.g., edu,org,gov) or keywords (press Enter for none):" -ForegroundColor Yellow
    $domains = Read-Host

    if (-not [string]::IsNullOrWhiteSpace($domains)) {
        $categoryDomains[$category] = $domains.Split(',') | ForEach-Object { $_.Trim() }
    } else {
        $categoryDomains[$category] = @()
    }
}

# Search engines
Write-Host ""
Write-Host "Search Engines:" -ForegroundColor Cyan
Write-Host "  1. Google only" -ForegroundColor White
Write-Host "  2. Bing + Google (recommended)" -ForegroundColor White
Write-Host "  3. All engines (Google, Bing, SearXNG)" -ForegroundColor White

$engineChoice = Read-Host "Choose engines (1-3, default: 2)"
if ([string]::IsNullOrWhiteSpace($engineChoice)) { $engineChoice = "2" }

$searchEngines = @()
switch ($engineChoice) {
    "1" { $searchEngines = @("google") }
    "2" { $searchEngines = @("google", "bing") }
    "3" { $searchEngines = @("google", "bing", "searxng") }
    default { $searchEngines = @("google", "bing") }
}

# Research parameters
Write-Host ""
Write-Host "Research Parameters:" -ForegroundColor Cyan

$maxPagesPerCategory = Read-Host "Max pages per category (default: 50)"
if ([string]::IsNullOrWhiteSpace($maxPagesPerCategory)) { $maxPagesPerCategory = "50" }

$maxCrawlingTime = Read-Host "Max crawling time in minutes (default: 30)"
if ([string]::IsNullOrWhiteSpace($maxCrawlingTime)) { $maxCrawlingTime = "30" }

$delayBetweenSearches = Read-Host "Delay between searches in seconds (default: 3)"
if ([string]::IsNullOrWhiteSpace($delayBetweenSearches)) { $delayBetweenSearches = "3" }

# Output directory
Write-Host ""
$defaultDir = Join-Path (Get-Location) "continuous_research_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$outputDir = Read-Host "Output directory (default: $(Split-Path $defaultDir -Leaf))"

if ([string]::IsNullOrWhiteSpace($outputDir)) {
    $outputDir = $defaultDir
}

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Created directory: $outputDir" -ForegroundColor Green
}

# Content processing options
Write-Host ""
Write-Host "Content Processing:" -ForegroundColor Cyan
$downloadContent = Read-Host "Download full content of found pages? (y/n, default: n)"
$saveSummaries = Read-Host "Generate AI summaries of findings? (y/n, default: y)"

if ([string]::IsNullOrWhiteSpace($downloadContent)) { $downloadContent = "n" }
if ([string]::IsNullOrWhiteSpace($saveSummaries)) { $saveSummaries = "y" }

Write-Host ""
Write-Host "Research Configuration Summary:" -ForegroundColor Green
Write-Host "  Query: $researchQuery" -ForegroundColor White
Write-Host "  Categories: $($categories -join ', ')" -ForegroundColor White
Write-Host "  Engines: $($searchEngines -join ', ')" -ForegroundColor White
Write-Host "  Max pages per category: $maxPagesPerCategory" -ForegroundColor White
Write-Host "  Max time: $maxCrawlingTime minutes" -ForegroundColor White
Write-Host "  Download content: $(if ($downloadContent -eq 'y') {'Yes'} else {'No'})" -ForegroundColor White
Write-Host "  Generate summaries: $(if ($saveSummaries -eq 'y') {'Yes'} else {'No'})" -ForegroundColor White

Write-Host ""
$confirm = Read-Host "Start continuous research? (y/n, default: y)"
if ($confirm -eq 'n') {
    Write-Host "Research cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🔍 Starting continuous research crawler..." -ForegroundColor Green
Write-Host "   This will run for up to $maxCrawlingTime minutes" -ForegroundColor Yellow
Write-Host ""

# Create the research script
$categoriesJson = $categories | ConvertTo-Json -Compress
$categoryDomainsJson = $categoryDomains | ConvertTo-Json -Compress
$searchEnginesJson = $searchEngines | ConvertTo-Json -Compress

$researchScript = @"
import asyncio
import json
import csv
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus, urlparse
import re

from crawl4ai import AsyncWebCrawler, AdaptiveCrawler, AdaptiveConfig
from bs4 import BeautifulSoup

class ContinuousResearchCrawler:
    def __init__(self, query, categories, category_domains, search_engines,
                 max_pages_per_category, max_time_minutes, output_dir,
                 download_content, save_summaries, delay_between_searches):

        self.query = query
        self.categories = categories
        self.category_domains = category_domains
        self.search_engines = search_engines
        self.max_pages_per_category = int(max_pages_per_category)
        self.max_time_minutes = int(max_time_minutes)
        self.output_dir = Path(output_dir)
        self.download_content = download_content.lower() == 'true'
        self.save_summaries = save_summaries.lower() == 'true'
        self.delay_between_searches = int(delay_between_searches)

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(minutes=self.max_time_minutes)

        # Create output structure
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.categories_dir = self.output_dir / 'categories'
        self.categories_dir.mkdir(exist_ok=True)

        if self.download_content:
            self.content_dir = self.output_dir / 'downloaded_content'
            self.content_dir.mkdir(exist_ok=True)

        # Tracking
        self.results = {cat: [] for cat in self.categories}
        self.stats = {
            'searches_performed': 0,
            'pages_found': 0,
            'pages_downloaded': 0,
            'start_time': self.start_time.isoformat(),
            'categories': self.categories
        }

    def should_continue(self):
        return datetime.now() < self.end_time

    def categorize_url(self, url):
        """Categorize URL based on domain filters"""
        try:
            domain = urlparse(url).netloc.lower()

            for category, domains in self.category_domains.items():
                if not domains:  # No filters for this category
                    continue

                for domain_filter in domains:
                    if domain_filter.lower() in domain:
                        return category

            # If no specific category matches, try to infer
            if any(ext in domain for ext in ['.edu', '.ac.uk', '.ac.']):
                return 'academic'
            elif any(ext in domain for ext in ['.org', '.gov']):
                return 'organizations'
            elif any(word in domain for word in ['news', 'times', 'post', 'journal']):
                return 'news'
            elif any(word in domain for word in ['blog', 'wordpress', 'medium']):
                return 'blogs'

        except:
            pass

        return 'general'

    async def search_engine(self, engine, category, page_num=1):
        """Search using a specific engine for a category"""
        search_query = f"{self.query} {category}"

        if engine == "google":
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}&start={page_num*10}"
        elif engine == "bing":
            search_url = f"https://www.bing.com/search?q={quote_plus(search_query)}&first={page_num*10 + 1}"
        elif engine == "searxng":
            search_url = f"https://searx.be/search?q={quote_plus(search_query)}&categories=general&pageno={page_num + 1}"
        else:
            return []

        print(f"🔍 Searching {engine} for: {search_query}")

        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=search_url)

                if not result.success:
                    print(f"   ✗ Search failed: {result.error_message}")
                    return []

                soup = BeautifulSoup(result.html, 'html.parser')
                links = []

                # Extract links based on search engine
                for link in soup.find_all('a', href=True):
                    href = link['href']

                    # Clean up URLs based on engine
                    if engine == "google" and '/url?q=' in href:
                        href = href.split('/url?q=')[1].split('&')[0]
                    elif engine == "bing":
                        pass  # Bing links are usually direct
                    elif engine == "searxng":
                        pass  # SearXNG links are usually direct

                    # Validate URL
                    if not href.startswith('http'):
                        continue

                    # Skip internal search pages
                    if any(x in href.lower() for x in ['google.com', 'bing.com', 'searx', 'webcache']):
                        continue

                    link_text = link.get_text(strip=True)

                    links.append({
                        'url': href,
                        'title': link_text[:200] if link_text else 'No title',
                        'engine': engine,
                        'category': category,
                        'found_at': datetime.now().isoformat()
                    })

                    if len(links) >= 10:  # Limit per search
                        break

                print(f"   ✓ Found {len(links)} links")
                return links

        except Exception as e:
            print(f"   ✗ Error searching {engine}: {str(e)}")
            return []

    async def download_page_content(self, url, category, title):
        """Download full content of a page"""
        if not self.download_content:
            return None

        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)

                if result.success:
                    # Save content
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:100]
                    filename = f"{safe_title}.md"

                    content_file = self.content_dir / filename
                    content_file.write_text(result.markdown, encoding='utf-8')

                    self.stats['pages_downloaded'] += 1

                    return {
                        'file': str(content_file),
                        'content_length': len(result.markdown),
                        'downloaded_at': datetime.now().isoformat()
                    }
                else:
                    print(f"   ✗ Failed to download: {result.error_message}")
                    return None

        except Exception as e:
            print(f"   ✗ Error downloading {url}: {str(e)}")
            return None

    async def run_research(self):
        """Main research loop"""
        print(f"\\n🚀 Starting continuous research: {self.query}")
        print(f"⏰ Will run until: {self.end_time.strftime('%H:%M:%S')}")
        print(f"📊 Categories: {', '.join(self.categories)}")
        print(f"🔍 Engines: {', '.join(self.search_engines)}")
        print("="*80)

        iteration = 0

        while self.should_continue():
            iteration += 1
            print(f"\\n🔄 Iteration {iteration} - {datetime.now().strftime('%H:%M:%S')}")

            for category in self.categories:
                if not self.should_continue():
                    break

                # Check if we have enough results for this category
                if len(self.results[category]) >= self.max_pages_per_category:
                    continue

                print(f"\\n📂 Researching category: {category}")

                # Search each engine
                for engine in self.search_engines:
                    if not self.should_continue():
                        break

                    try:
                        links = await self.search_engine(engine, category, 0)
                        self.stats['searches_performed'] += 1

                        # Process found links
                        for link_data in links:
                            url = link_data['url']

                            # Check if we already have this URL
                            if any(r['url'] == url for r in self.results[category]):
                                continue

                            # Categorize the URL
                            detected_category = self.categorize_url(url)

                            # Add to appropriate category
                            if detected_category in self.results:
                                self.results[detected_category].append(link_data)
                                self.stats['pages_found'] += 1

                                print(f"   ➕ Added to {detected_category}: {link_data['title'][:50]}...")

                                # Download content if requested
                                if self.download_content:
                                    content_info = await self.download_page_content(
                                        url, detected_category, link_data['title']
                                    )
                                    if content_info:
                                        link_data['content_downloaded'] = content_info

                        # Delay between searches
                        if self.delay_between_searches > 0:
                            await asyncio.sleep(self.delay_between_searches)

                    except Exception as e:
                        print(f"   ✗ Error in {engine} search: {str(e)}")

            # Progress update
            total_found = sum(len(results) for results in self.results.values())
            print(f"\\n📊 Progress: {total_found} total pages found")

            for cat, results in self.results.items():
                print(f"   {cat}: {len(results)} pages")

            # Save intermediate results every 5 iterations
            if iteration % 5 == 0:
                await self.save_results(intermediate=True)

        # Final save
        await self.save_results(intermediate=False)

        print("\\n" + "="*80)
        print("🎉 CONTINUOUS RESEARCH COMPLETE!")
        print("="*80)

    async def save_results(self, intermediate=False):
        """Save research results to files"""
        timestamp = "intermediate" if intermediate else "final"
        base_name = f"research_results_{timestamp}"

        # Save detailed results by category
        for category, results in self.results.items():
            category_file = self.categories_dir / f"{category}_{timestamp}.json"
            with open(category_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        # Save summary CSV
        csv_file = self.output_dir / f"{base_name}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Title', 'URL', 'Engine', 'Found_At'])

            for category, results in self.results.items():
                for result in results:
                    writer.writerow([
                        category,
                        result['title'],
                        result['url'],
                        result['engine'],
                        result['found_at']
                    ])

        # Save statistics
        stats_file = self.output_dir / f"research_stats_{timestamp}.json"
        current_stats = self.stats.copy()
        current_stats['end_time'] = datetime.now().isoformat()
        current_stats['duration_minutes'] = (datetime.now() - self.start_time).total_seconds() / 60
        current_stats['results_per_category'] = {cat: len(results) for cat, results in self.results.items()}

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(current_stats, f, indent=2)

        # Save research summary
        summary_file = self.output_dir / f"research_summary_{timestamp}.md"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# Research Summary: {self.query}\\n\\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
            f.write(f"**Duration:** {current_stats['duration_minutes']:.1f} minutes\\n\\n")
            f.write(f"**Searches Performed:** {current_stats['searches_performed']}\\n\\n")
            f.write(f"**Total Pages Found:** {current_stats['pages_found']}\\n\\n")

            if self.download_content:
                f.write(f"**Pages Downloaded:** {current_stats['pages_downloaded']}\\n\\n")

            f.write("## Results by Category\\n\\n")

            for category, results in self.results.items():
                f.write(f"### {category.title()} ({len(results)} pages)\\n\\n")

                if results:
                    for i, result in enumerate(results[:10], 1):  # Show first 10
                        f.write(f"{i}. **{result['title']}**\\n")
                        f.write(f"   - URL: {result['url']}\\n")
                        f.write(f"   - Source: {result['engine']}\\n")

                        if 'content_downloaded' in result:
                            f.write(f"   - Content: {result['content_downloaded']['file']}\\n")

                        f.write("\\n")

                    if len(results) > 10:
                        f.write(f"*... and {len(results) - 10} more pages*\\n\\n")
                else:
                    f.write("No pages found.\\n\\n")

            f.write("## Files Generated\\n\\n")
            f.write(f"- {csv_file.name} - CSV summary\\n")
            f.write(f"- {stats_file.name} - Detailed statistics\\n")

            for category in self.categories:
                f.write(f"- categories/{category}_{timestamp}.json - {category} results\\n")

            if self.download_content:
                f.write(f"- downloaded_content/ - Full page content\\n")

        print(f"💾 {'Intermediate' if intermediate else 'Final'} results saved to {self.output_dir}")

async def main():
    categories = json.loads('$categoriesJson')
    category_domains = json.loads('$categoryDomainsJson')
    search_engines = json.loads('$searchEnginesJson')

    crawler = ContinuousResearchCrawler(
        query='$researchQuery',
        categories=categories,
        category_domains=category_domains,
        search_engines=search_engines,
        max_pages_per_category='$maxPagesPerCategory',
        max_time_minutes='$maxCrawlingTime',
        output_dir=r'$outputDir',
        download_content='$downloadContent',
        save_summaries='$saveSummaries',
        delay_between_searches='$delayBetweenSearches'
    )

    await crawler.run_research()

if __name__ == "__main__":
    asyncio.run(main())
"@

$researchScript | Out-File -FilePath "temp_continuous_research.py" -Encoding UTF8

# Run the research
python temp_continuous_research.py

# Cleanup
Remove-Item "temp_continuous_research.py" -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Continuous Research Completed!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📁 Results saved to: $outputDir" -ForegroundColor White
Write-Host ""

# Show what was created
if (Test-Path $outputDir) {
    Write-Host "📊 Generated Files:" -ForegroundColor Cyan

    Get-ChildItem $outputDir -File -Recurse | ForEach-Object {
        $relativePath = $_.FullName.Replace($outputDir, "").TrimStart("\\")
        Write-Host "   📄 $relativePath" -ForegroundColor White
    }

    $subdirs = Get-ChildItem $outputDir -Directory
    if ($subdirs.Count -gt 0) {
        Write-Host "   📁 Directories:" -ForegroundColor Gray
        foreach ($dir in $subdirs) {
            $fileCount = Get-ChildItem $dir.FullName -File -Recurse | Measure-Object | Select-Object -ExpandProperty Count
            Write-Host "      $($dir.Name)/ ($fileCount files)" -ForegroundColor Gray
        }
    }
}

Write-Host ""
$openFolder = Read-Host "Open results folder? (y/n, default: y)"
if ([string]::IsNullOrWhiteSpace($openFolder) -or $openFolder -eq 'y') {
    Invoke-Item $outputDir
}

Write-Host ""
Write-Host "💡 Next steps:" -ForegroundColor Cyan
Write-Host "   • Review the research_summary_final.md for an overview" -ForegroundColor White
Write-Host "   • Check category-specific JSON files for detailed results" -ForegroundColor White
Write-Host "   • Use the CSV file for easy filtering and analysis" -ForegroundColor White
if ($downloadContent -eq 'y') {
    Write-Host "   • Full content is available in the downloaded_content folder" -ForegroundColor White
}