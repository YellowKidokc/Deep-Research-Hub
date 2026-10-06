#!/usr/bin/env python3

"""
INSTANT TIKTOK TRANSCRIBER - Process your 80+ videos immediately
"""

import os
import sys
from pathlib import Path

def instant_transcribe():
    """Start transcribing your TikTok videos immediately"""
    
    video_dir = Path(r"C:\Users\lowes\Videos\4K Tokkit\ppe_clips")
    
    if not video_dir.exists():
        print(f"❌ Directory not found: {video_dir}")
        return
    
    # Count videos
    video_files = list(video_dir.glob("*.mp4"))
    print(f"🎬 Found {len(video_files)} TikTok videos")
    print(f"📁 Directory: {video_dir}")
    print()
    
    if len(video_files) == 0:
        print("❌ No MP4 files found!")
        return
    
    print("⚡ STARTING ULTRA FAST TRANSCRIPTION...")
    print("🚀 Using Tiny model for maximum speed")
    print("📊 Processing in parallel for best performance")
    print()
    
    # Import and run the transcriber
    try:
        from fast_video_transcriber import FastVideoTranscriber
        
        transcriber = FastVideoTranscriber()
        
        # Quick dependency check
        transcriber.check_dependencies()
        
        # Start ultra fast processing
        print("🎙️ Loading AI model...")
        results = transcriber.transcribe_batch_fast(
            video_files, 
            model_size="tiny", 
            max_workers=2
        )
        
        # Create summary
        transcriber.create_summary_report(results)
        
        print()
        print("🎉 ALL DONE!")
        print(f"📊 Successfully processed: {len(results)}/{len(video_files)} videos")
        print(f"📁 Transcripts saved to: ./transcripts/")
        print(f"📋 Summary: ./transcripts/TRANSCRIPTION_SUMMARY.txt")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try running the setup first: python setup.py")

if __name__ == "__main__":
    print("⚡ INSTANT TIKTOK TRANSCRIBER")
    print("=" * 40)
    instant_transcribe()
    input("\nPress Enter to exit...")
