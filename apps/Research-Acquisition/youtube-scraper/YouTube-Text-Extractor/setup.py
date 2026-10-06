#!/usr/bin/env python3
"""
Setup script for YouTube Text Extractor
"""

import os
import sys
import subprocess
import urllib.request
from pathlib import Path

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     🎬 YOUTUBE TEXT EXTRACTOR - SETUP WIZARD                ║
    ║                                                              ║
    ║     Professional YouTube Video Downloader & Text Extractor   ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required packages"""
    print("\n🔧 Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  FFmpeg is not installed")
        return False

def show_ffmpeg_instructions():
    """Show FFmpeg installation instructions"""
    print("\n📥 FFMPEG INSTALLATION REQUIRED")
    print("FFmpeg is required for audio extraction from videos.")
    print("\n📦 INSTALLATION OPTIONS:")
    print("1. Windows (Chocolatey - Recommended):")
    print("   choco install ffmpeg")
    print("\n2. Windows (Scoop):")
    print("   scoop install ffmpeg")
    print("\n3. Manual Download:")
    print("   • Download from: https://ffmpeg.org/download.html")
    print("   • Extract ffmpeg.exe to your PATH")
    print("   • Or add to System Environment Variables")
    print("\n4. Quick Install (Windows):")
    print("   • Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z")
    print("   • Extract and add bin folder to PATH")

def create_directories():
    """Create necessary directories"""
    directories = ["downloads", "transcripts", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")

def create_desktop_shortcut():
    """Create desktop shortcut"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "YouTube Text Extractor.lnk")
        target = os.path.join(os.getcwd(), "START.bat")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print("✅ Desktop shortcut created")
        return True
    except ImportError:
        print("⚠️  Could not create desktop shortcut (pywin32 not installed)")
        return False
    except Exception as e:
        print(f"⚠️  Could not create desktop shortcut: {e}")
        return False

def test_installation():
    """Test if everything works"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        import yt_dlp
        import whisper
        import torch
        print("✅ All Python packages imported successfully")
        
        # Test basic functionality
        print("✅ Installation test passed")
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    print_banner()
    
    # Check Python
    if not check_python():
        input("Press Enter to exit...")
        return False
    
    # Install dependencies
    if not install_dependencies():
        input("Press Enter to exit...")
        return False
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        show_ffmpeg_instructions()
    
    # Create directories
    create_directories()
    
    # Create desktop shortcut
    create_desktop_shortcut()
    
    # Test installation
    if test_installation():
        print("\n🎉 SETUP COMPLETE!")
        print("\n🚀 NEXT STEPS:")
        print("1. Install FFmpeg if not already installed")
        print("2. Double-click 'START.bat' to launch the application")
        print("3. Or run: python src/gui_interface.py")
        print("\n📁 Your folders are ready:")
        print("   • downloads/ - MP3 files will be saved here")
        print("   • transcripts/ - Text files will be saved here")
        print("\n💡 TIP: Start with the GUI interface for the best experience!")
        
        if not ffmpeg_ok:
            print("\n⚠️  REMINDER: Install FFmpeg for full functionality")
        
        input("\nPress Enter to exit...")
        return True
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        input("Press Enter to exit...")
        return False

if __name__ == "__main__":
    main()
