#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path

def check_whisper():
    """Check if OpenAI Whisper is available"""
    try:
        import whisper
        return True
    except ImportError:
        return False

def install_whisper():
    """Install OpenAI Whisper"""
    print("🔧 Installing OpenAI Whisper...")
    try:
        # Install whisper
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper'], check=True)
        
        # Install torch (for CPU usage)
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'torch', 'torchaudio'], check=True)
        
        print("✅ Whisper installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Whisper: {e}")
        return False

def transcribe_with_whisper(audio_file, model_size="base", output_dir="transcripts"):
    """
    Transcribe audio file using OpenAI Whisper
    
    Args:
        audio_file: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        output_dir: Directory to save transcripts
    
    Returns:
        Path to transcript file or None if failed
    """
    
    if not check_whisper():
        if not install_whisper():
            return None
    
    try:
        import whisper
    except ImportError:
        print("❌ Whisper not available")
        return None
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"🎙️  Loading Whisper model: {model_size}")
    try:
        model = whisper.load_model(model_size)
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return None
    
    print(f"📝 Transcribing: {os.path.basename(audio_file)}")
    
    try:
        result = model.transcribe(audio_file)
        
        # Save transcript
        audio_name = Path(audio_file).stem
        transcript_file = os.path.join(output_dir, f"{audio_name}_transcript.txt")
        json_file = os.path.join(output_dir, f"{audio_name}_transcript.json")
        
        # Save plain text
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(result["text"])
        
        # Save detailed JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Transcription saved!")
        print(f"   📄 Text: {transcript_file}")
        print(f"   📊 JSON: {json_file}")
        print(f"   ⏱️  Duration: {result.get('segments', [])[-1].get('end', 0):.1f}s" if result.get('segments') else "")
        print(f"   🌐 Language: {result.get('language', 'unknown')}")
        
        return transcript_file
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None

def batch_transcribe_directory(audio_dir, output_dir="transcripts", model_size="base", file_pattern="*.mp3"):
    """
    Transcribe all audio files in a directory
    
    Args:
        audio_dir: Directory containing audio files
        output_dir: Directory to save transcripts
        model_size: Whisper model size
        file_pattern: File pattern to match (e.g., "*.mp3", "*.wav")
    """
    
    audio_path = Path(audio_dir)
    if not audio_path.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return
    
    audio_files = list(audio_path.rglob(file_pattern))
    
    if not audio_files:
        print(f"❌ No {file_pattern} files found in {audio_dir}")
        return
    
    print(f"📁 Found {len(audio_files)} audio files")
    
    success_count = 0
    failed_count = 0
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n{'='*60}")
        print(f"📊 Processing file {i}/{len(audio_files)}")
        
        result = transcribe_with_whisper(str(audio_file), model_size, output_dir)
        
        if result:
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 BATCH TRANSCRIPTION SUMMARY:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📈 Success rate: {success_count/len(audio_files)*100:.1f}%")

def show_free_tts_options():
    """Display free TTS/Speech-to-Text options"""
    
    print("🎙️  FREE SPEECH-TO-TEXT OPTIONS")
    print("=" * 60)
    
    print("\n1️⃣  OPENAI WHISPER (Recommended - Offline)")
    print("   🌟 Features:")
    print("      • Completely free and offline")
    print("      • High accuracy (99%+ for clear audio)")
    print("      • Multiple languages")
    print("      • Different model sizes")
    print("   📊 Model Options:")
    print("      • tiny:   ~32MB,  ~10x faster,  ~85% accuracy")
    print("      • base:   ~142MB, ~6x faster,   ~90% accuracy")
    print("      • small:  ~466MB, ~2x faster,   ~94% accuracy")
    print("      • medium: ~1.5GB, normal speed, ~96% accuracy")
    print("      • large:  ~2.9GB, slower,       ~98% accuracy")
    print("   💻 Installation: pip install openai-whisper torch")
    
    print("\n2️⃣  GOOGLE SPEECH-TO-TEXT API")
    print("   🌟 Features:")
    print("      • Very high accuracy")
    print("      • Real-time processing")
    print("      • 60 minutes free per month")
    print("   💰 Cost: Free tier, then $0.006 per 15 seconds")
    print("   🔧 Setup: Requires Google Cloud account")
    
    print("\n3️⃣  AZURE SPEECH SERVICES")
    print("   🌟 Features:")
    print("      • High accuracy")
    print("      • 5 hours free per month")
    print("      • Multiple languages")
    print("   💰 Cost: Free tier, then $1 per hour")
    print("   🔧 Setup: Requires Azure account")
    
    print("\n4️⃣  ASSEMBLYAI")
    print("   🌟 Features:")
    print("      • Very accurate")
    print("      • Speaker diarization")
    print("      • 3 hours free per month")
    print("   💰 Cost: Free tier, then $0.00015 per second")
    
    print("\n5️⃣  VOSK (Offline)")
    print("   🌟 Features:")
    print("      • Completely free and offline")
    print("      • Lightweight")
    print("      • Multiple languages")
    print("   ⚠️  Less accurate than Whisper")
    
    print("\n🏆 RECOMMENDATION:")
    print("   Use OpenAI Whisper for best free offline solution")
    print("   Start with 'base' model, upgrade to 'small' if needed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Free Speech-to-Text transcription using Whisper")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Transcribe single file
    single_parser = subparsers.add_parser('transcribe', help='Transcribe single audio file')
    single_parser.add_argument('audio_file', help='Path to audio file')
    single_parser.add_argument('--model', '-m', choices=['tiny', 'base', 'small', 'medium', 'large'],
                              default='base', help='Whisper model size')
    single_parser.add_argument('--output', '-o', default='transcripts', help='Output directory')
    
    # Batch transcribe directory
    batch_parser = subparsers.add_parser('batch', help='Transcribe all files in directory')
    batch_parser.add_argument('audio_dir', help='Directory containing audio files')
    batch_parser.add_argument('--model', '-m', choices=['tiny', 'base', 'small', 'medium', 'large'],
                              default='base', help='Whisper model size')
    batch_parser.add_argument('--output', '-o', default='transcripts', help='Output directory')
    batch_parser.add_argument('--pattern', '-p', default='*.mp3', help='File pattern to match')
    
    # Show options
    options_parser = subparsers.add_parser('options', help='Show free TTS options')
    
    args = parser.parse_args()
    
    if args.command == 'transcribe':
        transcribe_with_whisper(args.audio_file, args.model, args.output)
    elif args.command == 'batch':
        batch_transcribe_directory(args.audio_dir, args.output, args.model, args.pattern)
    elif args.command == 'options':
        show_free_tts_options()
    else:
        show_free_tts_options()
        parser.print_help()
