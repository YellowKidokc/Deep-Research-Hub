#!/usr/bin/env python3
"""
🎬 YouTube Text Extractor - Professional Interface
A clean, paper-like interface for downloading YouTube videos and extracting text
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import subprocess
import sys
import os
import json
import time
from pathlib import Path
import re

class YouTubeTextExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 YouTube Text Extractor - Professional")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.bg_color = '#ffffff'
        self.paper_color = '#fafafa'
        self.accent_color = '#ff0000'  # YouTube red
        self.text_color = '#333333'
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Main container with paper-like background
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.accent_color, relief=tk.RAISED, bd=2)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame, text="🎬 YouTube Text Extractor", 
                              font=("Arial", 24, "bold"), 
                              bg=self.accent_color, fg='white')
        title_label.pack(pady=15)
        
        subtitle = tk.Label(header_frame, text="Download Videos • Extract Text • Analyze Content", 
                           font=("Arial", 12), 
                           bg=self.accent_color, fg='#ffcccc')
        subtitle.pack(pady=(0, 15))
        
        # Paper-like content area
        paper_frame = tk.Frame(main_frame, bg=self.paper_color, relief=tk.RIDGE, bd=2)
        paper_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(paper_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Quick Extract
        self.create_quick_extract_tab()
        
        # Tab 2: Batch Processing
        self.create_batch_tab()
        
        # Tab 3: Settings
        self.create_settings_tab()
        
        # Status bar
        self.status_bar = tk.Label(main_frame, text="Ready", 
                                  bg='#e0e0e0', fg=self.text_color, 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_quick_extract_tab(self):
        tab = tk.Frame(self.notebook, bg=self.paper_color)
        self.notebook.add(tab, text="🚀 Quick Extract")
        
        # URL Input Section
        url_frame = tk.LabelFrame(tab, text="📺 YouTube URL", font=("Arial", 12, "bold"),
                                bg=self.paper_color, fg=self.text_color)
        url_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.url_entry = tk.Text(url_frame, height=3, font=("Arial", 11),
                                bg='white', fg=self.text_color, 
                                relief=tk.SUNKEN, bd=2)
        self.url_entry.pack(fill=tk.X, padx=10, pady=10)
        self.url_entry.insert('1.0', "Paste YouTube video or playlist URLs here...\n"
                                   "One URL per line, or single URL")
        
        # Options Section
        options_frame = tk.LabelFrame(tab, text="⚙️ Options", font=("Arial", 12, "bold"),
                                   bg=self.paper_color, fg=self.text_color)
        options_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Model Selection
        model_frame = tk.Frame(options_frame, bg=self.paper_color)
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(model_frame, text="Transcription Model:", font=("Arial", 10),
                bg=self.paper_color, fg=self.text_color).pack(side=tk.LEFT, padx=(0, 10))
        
        self.model_var = tk.StringVar(value="base")
        models = [("Tiny (Fastest)", "tiny"), ("Base (Recommended)", "base"), 
                 ("Small (Good)", "small"), ("Medium (Better)", "medium")]
        
        for text, value in models:
            tk.Radiobutton(model_frame, text=text, variable=self.model_var, value=value,
                          bg=self.paper_color, fg=self.text_color, 
                          font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # Output Options
        output_frame = tk.Frame(options_frame, bg=self.paper_color)
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(output_frame, text="Output Folder:", font=("Arial", 10),
                bg=self.paper_color, fg=self.text_color).pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_var = tk.StringVar(value="extracted_content")
        tk.Entry(output_frame, textvariable=self.output_var, font=("Arial", 10),
                bg='white', fg=self.text_color).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(output_frame, text="Browse", command=self.browse_output,
                 bg='#e0e0e0', fg=self.text_color, font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Action Buttons
        button_frame = tk.Frame(tab, bg=self.paper_color)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(button_frame, text="🎬 Download & Transcribe", 
                 command=self.start_extraction,
                 bg=self.accent_color, fg='white', font=("Arial", 12, "bold"),
                 height=2, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="📋 Find Bible Videos", 
                 command=self.find_bible_videos,
                 bg='#4CAF50', fg='white', font=("Arial", 11, "bold"),
                 height=2, width=18).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(button_frame, text="📁 Open Downloads", 
                 command=self.open_downloads,
                 bg='#2196F3', fg='white', font=("Arial", 11),
                 height=2, width=15).pack(side=tk.LEFT)
        
        # Progress Section
        progress_frame = tk.LabelFrame(tab, text="📊 Progress", font=("Arial", 12, "bold"),
                                     bg=self.paper_color, fg=self.text_color)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=15, 
                                                      font=("Consolas", 9),
                                                      bg='white', fg=self.text_color)
        self.progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_batch_tab(self):
        tab = tk.Frame(self.notebook, bg=self.paper_color)
        self.notebook.add(tab, text="📦 Batch Processing")
        
        # Instructions
        inst_frame = tk.LabelFrame(tab, text="📝 Instructions", font=("Arial", 12, "bold"),
                                 bg=self.paper_color, fg=self.text_color)
        inst_frame.pack(fill=tk.X, padx=20, pady=20)
        
        instructions = """
1. Create a text file with YouTube URLs (one per line)
2. Save it as 'urls.txt' in the downloads folder
3. Click 'Start Batch Processing'
4. All videos will be downloaded and transcribed automatically

Example urls.txt content:
https://www.youtube.com/watch?v=VIDEO1
https://www.youtube.com/watch?v=VIDEO2
https://www.youtube.com/watch?v=VIDEO3
        """
        
        inst_text = tk.Text(inst_frame, height=10, font=("Arial", 10),
                          bg='white', fg=self.text_color)
        inst_text.pack(fill=tk.X, padx=10, pady=10)
        inst_text.insert('1.0', instructions.strip())
        inst_text.config(state=tk.DISABLED)
        
        # Batch Controls
        batch_frame = tk.Frame(tab, bg=self.paper_color)
        batch_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(batch_frame, text="📄 Create Sample URLs File", 
                 command=self.create_sample_urls,
                 bg='#FF9800', fg='white', font=("Arial", 11, "bold"),
                 height=2, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(batch_frame, text="🚀 Start Batch Processing", 
                 command=self.start_batch,
                 bg=self.accent_color, fg='white', font=("Arial", 12, "bold"),
                 height=2, width=20).pack(side=tk.LEFT)
        
        # Batch Progress
        batch_progress_frame = tk.LabelFrame(tab, text="📊 Batch Progress", 
                                           font=("Arial", 12, "bold"),
                                           bg=self.paper_color, fg=self.text_color)
        batch_progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.batch_progress = scrolledtext.ScrolledText(batch_progress_frame, height=15,
                                                       font=("Consolas", 9),
                                                       bg='white', fg=self.text_color)
        self.batch_progress.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_settings_tab(self):
        tab = tk.Frame(self.notebook, bg=self.paper_color)
        self.notebook.add(tab, text="⚙️ Settings")
        
        # Settings sections
        settings_info = """
🎬 YouTube Text Extractor - Settings

📊 PERFORMANCE SETTINGS:
• Model Quality: Higher models = better accuracy but slower processing
• Output Format: Choose where to save downloaded content
• Auto-open: Automatically open folders when complete

🔧 TECHNICAL SETTINGS:
• FFmpeg Path: Location of FFmpeg executable
• Temp Directory: Where temporary files are stored
• Concurrent Downloads: How many videos to process at once

💡 TIPS:
• Use 'Base' model for best balance of speed and accuracy
• Organize content by topic using different output folders
• Check transcripts folder for processed text files

📁 DEFAULT FOLDERS:
• Downloads: ./downloads/
• Transcripts: ./transcripts/
• Temporary: ./temp/
        """
        
        settings_text = scrolledtext.ScrolledText(tab, font=("Arial", 11),
                                                 bg='white', fg=self.text_color)
        settings_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        settings_text.insert('1.0', settings_info.strip())
        settings_text.config(state=tk.DISABLED)
        
    def browse_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_var.set(folder)
            
    def log_message(self, message, tab="progress"):
        """Add message to progress log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        if tab == "progress":
            self.progress_text.insert(tk.END, log_entry)
            self.progress_text.see(tk.END)
            self.root.update()
        else:
            self.batch_progress.insert(tk.END, log_entry)
            self.batch_progress.see(tk.END)
            self.root.update()
            
        self.status_bar.config(text=message)
        
    def start_extraction(self):
        """Start the extraction process"""
        urls = self.url_entry.get('1.0', tk.END).strip().split('\n')
        urls = [url.strip() for url in urls if url.strip() and not url.startswith("Paste")]
        
        if not urls:
            messagebox.showerror("Error", "Please enter at least one YouTube URL")
            return
            
        # Start processing in background thread
        thread = threading.Thread(target=self.process_urls, args=(urls,))
        thread.daemon = True
        thread.start()
        
    def process_urls(self, urls):
        """Process list of URLs"""
        output_dir = self.output_var.get()
        model = self.model_var.get()
        
        self.log_message(f"Starting extraction for {len(urls)} URL(s)...")
        
        for i, url in enumerate(urls, 1):
            self.log_message(f"Processing video {i}/{len(urls)}: {url[:50]}...")
            
            try:
                # Call the main extraction script
                cmd = [
                    sys.executable, '../src/youtube_to_text.py',
                    url, '--output', output_dir, '--model', model
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, 
                                      cwd='..', timeout=1800)  # 30 min timeout
                
                if result.returncode == 0:
                    self.log_message(f"✅ Completed: {url[:50]}")
                else:
                    self.log_message(f"❌ Failed: {url[:50]} - {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.log_message(f"⏰ Timeout: {url[:50]}")
            except Exception as e:
                self.log_message(f"❌ Error: {url[:50]} - {str(e)}")
                
        self.log_message("🎉 Extraction complete!")
        
    def find_bible_videos(self):
        """Search for Bible-related videos"""
        self.log_message("🔍 Searching for Bible contradiction videos...")
        
        thread = threading.Thread(target=self.search_bible_content)
        thread.daemon = True
        thread.start()
        
    def search_bible_content(self):
        """Search for Bible content"""
        try:
            cmd = [
                sys.executable, '../src/bible_content_analyzer.py',
                '--query', 'bible contradictions explained',
                '--max_videos', '5'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='..')
            
            if result.returncode == 0:
                self.log_message("✅ Found relevant Bible videos!")
                self.log_message(result.stdout)
            else:
                self.log_message(f"❌ Search failed: {result.stderr}")
                
        except Exception as e:
            self.log_message(f"❌ Search error: {str(e)}")
            
    def create_sample_urls(self):
        """Create sample URLs file"""
        sample_urls = """# Sample YouTube URLs for Bible contradictions
# Replace these with actual video URLs you want to process

https://www.youtube.com/watch?v=OA-4eQN16n0
https://www.youtube.com/watch?v=AsRti0nQqmg  
https://www.youtube.com/watch?v=KJ29Ik1m854

# Add your URLs below (one per line):
# https://www.youtube.com/watch?v=YOUR_VIDEO_ID
        """
        
        urls_file = Path("downloads/urls.txt")
        urls_file.parent.mkdir(exist_ok=True)
        
        with open(urls_file, 'w') as f:
            f.write(sample_urls)
            
        self.log_message("✅ Created sample urls.txt file in downloads folder")
        messagebox.showinfo("Success", "Sample URLs file created!\nEdit downloads/urls.txt with your video URLs.")
        
    def start_batch(self):
        """Start batch processing"""
        urls_file = Path("downloads/urls.txt")
        
        if not urls_file.exists():
            messagebox.showerror("Error", "urls.txt not found in downloads folder")
            return
            
        # Read URLs from file
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        if not urls:
            messagebox.showerror("Error", "No URLs found in urls.txt")
            return
            
        self.log_message("🚀 Starting batch processing...", tab="batch")
        
        thread = threading.Thread(target=self.process_urls, args=(urls,))
        thread.daemon = True
        thread.start()
        
    def open_downloads(self):
        """Open downloads folder"""
        downloads_path = Path("downloads").resolve()
        if downloads_path.exists():
            os.startfile(str(downloads_path))
        else:
            downloads_path.mkdir(exist_ok=True)
            os.startfile(str(downloads_path))
            
    def load_settings(self):
        """Load saved settings"""
        settings_file = Path("settings.json")
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.output_var.set(settings.get('output_dir', 'extracted_content'))
                    self.model_var.set(settings.get('model', 'base'))
            except:
                pass
                
    def save_settings(self):
        """Save current settings"""
        settings = {
            'output_dir': self.output_var.get(),
            'model': self.model_var.get()
        }
        
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

def main():
    root = tk.Tk()
    app = YouTubeTextExtractor(root)
    
    # Handle window closing
    def on_closing():
        app.save_settings()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
