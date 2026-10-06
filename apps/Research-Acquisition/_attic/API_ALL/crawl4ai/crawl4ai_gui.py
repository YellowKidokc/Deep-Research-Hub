"""
Crawl4AI Simple GUI
A user-friendly graphical interface for Crawl4AI web crawler
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import asyncio
from crawl4ai import AsyncWebCrawler
from pathlib import Path
import threading
from datetime import datetime
import re
from urllib.parse import urlparse

class Crawl4AIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Crawl4AI - Simple Web Crawler")
        self.root.geometry("900x700")
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.cwd() / "crawl_output"))
        self.format_var = tk.StringVar(value="markdown")
        self.is_crawling = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Crawl4AI Web Crawler", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL Input Section
        url_frame = ttk.LabelFrame(main_frame, text="URL to Crawl", padding="10")
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(1, weight=1)
        
        ttk.Label(url_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Quick examples
        ttk.Label(url_frame, text="Examples:", font=('Arial', 8)).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        examples_frame = ttk.Frame(url_frame)
        examples_frame.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        example_urls = [
            ("Wikipedia", "https://en.wikipedia.org/wiki/Web_scraping"),
            ("Python.org", "https://www.python.org/"),
            ("Example.com", "https://example.com")
        ]
        
        for idx, (name, url) in enumerate(example_urls):
            btn = ttk.Button(examples_frame, text=name, 
                           command=lambda u=url: self.url_var.set(u),
                           width=12)
            btn.grid(row=0, column=idx, padx=(0, 5))
        
        # Output Settings Section
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        # Output directory
        ttk.Label(output_frame, text="Output Dir:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(output_frame, text="Browse...", 
                  command=self.browse_output_dir).grid(row=0, column=2)
        
        # Output format
        ttk.Label(output_frame, text="Format:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        format_frame = ttk.Frame(output_frame)
        format_frame.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        ttk.Radiobutton(format_frame, text="Markdown", variable=self.format_var, 
                       value="markdown").grid(row=0, column=0, padx=(0, 15))
        ttk.Radiobutton(format_frame, text="HTML", variable=self.format_var, 
                       value="html").grid(row=0, column=1, padx=(0, 15))
        ttk.Radiobutton(format_frame, text="Both", variable=self.format_var, 
                       value="both").grid(row=0, column=2)
        
        # Crawl Options Section
        options_frame = ttk.LabelFrame(main_frame, text="Crawl Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.verbose_var = tk.BooleanVar(value=True)
        self.screenshot_var = tk.BooleanVar(value=False)
        self.extract_links_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(options_frame, text="Verbose output", 
                       variable=self.verbose_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Take screenshot", 
                       variable=self.screenshot_var).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Checkbutton(options_frame, text="Extract all links", 
                       variable=self.extract_links_var).grid(row=0, column=2, sticky=tk.W)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.crawl_button = ttk.Button(button_frame, text="Start Crawl", 
                                       command=self.start_crawl, width=20)
        self.crawl_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop", 
                                      command=self.stop_crawl, width=20, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log, width=20).grid(row=0, column=2)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(
            row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log Output Section
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready to crawl")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
    def browse_output_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def log(self, message):
        """Add message to log output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def sanitize_filename(self, url):
        """Create a safe filename from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/').replace('/', '_')
        
        if not path:
            filename = domain + '_index'
        else:
            filename = domain + '_' + path
        
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    def start_crawl(self):
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showerror("Error", "Please enter a URL to crawl")
            return
        
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("Error", "URL must start with http:// or https://")
            return
        
        self.is_crawling = True
        self.crawl_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.progress_var.set("Crawling...")
        self.status_var.set(f"Crawling: {url}")
        
        # Run crawl in separate thread
        thread = threading.Thread(target=self.run_crawl, args=(url,))
        thread.daemon = True
        thread.start()
    
    def stop_crawl(self):
        self.is_crawling = False
        self.log("Stopping crawl...")
        self.status_var.set("Crawl stopped by user")
    
    def run_crawl(self, url):
        """Run the actual crawl operation"""
        try:
            # Create output directory
            output_dir = Path(self.output_dir_var.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            
            self.log(f"Starting crawl of: {url}")
            self.log(f"Output directory: {output_dir}")
            
            # Run async crawl
            asyncio.run(self.crawl_url(url, output_dir))
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Crawl Error", str(e))
        finally:
            self.crawl_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.progress_bar.stop()
            self.progress_var.set("Complete" if self.is_crawling else "Stopped")
    
    async def crawl_url(self, url, output_dir):
        """Async crawl operation"""
        async with AsyncWebCrawler(verbose=self.verbose_var.get()) as crawler:
            self.log("Fetching page...")
            
            result = await crawler.arun(url=url)
            
            if not self.is_crawling:
                return
            
            if result.success:
                self.log("✓ Page fetched successfully")
                
                # Generate filename
                base_filename = self.sanitize_filename(url)
                
                # Save based on format selection
                format_choice = self.format_var.get()
                
                if format_choice in ("markdown", "both"):
                    md_file = output_dir / f"{base_filename}.md"
                    
                    # Add metadata header
                    header = f"# {result.title or 'Untitled'}\n\n"
                    header += f"**URL:** {url}\n\n"
                    header += f"**Crawled:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    header += "---\n\n"
                    
                    md_file.write_text(header + result.markdown, encoding='utf-8')
                    self.log(f"✓ Saved Markdown: {md_file.name}")
                
                if format_choice in ("html", "both"):
                    html_file = output_dir / f"{base_filename}.html"
                    html_file.write_text(result.html, encoding='utf-8')
                    self.log(f"✓ Saved HTML: {html_file.name}")
                
                # Extract links if requested
                if self.extract_links_var.get():
                    links_file = output_dir / f"{base_filename}_links.txt"
                    links = result.links.get('internal', []) + result.links.get('external', [])
                    links_file.write_text('\n'.join(links), encoding='utf-8')
                    self.log(f"✓ Saved {len(links)} links: {links_file.name}")
                
                # Take screenshot if requested
                if self.screenshot_var.get():
                    self.log("Taking screenshot...")
                    # Screenshot would require additional setup
                    self.log("⚠ Screenshot feature requires additional configuration")
                
                self.log(f"✓ Crawl complete! Files saved to: {output_dir}")
                self.status_var.set(f"Complete: {base_filename}")
                
                # Ask if user wants to open folder
                self.root.after(100, lambda: self.ask_open_folder(output_dir))
                
            else:
                error_msg = result.error_message or "Unknown error"
                self.log(f"✗ Crawl failed: {error_msg}")
                self.status_var.set(f"Failed: {error_msg}")
    
    def ask_open_folder(self, output_dir):
        """Ask user if they want to open the output folder"""
        if messagebox.askyesno("Success", "Crawl complete! Open output folder?"):
            import os
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(output_dir)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{output_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{output_dir}"')

def main():
    root = tk.Tk()
    app = Crawl4AIGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
