"""
Dashboard Batch Crawler
Crawls multiple dashboard URLs and saves analytics data as Markdown
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
from datetime import datetime
import re
from urllib.parse import urlparse
import sys

def sanitize_filename(url, index):
    """Create safe filename from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/').replace('/', '_')
    
    if not path:
        filename = f"dashboard_{index:03d}_{domain}"
    else:
        filename = f"dashboard_{index:03d}_{domain}_{path}"
    
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename

def load_dashboard_urls(file_path):
    """Load URLs from text file"""
    urls = []
    
    if not Path(file_path).exists():
        print(f"Error: {file_path} not found!")
        return urls
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                urls.append(line)
    
    return urls

async def crawl_dashboards(urls_file, output_dir):
    """Crawl all dashboards from URL list"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load URLs
    urls = load_dashboard_urls(urls_file)
    
    if not urls:
        print("No URLs found to crawl!")
        return
    
    print(f"\n{'='*70}")
    print(f"DASHBOARD BATCH CRAWLER")
    print(f"{'='*70}")
    print(f"Total dashboards to crawl: {len(urls)}")
    print(f"Output directory: {output_path}")
    print(f"{'='*70}\n")
    
    results = {
        'success': [],
        'failed': []
    }
    
    start_time = datetime.now()
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for idx, url in enumerate(urls, 1):
            print(f"\n{'='*70}")
            print(f"[{idx}/{len(urls)}] Crawling Dashboard")
            print(f"URL: {url}")
            print(f"{'='*70}")
            
            try:
                result = await crawler.arun(url=url)
                
                if result.success:
                    # Generate filename
                    filename = sanitize_filename(url, idx)
                    md_file = output_path / f"{filename}.md"
                    
                    # Create header with metadata
                    header = f"# Dashboard {idx}: {result.title or 'Untitled'}\n\n"
                    header += f"**URL:** {url}\n\n"
                    header += f"**Dashboard Number:** {idx} of {len(urls)}\n\n"
                    header += f"**Crawled:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    header += f"**Status:** Success\n\n"
                    
                    # Add content statistics
                    content_length = len(result.markdown)
                    header += f"**Content Length:** {content_length:,} characters\n\n"
                    
                    # Check for common dashboard elements
                    content_lower = result.markdown.lower()
                    dashboard_indicators = []
                    
                    if 'chart' in content_lower or 'graph' in content_lower:
                        dashboard_indicators.append("Charts/Graphs detected")
                    if 'table' in content_lower or 'data' in content_lower:
                        dashboard_indicators.append("Tables/Data detected")
                    if 'metric' in content_lower or 'kpi' in content_lower:
                        dashboard_indicators.append("Metrics/KPIs detected")
                    if 'filter' in content_lower or 'date range' in content_lower:
                        dashboard_indicators.append("Filters detected")
                    
                    if dashboard_indicators:
                        header += f"**Dashboard Elements:** {', '.join(dashboard_indicators)}\n\n"
                    
                    header += "---\n\n"
                    
                    # Save the dashboard content
                    md_file.write_text(header + result.markdown, encoding='utf-8')
                    
                    print(f"  ✓ Saved: {md_file.name}")
                    print(f"  ✓ Content: {content_length:,} characters")
                    
                    results['success'].append({
                        'index': idx,
                        'url': url,
                        'title': result.title or 'Untitled',
                        'filename': md_file.name,
                        'size': content_length
                    })
                    
                else:
                    error_msg = result.error_message or 'Unknown error'
                    print(f"  ✗ Failed: {error_msg}")
                    
                    results['failed'].append({
                        'index': idx,
                        'url': url,
                        'error': error_msg
                    })
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                
                results['failed'].append({
                    'index': idx,
                    'url': url,
                    'error': str(e)
                })
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Create comprehensive report
    report_file = output_path / f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Dashboard Crawl Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Dashboards:** {len(urls)}\n\n")
        f.write(f"**Successful:** {len(results['success'])}\n\n")
        f.write(f"**Failed:** {len(results['failed'])}\n\n")
        f.write(f"**Duration:** {duration:.1f} seconds ({duration/60:.1f} minutes)\n\n")
        f.write(f"**Average Time:** {duration/len(urls):.1f} seconds per dashboard\n\n")
        f.write("---\n\n")
        
        if results['success']:
            f.write("## Successfully Crawled Dashboards\n\n")
            
            total_size = sum(item['size'] for item in results['success'])
            f.write(f"**Total Content:** {total_size:,} characters\n\n")
            
            for item in results['success']:
                f.write(f"### {item['index']}. {item['title']}\n\n")
                f.write(f"- **URL:** {item['url']}\n")
                f.write(f"- **File:** {item['filename']}\n")
                f.write(f"- **Size:** {item['size']:,} characters\n\n")
        
        if results['failed']:
            f.write("## Failed Dashboards\n\n")
            
            for item in results['failed']:
                f.write(f"### {item['index']}. Failed\n\n")
                f.write(f"- **URL:** {item['url']}\n")
                f.write(f"- **Error:** {item['error']}\n\n")
    
    # Create index file
    index_file = output_path / "index.md"
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("# Dashboard Collection Index\n\n")
        f.write(f"**Total Dashboards:** {len(urls)}\n\n")
        f.write(f"**Successfully Crawled:** {len(results['success'])}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write("## Dashboard Files\n\n")
        
        for item in sorted(results['success'], key=lambda x: x['index']):
            f.write(f"{item['index']}. [{item['title']}]({item['filename']})\n")
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"DASHBOARD CRAWL COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Successfully crawled: {len(results['success'])}/{len(urls)} dashboards")
    
    if results['failed']:
        print(f"✗ Failed: {len(results['failed'])} dashboards")
    
    print(f"⏱ Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"⏱ Average: {duration/len(urls):.1f} seconds per dashboard")
    print(f"\n📁 Files saved to: {output_path}")
    print(f"📊 Report: {report_file.name}")
    print(f"📑 Index: {index_file.name}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    urls_file = "dashboard_urls.txt"
    output_dir = "dashboard_analytics"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        urls_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    asyncio.run(crawl_dashboards(urls_file, output_dir))
