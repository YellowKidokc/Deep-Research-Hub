#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing required dependencies...")
    
    packages = [
        'yt-dlp',           # YouTube downloader
        'openai-whisper',   # Speech-to-text
        'torch',            # PyTorch for Whisper
        'torchaudio'        # Audio processing
    ]
    
    for package in packages:
        print(f"📦 Installing {package}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_and_transcribe(video_url, output_dir="bible_videos", model_size="base"):
    """
    Complete workflow: Download YouTube video as MP3 and transcribe it
    """
    
    print("🎬 YOUTUBE TO TEXT WORKFLOW")
    print("=" * 50)
    
    # Create directories
    audio_dir = os.path.join(output_dir, "audio")
    transcript_dir = os.path.join(output_dir, "transcripts")
    
    Path(audio_dir).mkdir(parents=True, exist_ok=True)
    Path(transcript_dir).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download audio
    print("\n📥 STEP 1: Downloading audio...")
    
    output_template = os.path.join(audio_dir, "%(title)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        '-x',  # Extract audio
        '--audio-format', 'mp3',
        '--audio-quality', 'best',
        '-o', output_template,
        '--no-playlist',
        '--embed-thumbnail',
        '--embed-metadata',
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Find downloaded file
        audio_file = None
        for file in Path(audio_dir).glob("*.mp3"):
            audio_file = str(file)
            break
        
        if not audio_file:
            print("❌ Download completed but file not found")
            return None
        
        print(f"✅ Downloaded: {os.path.basename(audio_file)}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        return None
    
    # Step 2: Transcribe audio
    print(f"\n📝 STEP 2: Transcribing with Whisper ({model_size} model)...")
    
    try:
        import whisper
    except ImportError:
        print("❌ Whisper not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper'], check=True)
        import whisper
    
    try:
        model = whisper.load_model(model_size)
        print(f"✅ Whisper model loaded")
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        return None
    
    try:
        result = model.transcribe(audio_file)
        
        # Save transcript
        audio_name = Path(audio_file).stem
        transcript_file = os.path.join(transcript_dir, f"{audio_name}.txt")
        
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(result["text"])
        
        print(f"✅ Transcription complete!")
        print(f"   📄 Transcript saved to: {transcript_file}")
        print(f"   ⏱️  Duration: {result.get('segments', [])[-1].get('end', 0):.1f}s" if result.get('segments') else "")
        print(f"   🌐 Language detected: {result.get('language', 'unknown')}")
        print(f"   📊 Word count: {len(result['text'].split())}")
        
        return transcript_file
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None

def process_playlist(playlist_url, output_dir="bible_playlist", max_videos=5, model_size="base"):
    """
    Download and transcribe multiple videos from a playlist
    """
    
    print(f"🎬 PLAYLIST PROCESSING WORKFLOW")
    print("=" * 50)
    
    # Create directories
    audio_dir = os.path.join(output_dir, "audio")
    transcript_dir = os.path.join(output_dir, "transcripts")
    
    Path(audio_dir).mkdir(parents=True, exist_ok=True)
    Path(transcript_dir).mkdir(parents=True, exist_ok=True)
    
    # Get playlist info first
    print(f"\n📋 Getting playlist information...")
    
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--print', '%(title)s - %(url)s',
        playlist_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        video_lines = result.stdout.strip().split('\n')
        
        if max_videos:
            video_lines = video_lines[:max_videos]
        
        print(f"📊 Found {len(video_lines)} videos to process")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get playlist info: {e}")
        return
    
    # Process each video
    success_count = 0
    
    for i, line in enumerate(video_lines, 1):
        if ' - ' not in line:
            continue
            
        title, url = line.rsplit(' - ', 1)
        
        print(f"\n{'='*60}")
        print(f"📺 Processing video {i}/{len(video_lines)}")
        print(f"🎬 {title}")
        
        # Download and transcribe this video
        transcript_file = download_and_transcribe(url, output_dir, model_size)
        
        if transcript_file:
            success_count += 1
            print(f"✅ Completed: {os.path.basename(transcript_file)}")
        else:
            print(f"❌ Failed: {title}")
    
    print(f"\n{'='*60}")
    print(f"📊 PLAYLIST PROCESSING SUMMARY:")
    print(f"   ✅ Successfully processed: {success_count}/{len(video_lines)} videos")
    print(f"   📁 Output directory: {output_dir}")
    print(f"   📄 Transcripts: {transcript_dir}")
    print(f"   🎵 Audio files: {audio_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Complete YouTube to Text workflow")
    
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument("--output", "-o", default="bible_videos", help="Output directory")
    parser.add_argument("--model", "-m", choices=['tiny', 'base', 'small', 'medium', 'large'],
                       default='base', help="Whisper model size (base=good balance)")
    parser.add_argument("--playlist", action="store_true", help="Process as playlist")
    parser.add_argument("--max-videos", type=int, default=5, help="Max videos from playlist")
    parser.add_argument("--install", action="store_true", help="Install dependencies first")
    
    args = parser.parse_args()
    
    if args.install:
        print("🔧 Installing dependencies...")
        if install_dependencies():
            print("✅ All dependencies installed successfully!")
        else:
            print("❌ Some dependencies failed to install")
            sys.exit(1)
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("❌ FFmpeg is required but not installed.")
        print("Please install FFmpeg first:")
        print("  Windows: choco install ffmpeg")
        print("  Or download from: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    if args.playlist or "playlist" in args.url.lower():
        process_playlist(args.url, args.output, args.max_videos, args.model)
    else:
        download_and_transcribe(args.url, args.output, args.model)
