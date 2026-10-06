#!/usr/bin/env python3

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
import concurrent.futures
from tqdm import tqdm

class FastVideoTranscriber:
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        self.output_dir = Path("transcripts")
        self.output_dir.mkdir(exist_ok=True)
        
    def check_dependencies(self):
        """Check if required tools are installed"""
        print("🔍 Checking dependencies...")
        
        try:
            import whisper
            print("✅ Whisper installed")
        except ImportError:
            print("❌ Whisper not installed. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper'], check=True)
            import whisper
            
        try:
            import torch
            print("✅ PyTorch installed")
        except ImportError:
            print("❌ PyTorch not installed. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch'], check=True)
            
        print("✅ All dependencies ready!")
        
    def get_video_files(self, directory):
        """Get all video files from directory"""
        video_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            print(f"❌ Directory not found: {directory}")
            return []
            
        print(f"🔍 Scanning {directory} for video files...")
        
        for ext in self.supported_formats:
            video_files.extend(directory_path.glob(f"*{ext}"))
            
        print(f"📁 Found {len(video_files)} video files")
        return sorted(video_files)
    
    def transcribe_single_video(self, video_path, model_size="tiny"):
        """Transcribe a single video file"""
        try:
            import whisper
        except ImportError:
            print("❌ Whisper not available")
            return None
            
        try:
            # Load model (use tiny for speed)
            print(f"🎙️ Loading {model_size} model...")
            model = whisper.load_model(model_size)
            
            # Transcribe video
            print(f"📝 Transcribing: {video_path.name}")
            result = model.transcribe(str(video_path))
            
            # Save transcript
            output_file = self.output_dir / f"{video_path.stem}_transcript.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"VIDEO: {video_path.name}\n")
                f.write(f"TRANSCRIPT:\n")
                f.write("=" * 50 + "\n")
                f.write(result['text'])
                f.write(f"\n\nDURATION: {result.get('segments', [])[-1].get('end', 0):.1f} seconds")
                f.write(f"\nLANGUAGE: {result.get('language', 'unknown')}")
                f.write(f"\nWORD COUNT: {len(result['text'].split())}")
            
            print(f"✅ Completed: {video_path.name}")
            return output_file
            
        except Exception as e:
            print(f"❌ Failed to transcribe {video_path.name}: {e}")
            return None
    
    def transcribe_batch_fast(self, video_files, model_size="tiny", max_workers=2):
        """Transcribe multiple videos in parallel for maximum speed"""
        print(f"🚀 Starting FAST batch transcription with {max_workers} workers")
        print(f"📊 Processing {len(video_files)} files with {model_size} model")
        print(f"⚡ Estimated time: {len(video_files) * 30} seconds (very fast!)")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_video = {
                executor.submit(self.transcribe_single_video, video, model_size): video 
                for video in video_files
            }
            
            # Progress bar
            with tqdm(total=len(video_files), desc="🎬 Transcribing", unit="video") as pbar:
                for future in concurrent.futures.as_completed(future_to_video):
                    video = future_to_video[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        print(f"❌ Error with {video.name}: {e}")
                    pbar.update(1)
        
        return results
    
    def transcribe_batch_sequential(self, video_files, model_size="tiny"):
        """Transcribe videos one by one (more stable)"""
        print(f"📝 Starting sequential transcription with {model_size} model")
        
        results = []
        
        for i, video in enumerate(tqdm(video_files, desc="🎬 Transcribing", unit="video")):
            print(f"\n📊 Video {i+1}/{len(video_files)}: {video.name}")
            result = self.transcribe_single_video(video, model_size)
            if result:
                results.append(result)
                
        return results
    
    def create_summary_report(self, results):
        """Create a summary report of all transcriptions"""
        report_file = self.output_dir / "TRANSCRIPTION_SUMMARY.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🎬 VIDEO TRANSCRIPTION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total videos processed: {len(results)}\n")
            f.write(f"Processing date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output directory: {self.output_dir}\n\n")
            f.write("📋 TRANSCRIBED FILES:\n")
            f.write("-" * 40 + "\n")
            
            for result in results:
                if result and result.exists():
                    # Get file info
                    stat = result.stat()
                    size_kb = stat.st_size / 1024
                    
                    # Read first line to get video name
                    with open(result, 'r', encoding='utf-8') as transcript:
                        first_line = transcript.readline().strip()
                    
                    f.write(f"📄 {result.name}\n")
                    f.write(f"   {first_line}\n")
                    f.write(f"   Size: {size_kb:.1f} KB\n")
                    f.write(f"   Created: {time.ctime(stat.st_mtime)}\n\n")
        
        print(f"📊 Summary report saved: {report_file}")

def main():
    print("🚀 LIGHTNING FAST VIDEO TRANSCRIBER")
    print("=" * 50)
    
    transcriber = FastVideoTranscriber()
    
    # Check dependencies
    transcriber.check_dependencies()
    
    # Get video directory
    video_dir = input("📁 Enter video directory path (or press Enter for default): ").strip()
    if not video_dir:
        video_dir = "C:\\Users\\lowes\\Videos\\4K Tokkit\\ppe_clips"
    
    # Get video files
    video_files = transcriber.get_video_files(video_dir)
    
    if not video_files:
        print("❌ No video files found!")
        return
    
    # Choose processing mode
    print(f"\n⚡ PROCESSING OPTIONS:")
    print("1. 🚀 ULTRA FAST (Parallel, 2 workers) - Recommended")
    print("2. 📝 FAST (Sequential) - More stable")
    print("3. 🎯 HIGH QUALITY (Sequential, small model)")
    
    choice = input("Choose mode (1-3): ").strip()
    
    if choice == "1":
        print("\n🚀 ULTRA FAST MODE - Maximum speed!")
        results = transcriber.transcribe_batch_fast(video_files, model_size="tiny", max_workers=2)
    elif choice == "2":
        print("\n📝 FAST MODE - Good balance")
        results = transcriber.transcribe_batch_sequential(video_files, model_size="tiny")
    elif choice == "3":
        print("\n🎯 HIGH QUALITY MODE - Better accuracy")
        results = transcriber.transcribe_batch_sequential(video_files, model_size="small")
    else:
        print("\n🚀 Defaulting to ULTRA FAST mode")
        results = transcriber.transcribe_batch_fast(video_files, model_size="tiny", max_workers=2)
    
    # Create summary
    transcriber.create_summary_report(results)
    
    print(f"\n🎉 TRANSCRIPTION COMPLETE!")
    print(f"📊 Successfully processed: {len(results)}/{len(video_files)} videos")
    print(f"📁 All transcripts saved to: {transcriber.output_dir}")
    print(f"📋 Summary report: {transcriber.output_dir}/TRANSCRIPTION_SUMMARY.txt")

if __name__ == "__main__":
    main()
