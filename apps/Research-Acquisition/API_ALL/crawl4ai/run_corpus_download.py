import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import csv
import re
from urllib.parse import urlparse
from datetime import datetime

def sanitize_filename(text, category):
    filename = f"{category}_{text}"
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.replace(' ', '_')
    
    if len(filename) > 150:
        filename = filename[:150]
    
    return filename

async def download_corpus():
    output_path = Path("philosophical_corpus")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load URLs from CSV
    urls = []
    with open('philosophical_corpus_urls.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            urls.append(row)
    
    print(f"{'='*70}")
    print(f"DOWNLOADING {len(urls)} PHILOSOPHICAL TEXTS")
    print(f"{'='*70}")
    print()
    
    results = {
        'success': [],
        'failed': []
    }
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        for idx, item in enumerate(urls, 1):
            url = item['URL']
            text_name = item['Text']
            category = item['Category']
            tier = item['Tier']
            
            print(f"\n{'='*70}")
            print(f"[{idx}/{len(urls)}] {text_name}")
            print(f"Category: {category} | Tier: {tier}")
            print(f"URL: {url}")
            print(f"{'='*70}")
            
            try:
                result = await crawler.arun(url=url)
                
                if result.success:
                    base_filename = sanitize_filename(text_name, category)
                    md_file = output_path / f"{base_filename}.md"
                    
                    # Create header with metadata
                    header = f"# {text_name}\n\n"
                    header += f"**Category:** {category}\n\n"
                    header += f"**Tier:** {tier}\n\n"
                    header += f"**Priority:** {item.get('Priority', 'N/A')}\n\n"
                    header += f"**URL:** {url}\n\n"
                    header += f"**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    header += f"**Notes:** {item.get('Notes', 'N/A')}\n\n"
                    header += "---\n\n"
                    
                    md_file.write_text(header + result.markdown, encoding='utf-8')
                    print(f"  ✓ Saved: {md_file.name}")
                    
                    results['success'].append({
                        'text': text_name,
                        'url': url,
                        'category': category,
                        'tier': tier
                    })
                else:
                    print(f"  ✗ Failed: {result.error_message or 'Unknown error'}")
                    results['failed'].append({
                        'text': text_name,
                        'url': url,
                        'error': result.error_message or 'Unknown error'
                    })
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                results['failed'].append({
                    'text': text_name,
                    'url': url,
                    'error': str(e)
                })
    
    # Create summary report
    print()
    print(f"{'='*70}")
    print("CREATING SUMMARY REPORT")
    print(f"{'='*70}")
    
    report_file = output_path / f"download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Philosophical Corpus Download Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Attempted:** {len(urls)}\n\n")
        f.write(f"**Successful:** {len(results['success'])}\n\n")
        f.write(f"**Failed:** {len(results['failed'])}\n\n")
        f.write("---\n\n")
        
        if results['success']:
            f.write("## Successfully Downloaded\n\n")
            
            # Group by tier
            by_tier = {}
            for item in results['success']:
                tier = item['tier']
                if tier not in by_tier:
                    by_tier[tier] = []
                by_tier[tier].append(item)
            
            for tier in sorted(by_tier.keys()):
                f.write(f"### Tier {tier}\n\n")
                for item in by_tier[tier]:
                    f.write(f"- **{item['text']}** ({item['category']})\n")
                    f.write(f"  - URL: {item['url']}\n\n")
        
        if results['failed']:
            f.write("## Failed Downloads\n\n")
            for item in results['failed']:
                f.write(f"- **{item['text']}**\n")
                f.write(f"  - URL: {item['url']}\n")
                f.write(f"  - Error: {item['error']}\n\n")
    
    print(f"\n{'='*70}")
    print("DOWNLOAD COMPLETE!")
    print(f"{'='*70}")
    print(f"✓ Successfully downloaded: {len(results['success'])}/{len(urls)}")
    print(f"✓ Report saved: {report_file.name}")
    print(f"✓ Files saved to: {output_path}")
    
    if results['failed']:
        print(f"\n⚠ {len(results['failed'])} downloads failed - see report for details")

asyncio.run(download_corpus())
