#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_ffmpeg():
    """Instructions for installing ffmpeg"""
    print("❌ FFmpeg is not installed. Please install it first:")
    print("\n📦 INSTALLATION OPTIONS:")
    print("1. Windows (Chocolatey): choco install ffmpeg")
    print("2. Windows (Scoop): scoop install ffmpeg")
    print("3. Download manually: https://ffmpeg.org/download.html")
    print("4. Windows: Add ffmpeg.exe to your PATH or place in same folder")
    print("\n⏳ After installation, run this script again.")
    return False

def download_youtube_audio(video_url, output_dir="downloads", quality="best"):
    """
    Download audio from YouTube video using yt-dlp
    
    Args:
        video_url: YouTube video URL
        output_dir: Directory to save downloads
        quality: Audio quality (best, worst, or specific bitrate like 128)
    
    Returns:
        Path to downloaded file or None if failed
    """
    
    # Check if yt-dlp is available
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ yt-dlp not found. Installing...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], check=True)
            print("✅ yt-dlp installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install yt-dlp. Please install manually:")
            print("   pip install yt-dlp")
            return None
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Prepare yt-dlp command
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        '-x',  # Extract audio
        '--audio-format', 'mp3',
        '--audio-quality', quality,
        '-o', output_template,
        '--no-playlist',  # Download single video only
        '--embed-thumbnail',  # Add thumbnail if available
        '--embed-metadata',  # Add metadata
        video_url
    ]
    
    print(f"🎬 Downloading audio from: {video_url}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎵 Quality: {quality}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Extract filename from output
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if '[ExtractAudio]' in line and 'Destination:' in line:
                filename = line.split('Destination: ')[1].strip()
                if os.path.exists(filename):
                    print(f"✅ Downloaded successfully: {os.path.basename(filename)}")
                    return filename
        
        # Alternative method to find the downloaded file
        print("🔍 Searching for downloaded file...")
        for file in Path(output_dir).glob("*.mp3"):
            print(f"✅ Found: {file.name}")
            return str(file)
        
        print("⚠️  Download completed but file not found in expected location")
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def download_playlist_audio(playlist_url, output_dir="downloads", quality="best", max_videos=None):
    """
    Download audio from entire YouTube playlist
    
    Args:
        playlist_url: YouTube playlist URL
        output_dir: Directory to save downloads
        quality: Audio quality
        max_videos: Maximum number of videos to download (None for all)
    """
    
    # Check if yt-dlp is available
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ yt-dlp not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp'], check=True)
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    # Prepare yt-dlp command for playlist
    output_template = os.path.join(output_dir, "%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        '-x',  # Extract audio
        '--audio-format', 'mp3',
        '--audio-quality', quality,
        '-o', output_template,
        '--embed-thumbnail',
        '--embed-metadata',
    ]
    
    if max_videos:
        cmd.extend(['--playlist-end', str(max_videos)])
    
    cmd.append(playlist_url)
    
    print(f"🎬 Downloading playlist: {playlist_url}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎵 Quality: {quality}")
    if max_videos:
        print(f"📊 Max videos: {max_videos}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Playlist download completed!")
        
        # Count downloaded files
        mp3_count = len(list(Path(output_dir).rglob("*.mp3")))
        print(f"📊 Downloaded {mp3_count} MP3 files")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Playlist download failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube videos as MP3 audio")
    
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument("--output", "-o", help="Output directory", default="downloads")
    parser.add_argument("--quality", "-q", help="Audio quality (best, worst, or bitrate like 128)", 
                       default="best")
    parser.add_argument("--playlist", action="store_true", help="Treat URL as playlist")
    parser.add_argument("--max-videos", type=int, help="Maximum videos to download from playlist")
    
    args = parser.parse_args()
    
    # Check FFmpeg
    if not check_ffmpeg():
        install_ffmpeg()
        sys.exit(1)
    
    print("🎵 YouTube MP3 Downloader")
    print("=" * 50)
    
    if args.playlist or "playlist" in args.url.lower():
        download_playlist_audio(
            args.url, 
            args.output, 
            args.quality, 
            args.max_videos
        )
    else:
        download_youtube_audio(
            args.url, 
            args.output, 
            args.quality
        )
