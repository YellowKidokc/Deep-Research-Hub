#!/usr/bin/env python3
"""
THEOPHYSICS COHERENCE FRAMEWORK
Simple GUI Button for One-Click Analysis

Double-click this file to open a simple window with a big button!
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
from pathlib import Path
import sys
import webbrowser

class TheophysicsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Theophysics Coherence Framework")
        self.root.geometry("700x500")
        self.root.configure(bg='#1a1a2e')
        
        # Header
        header = tk.Label(
            root,
            text="THEOPHYSICS COHERENCE FRAMEWORK",
            font=('Arial', 18, 'bold'),
            bg='#1a1a2e',
            fg='#ffd700'
        )
        header.pack(pady=20)
        
        subtitle = tk.Label(
            root,
            text="Automated Scoring & Visualization Pipeline",
            font=('Arial', 12),
            bg='#1a1a2e',
            fg='#a0a0a0'
        )
        subtitle.pack()
        
        # Options Frame
        options_frame = tk.Frame(root, bg='#1a1a2e')
        options_frame.pack(pady=10)
        
        self.skip_scoring_var = tk.BooleanVar(value=False)
        skip_check = tk.Checkbutton(
            options_frame,
            text="Skip scoring (use existing data)",
            variable=self.skip_scoring_var,
            bg='#1a1a2e',
            fg='#e0e0e0',
            selectcolor='#2a2a3e',
            activebackground='#1a1a2e',
            activeforeground='#ffd700',
            font=('Arial', 10)
        )
        skip_check.pack()
        
        # Main Button
        self.run_button = tk.Button(
            root,
            text="🚀 SCORE & VISUALIZE",
            command=self.run_analysis,
            font=('Arial', 16, 'bold'),
            bg='#ffd700',
            fg='#000000',
            activebackground='#ffed4e',
            relief=tk.RAISED,
            bd=3,
            padx=30,
            pady=15,
            cursor='hand2'
        )
        self.run_button.pack(pady=20)
        
        # Progress Label
        self.status_label = tk.Label(
            root,
            text="Ready to analyze 159 documents across 4 categories",
            font=('Arial', 10),
            bg='#1a1a2e',
            fg='#a0a0a0'
        )
        self.status_label.pack(pady=5)
        
        # Output Console
        console_label = tk.Label(
            root,
            text="Output:",
            font=('Arial', 10, 'bold'),
            bg='#1a1a2e',
            fg='#ffd700',
            anchor='w'
        )
        console_label.pack(fill=tk.X, padx=20)
        
        self.output_text = scrolledtext.ScrolledText(
            root,
            height=12,
            bg='#0a0a0a',
            fg='#00ff00',
            font=('Courier', 9),
            insertbackground='#ffd700'
        )
        self.output_text.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        
        # Button Frame
        button_frame = tk.Frame(root, bg='#1a1a2e')
        button_frame.pack(pady=10)
        
        self.open_html_button = tk.Button(
            button_frame,
            text="Open Dashboard",
            command=self.open_dashboard,
            font=('Arial', 10),
            bg='#2a2a3e',
            fg='#ffd700',
            state=tk.DISABLED
        )
        self.open_html_button.pack(side=tk.LEFT, padx=5)
        
        self.open_excel_button = tk.Button(
            button_frame,
            text="Open Excel",
            command=self.open_excel,
            font=('Arial', 10),
            bg='#2a2a3e',
            fg='#ffd700',
            state=tk.DISABLED
        )
        self.open_excel_button.pack(side=tk.LEFT, padx=5)
        
        self.script_dir = Path(__file__).parent
        self.dashboard_path = self.script_dir / "outputs" / "dashboard" / "coherence_dashboard.html"
        self.excel_path = self.script_dir / "outputs" / "dashboard" / "coherence_analysis_with_charts.xlsx"
        
    def log(self, message):
        """Add message to output console"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
    
    def run_analysis(self):
        """Run the analysis in a background thread"""
        self.run_button.config(state=tk.DISABLED, text="RUNNING...")
        self.status_label.config(text="Analysis in progress...", fg='#ffd700')
        self.output_text.delete(1.0, tk.END)
        self.open_html_button.config(state=tk.DISABLED)
        self.open_excel_button.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._run_analysis_thread)
        thread.daemon = True
        thread.start()
    
    def _run_analysis_thread(self):
        """Background thread for running analysis"""
        try:
            script_path = self.script_dir / "SCORE_AND_VISUALIZE.py"
            
            args = [sys.executable, str(script_path), "--no-browser"]
            if self.skip_scoring_var.get():
                args.append("--skip-scoring")
            
            self.log("="*70)
            self.log("THEOPHYSICS COHERENCE FRAMEWORK")
            self.log("="*70)
            self.log("")
            
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            for line in process.stdout:
                # Strip ANSI color codes for clean display
                clean_line = line.strip()
                if clean_line:
                    self.log(clean_line)
            
            process.wait()
            
            if process.returncode == 0:
                self.log("")
                self.log("="*70)
                self.log("SUCCESS! Analysis complete.")
                self.log("="*70)
                self.status_label.config(text="✓ Analysis complete! Files are ready.", fg='#00ff00')
                self.open_html_button.config(state=tk.NORMAL)
                self.open_excel_button.config(state=tk.NORMAL)
                
                # Auto-open dashboard
                if self.dashboard_path.exists():
                    self.open_dashboard()
            else:
                self.log("")
                self.log("ERROR: Analysis failed. Check output above.")
                self.status_label.config(text="✗ Analysis failed", fg='#ff0000')
                
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.status_label.config(text="✗ Error occurred", fg='#ff0000')
        
        finally:
            self.run_button.config(state=tk.NORMAL, text="🚀 SCORE & VISUALIZE")
    
    def open_dashboard(self):
        """Open HTML dashboard in browser"""
        if self.dashboard_path.exists():
            webbrowser.open(str(self.dashboard_path))
            self.log(f"Opening dashboard: {self.dashboard_path}")
        else:
            self.log("ERROR: Dashboard file not found!")
    
    def open_excel(self):
        """Open Excel file"""
        if self.excel_path.exists():
            import os
            os.startfile(str(self.excel_path))
            self.log(f"Opening Excel: {self.excel_path}")
        else:
            self.log("ERROR: Excel file not found!")

def main():
    root = tk.Tk()
    app = TheophysicsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
