"""
Search Crawler - Continuous web search until specific content is found
Saves all matching links to a list
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import sys
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import re

async def search_web(query, max_results, output_dir):
    """Search web continuously for specific content"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create links file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    links_file = output_path / f"found_links_{timestamp}.txt"
    report_file = output_path / f"search_report_{timestamp}.md"
    
    found_links = []
    searched_urls = set()
    
    print(f"\n{'='*70}")
    print(f"SEARCHING WEB FOR: {query}")
    print(f"{'='*70}\n")
    
    # Start with Google search
    search_engines = [
        f"https://www.google.com/search?q={quote_plus(query)}&num=50",
        f"https://www.bing.com/search?q={quote_plus(query)}&count=50"
    ]
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for search_url in search_engines:
            print(f"\nSearching: {search_url}\n")
            
            try:
                result = await crawler.arun(url=search_url)
                
                if result.success:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Extract all links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        # Clean Google/Bing wrapped URLs
                        if '/url?q=' in href:
                            href = href.split('/url?q=')[1].split('&')[0]
                        
                        # Skip search engine internal links
                        if any(x in href.lower() for x in ['google.com', 'bing.com', 'webcache', 'translate']):
                            continue
                        
                        if not href.startswith('http'):
                            continue
                        
                        if href in searched_urls:
                            continue
                        
                        searched_urls.add(href)
                        
                        # Check if we've found enough
                        if len(found_links) >= max_results:
                            break
                        
                        # Crawl the actual page to check content
                        print(f"\nChecking [{len(found_links)+1}/{max_results}]: {href}")
                        
                        try:
                            page_result = await crawler.arun(url=href)
                            
                            if page_result.success:
                                # Check if query terms are in content
                                content_lower = page_result.markdown.lower()
                                query_lower = query.lower()
                                
                                if query_lower in content_lower:
                                    print(f"  ✓ MATCH FOUND!")
                                    
                                    found_links.append({
                                        'url': href,
                                        'title': page_result.title or 'No title',
                                        'found_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                                    
                                    # Save page content
                                    filename = f"match_{len(found_links):03d}.md"
                                    page_file = output_path / filename
                                    
                                    header = f"# {page_result.title or 'Untitled'}\n\n"
                                    header += f"**URL:** {href}\n\n"
                                    header += f"**Found:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                    header += f"**Search Query:** {query}\n\n"
                                    header += "---\n\n"
                                    
                                    page_file.write_text(header + page_result.markdown, encoding='utf-8')
                                    print(f"  ✓ Saved: {filename}")
                                    
                                    # Update links file
                                    with open(links_file, 'w', encoding='utf-8') as f:
                                        for item in found_links:
                                            f.write(f"{item['url']}\n")
                                else:
                                    print(f"  ✗ No match")
                            else:
                                print(f"  ✗ Failed to crawl")
                                
                        except Exception as e:
                            print(f"  ✗ Error: {str(e)}")
                        
                        if len(found_links) >= max_results:
                            break
                    
            except Exception as e:
                print(f"Search error: {str(e)}")
            
            if len(found_links) >= max_results:
                break
    
    # Create report
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Web Search Report\n\n")
        f.write(f"**Search Query:** {query}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Results Found:** {len(found_links)}\n\n")
        f.write("---\n\n")
        f.write("## Found Links\n\n")
        
        for idx, item in enumerate(found_links, 1):
            f.write(f"{idx}. **{item['title']}**\n")
            f.write(f"   - URL: {item['url']}\n")
            f.write(f"   - Found: {item['found_at']}\n\n")
    
    print(f"\n{'='*70}")
    print(f"SEARCH COMPLETE")
    print(f"{'='*70}")
    print(f"Found: {len(found_links)} matching pages")
    print(f"Links saved: {links_file}")
    print(f"Report saved: {report_file}")
    print(f"Pages saved: {output_path}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python search_crawler.py <query> <max_results> <output_dir>")
        sys.exit(1)
    
    query = sys.argv[1]
    max_results = int(sys.argv[2])
    output_dir = sys.argv[3]
    
    asyncio.run(search_web(query, max_results, output_dir))
