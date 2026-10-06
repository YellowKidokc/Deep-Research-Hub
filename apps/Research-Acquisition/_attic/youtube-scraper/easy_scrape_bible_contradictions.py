"""
YouTube Transcript Scraper - Bible Contradiction Channels
Christian apologists and critical content about Bible contradictions
"""

import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

# Bible Contradiction Channels - Christian Apologists & Critical Content
CHANNELS = [
    # NEW CHANNELS - Process these first with ALL videos
    "TruthisChrist",
    "AnswersInGenesis",
    "MikeWinger",
    "DanPaterson",
    "BibleNerdMinistries",
    "LivingWaters",
    
    # Critical/Skeptical Content
    "HolyKoolaid",
]

MAX_VIDEOS_PER_CHANNEL = None  # Download ALL videos from each channel
RESULTS_DIR = "transcripts_bible_contradictions"

def main():
    print("=" * 60)
    print("YouTube Channel Transcript Scraper")
    print("Bible Contradiction Channels")
    print("=" * 60)
    
    if not CHANNELS:
        print("\n⚠️  No channels specified!")
        print("Edit the CHANNELS list in this file and add channel names.")
        print("\nExample:")
        print('CHANNELS = ["AnswersInGenesis", "MikeWinger"]')
        sys.exit(1)
    
    api_key = os.getenv("YTB_API_KEY")
    if not api_key or api_key == "your-youtube-api-key-here":
        print("\n⚠️  YouTube API key not configured!")
        print("Please add your API key to the .env file:")
        print("YTB_API_KEY=your-actual-api-key")
        sys.exit(1)
    
    print(f"\n📋 Channels to scrape: {len(CHANNELS)}")
    for i, channel in enumerate(CHANNELS, 1):
        print(f"   {i}. @{channel}")
    
    print(f"\n📁 Output directory: {RESULTS_DIR}/")
    if MAX_VIDEOS_PER_CHANNEL:
        print(f"🎬 Max videos per channel: {MAX_VIDEOS_PER_CHANNEL}")
    else:
        print(f"🎬 Max videos per channel: ALL")
    
    print("\n" + "=" * 60)
    
    for i, channel in enumerate(CHANNELS, 1):
        print(f"\n[{i}/{len(CHANNELS)}] Processing @{channel}...")
        print("-" * 60)
        
        cmd = [
            sys.executable,
            "ytb_scraper.py",
            "--channel_name", channel,
            "--results_dir", RESULTS_DIR
        ]
        
        if MAX_VIDEOS_PER_CHANNEL:
            cmd.extend(["--max_videos", str(MAX_VIDEOS_PER_CHANNEL)])
        
        try:
            result = subprocess.run(cmd, check=True)
            print(f"✅ Completed @{channel}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to process @{channel}")
            print(f"   Error: {e}")
            continue
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All channels processed!")
    print(f"📁 Transcripts saved to: {os.path.abspath(RESULTS_DIR)}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
