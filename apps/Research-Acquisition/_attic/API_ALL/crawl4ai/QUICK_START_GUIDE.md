# Crawl4AI - Quick Start Guide

## 🎯 You're Ready to Go!

Crawl4AI is **already installed and working** on your system (v0.7.8).

---

## 📋 What You Have

### ✅ **4 Interactive Scripts** (No command-line needed!)

1. **`interactive_website_downloader.ps1`**

   - Download entire websites or single pages
   - Auto-detects page count
   - Choose Markdown, HTML, or both
   - Perfect for: Documentation, blogs, articles

2. **`batch_link_downloader.ps1`**

   - Download multiple URLs at once
   - Paste links or load from file
   - Extract all links from each page
   - Optional screenshots
   - Perfect for: Research, content collection

3. **`deep_research_crawler.ps1`** ⭐ **MOST POWERFUL**

   - Intelligent adaptive crawling
   - Automatically finds relevant pages
   - Stops when it has enough information
   - Generates comprehensive research reports
   - Perfect for: Deep research, knowledge gathering

4. **`setup_api_keys.ps1`**
   - Optional - only needed for advanced LLM features
   - Basic crawling works WITHOUT API keys!

---

## 🚀 How to Use the Scripts

### Method 1: Right-Click (Easiest)

1. Right-click any `.ps1` file
2. Select "Run with PowerShell"
3. Follow the prompts!

### Method 2: PowerShell

```powershell
cd d:\GitHub\crawl4ai
.\interactive_website_downloader.ps1
```

### Method 3: From Anywhere

```powershell
powershell -ExecutionPolicy Bypass -File "d:\GitHub\crawl4ai\interactive_website_downloader.ps1"
```

---

## 📖 Example Workflows

### **Download a Website**

```
1. Run: interactive_website_downloader.ps1
2. Enter URL: https://docs.python.org
3. Choose: Download all pages (y/n)
4. Choose: Output directory
5. Choose: Markdown only
6. Wait for completion!
```

### **Batch Download Links**

```
1. Run: batch_link_downloader.ps1
2. Choose: Paste URLs now
3. Paste your links (one per line)
4. Press Enter twice when done
5. Choose: Output directory
6. Choose: Markdown + HTML backup
7. Enable: Extract links (y)
8. Wait for completion!
```

### **Deep Research** ⭐

```
1. Run: deep_research_crawler.ps1
2. Enter query: "Python async programming best practices"
3. Starting URL: https://docs.python.org (or leave blank for Google)
4. Choose: Statistical strategy (no API needed)
5. Max pages: 20
6. Confidence: 0.7
7. Wait for intelligent crawling!
8. Get comprehensive research report!
```

---

## 🎨 Output Formats

### **Markdown** (Recommended)

- Clean, readable text
- Perfect for LLMs (ChatGPT, Claude)
- Preserves structure (headings, lists, tables)
- Removes ads, navigation, footers

### **HTML**

- Full page content
- Useful as backup
- Can be viewed in browser

### **Both**

- Best of both worlds
- Markdown for processing
- HTML for reference

---

## 💡 Pro Tips

### **Tip 1: Start Simple**

Try downloading a single page first to see the output quality:

```
URL: https://example.com
Download all: n
Format: Markdown only
```

### **Tip 2: Use Adaptive Crawling for Research**

The `deep_research_crawler.ps1` is incredibly powerful:

- It doesn't just download pages blindly
- It understands your query
- It finds the MOST relevant pages
- It stops when it has comprehensive coverage

### **Tip 3: Batch Processing**

Create a text file with URLs (one per line):

```
https://site1.com
https://site2.com/page1
https://site3.com/article
```

Then use `batch_link_downloader.ps1` and load from file!

### **Tip 4: Extract Links**

When batch downloading, enable "Extract links" to:

- Build a sitemap
- Find related content
- Discover hidden pages

### **Tip 5: No API Keys Needed!**

All scripts work perfectly WITHOUT any API keys:

- Basic crawling: No keys needed
- Adaptive crawling (statistical): No keys needed
- LLM extraction: Optional, only if you want AI-powered extraction

---

## 🔧 Troubleshooting

### **Script Won't Run?**

Enable script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Python Not Found?**

Make sure Python is in your PATH:

```powershell
python --version
```

### **Crawl4AI Import Error?**

Verify installation:

```powershell
python -c "import crawl4ai; print(crawl4ai.__version__.__version__)"
```

### **Browser Issues?**

Reinstall Playwright browsers:

```powershell
python -m playwright install chromium
```

---

## 🎯 Common Use Cases

### **1. Download Documentation**

```
Script: interactive_website_downloader.ps1
URL: https://docs.python.org/3/
Download all: y
Format: Markdown only
Result: Complete Python docs in clean Markdown!
```

### **2. Research a Topic**

```
Script: deep_research_crawler.ps1
Query: "machine learning deployment best practices"
Starting URL: (leave blank for Google)
Strategy: Statistical
Result: Comprehensive research report with top 10 relevant pages!
```

### **3. Monitor Competitors**

```
Script: batch_link_downloader.ps1
URLs: competitor1.com, competitor2.com, competitor3.com
Extract links: y
Screenshots: y
Result: Full snapshots of competitor sites!
```

### **4. Build Knowledge Base**

```
Script: deep_research_crawler.ps1
Query: "Your specific topic"
Max pages: 30
Confidence: 0.8
Result: Curated collection of most relevant content!
```

---

## 🌟 Advanced Features (When You're Ready)

### **API Keys (Optional)**

Run `setup_api_keys.ps1` to enable:

- LLM-powered extraction (GPT-4, Claude)
- Semantic understanding
- Structured data extraction

### **Python API**

For custom scripts, use the Python API directly:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)

asyncio.run(main())
```

### **Docker Deployment**

For production use:

```bash
docker pull unclecode/crawl4ai:latest
docker run -d -p 11235:11235 crawl4ai:latest
```

---

## 📚 Learn More

- **Full Documentation**: https://docs.crawl4ai.com/
- **Unique Features**: See `UNIQUE_FEATURES.md`
- **GitHub**: https://github.com/unclecode/crawl4ai
- **Examples**: Check the `docs/examples/` folder

---

## 🎉 You're All Set!

**Everything is ready to use right now!**

1. Pick a script based on your need
2. Run it (right-click → Run with PowerShell)
3. Follow the prompts
4. Get your results!

**No configuration needed. No API keys required. Just run and go!**

---

## 💬 Need Help?

If you run into issues:

1. Check the error message
2. Review the Troubleshooting section above
3. Make sure Python and Crawl4AI are installed
4. Try a simpler example first

**Happy Crawling! 🚀**
