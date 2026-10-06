#!/usr/bin/env python3

"""
🎬 COMPLETE YOUTUBE TO TEXT SETUP
Custom solution for downloading YouTube videos as MP3 and transcribing with free TTS
Created specifically for Bible study and contradiction analysis
"""

import os
import subprocess
import sys
from pathlib import Path

def print_banner():
    print("🎬 YOUTUBE TO TEXT - COMPLETE SETUP")
    print("=" * 60)
    print("📁 Custom solution by Cascade AI")
    print("🎯 Purpose: Download YouTube videos + Free Speech-to-Text")
    print("💰 Cost: 100% FREE (no API fees)")
    print("🔧 Features: Offline processing, batch support, high accuracy")
    print("=" * 60)

def check_setup():
    """Check what's already installed"""
    print("\n🔍 CHECKING SETUP...")
    
    # Check Python packages
    packages = {
        'yt-dlp': 'YouTube downloader',
        'whisper': 'Speech-to-text engine',
        'torch': 'AI framework',
        'torchaudio': 'Audio processing'
    }
    
    installed = {}
    for package, desc in packages.items():
        try:
            __import__(package)
            installed[package] = True
            print(f"✅ {package} - {desc}")
        except ImportError:
            installed[package] = False
            print(f"❌ {package} - {desc}")
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg - Video/audio processing")
        ffmpeg_installed = True
    except:
        print("❌ FFmpeg - Video/audio processing")
        ffmpeg_installed = False
    
    return all(installed.values()) and ffmpeg_installed

def install_missing():
    """Install missing components"""
    print("\n🔧 INSTALLING MISSING COMPONENTS...")
    
    # Install Python packages
    packages = ['yt-dlp', 'openai-whisper', 'torch', 'torchaudio']
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    # FFmpeg instructions
    print("\n🎥 FFMPEG SETUP REQUIRED:")
    print("FFmpeg is required for audio extraction.")
    print("\n📦 INSTALLATION OPTIONS:")
    print("1. Windows (Chocolatey): choco install ffmpeg")
    print("2. Windows (Scoop): scoop install ffmpeg") 
    print("3. Manual download: https://ffmpeg.org/download.html")
    print("4. Download ffmpeg.exe and add to PATH")
    
    return True

def create_desktop_shortcut():
    """Create desktop shortcuts for easy access"""
    try:
        desktop = Path.home() / "Desktop"
        script_dir = Path(__file__).parent
        
        # Create batch files for easy use
        shortcuts = {
            "Download & Transcribe.bat": f'@echo off\ncd /d "{script_dir}"\npython youtube_to_text.py %1\npause',
            "Find Bible Videos.bat": f'@echo off\ncd /d "{script_dir}"\npython bible_content_analyzer.py --query "%~1" --max_videos 5\npause',
            "Transcribe Audio.bat": f'@echo off\ncd /d "{script_dir}"\npython free_tts_transcriber.py transcribe %1\npause'
        }
        
        for filename, content in shortcuts.items():
            shortcut_path = desktop / filename
            with open(shortcut_path, 'w') as f:
                f.write(content)
            print(f"✅ Created: {filename}")
            
    except Exception as e:
        print(f"⚠️  Could not create desktop shortcuts: {e}")

def run_demo():
    """Run a quick demo"""
    print("\n🎬 RUNNING DEMO...")
    
    # Test with a short video about Bible topics
    demo_url = "https://www.youtube.com/watch?v=KJ29Ik1m854"  # Short Judas video
    
    print(f"📥 Downloading and transcribing: {demo_url}")
    
    try:
        result = subprocess.run([
            sys.executable, 'youtube_to_text.py', 
            demo_url, '--output', 'demo', '--model', 'tiny'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Demo completed successfully!")
            
            # Show transcript sample
            transcript_file = Path(__file__).parent / "demo" / "transcripts"
            if transcript_file.exists():
                files = list(transcript_file.glob("*.txt"))
                if files:
                    print(f"📄 Transcript saved: {files[0].name}")
                    with open(files[0], 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"📝 Sample: {content[:200]}...")
        else:
            print(f"❌ Demo failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Demo error: {e}")

def show_usage_examples():
    """Show usage examples"""
    print("\n📚 USAGE EXAMPLES:")
    print("=" * 50)
    
    print("\n1️⃣  FIND BIBLE CONTRADICTION VIDEOS:")
    print("   python bible_content_analyzer.py --query \"bible contradictions\" --max_videos 5")
    
    print("\n2️⃣  DOWNLOAD & TRANSCRIBE SINGLE VIDEO:")
    print("   python youtube_to_text.py \"YOUTUBE_URL\" --output bible_studies")
    
    print("\n3️⃣  PROCESS ENTIRE PLAYLIST:")
    print("   python youtube_to_text.py \"PLAYLIST_URL\" --playlist --max-videos 10")
    
    print("\n4️⃣  JUST DOWNLOAD MP3s:")
    print("   python youtube_mp3_downloader.py \"YOUTUBE_URL\"")
    
    print("\n5️⃣  TRANSCRIBE EXISTING AUDIO:")
    print("   python free_tts_transcriber.py transcribe audio_file.mp3")
    
    print("\n6️⃣  BATCH PROCESS FOLDER:")
    print("   python free_tts_transcriber.py batch downloads/ --model base")

def main():
    print_banner()
    
    # Check current setup
    if check_setup():
        print("\n🎉 EVERYTHING IS ALREADY SET UP!")
        run_demo()
    else:
        print("\n⚠️  SOME COMPONENTS MISSING")
        if install_missing():
            print("\n✅ INSTALLATION COMPLETE!")
            print("📝 Please install FFmpeg manually, then run this again")
        else:
            print("\n❌ INSTALLATION FAILED")
            return
    
    # Create desktop shortcuts
    create_desktop_shortcut()
    
    # Show usage examples
    show_usage_examples()
    
    print("\n🎯 SETUP COMPLETE!")
    print("📁 All files are in this folder")
    print("🎬 Ready to download and transcribe YouTube videos!")
    print("💰 100% FREE - No API costs or limits")

if __name__ == "__main__":
    main()
