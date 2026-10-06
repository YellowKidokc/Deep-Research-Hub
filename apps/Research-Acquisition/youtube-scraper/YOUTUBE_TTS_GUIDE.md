# 🎬 YouTube MP3 Downloader + Free TTS (Speech-to-Text)

## 🚀 QUICK START

### Step 1: Install Dependencies ✅ (Already done)
```bash
pip install yt-dlp openai-whisper torch torchaudio
```

### Step 2: Install FFmpeg (Required)
**Windows Options:**
- Chocolatey: `choco install ffmpeg`
- Scoop: `scoop install ffmpeg`
- Download from: https://ffmpeg.org/download.html

### Step 3: Download & Transcribe Videos

#### Single Video:
```bash
python youtube_to_text.py "YOUTUBE_VIDEO_URL"
```

#### Playlist (first 5 videos):
```bash
python youtube_to_text.py "YOUTUBE_PLAYLIST_URL" --playlist --max-videos 5
```

#### Higher Quality (slower but more accurate):
```bash
python youtube_to_text.py "YOUTUBE_VIDEO_URL" --model small
```

## 📁 OUTPUT STRUCTURE
```
bible_videos/
├── audio/           # Downloaded MP3 files
└── transcripts/     # Text transcripts
```

## 🎯 BIBLE TOPIC EXAMPLES

### Download Bible Contradiction Videos:
```bash
python youtube_to_text.py "https://www.youtube.com/watch?v=VIDEO_ID" --output bible_contradictions
```

### Process Entire Playlist:
```bash
python youtube_to_text.py "PLAYLIST_URL" --playlist --max-videos 10 --output bible_study
```

## 🎛️ WHISPER MODEL OPTIONS

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| tiny | 32MB | 10x faster | 85% | Quick drafts |
| base | 142MB | 6x faster | 90% | **Recommended** |
| small | 466MB | 2x faster | 94% | Good quality |
| medium | 1.5GB | Normal | 96% | High quality |
| large | 2.9GB | Slower | 98% | Best accuracy |

## 💡 TIPS FOR BIBLE CONTENT

1. **Use "base" model** for good balance of speed and accuracy
2. **Long videos**: Process in chunks for better results
3. **Multiple speakers**: Whisper handles this automatically
4. **Background noise**: Higher quality models work better

## 🔧 ALTERNATIVE TOOLS

### Just Download MP3:
```bash
python youtube_mp3_downloader.py "YOUTUBE_URL"
```

### Just Transcribe Audio:
```bash
python free_tts_transcriber.py transcribe audio_file.mp3
```

### Batch Transcribe Folder:
```bash
python free_tts_transcriber.py batch downloads/ --model base
```

## 📊 FREE TTS COMPARISON

| Service | Cost | Accuracy | Offline? | Limitations |
|---------|------|----------|----------|-------------|
| **Whisper** | FREE | 99% | ✅ | Requires GPU for speed |
| Google Cloud | $0.006/15s | 99% | ❌ | 60min free/month |
| Azure | $1/hour | 98% | ❌ | 5hrs free/month |
| AssemblyAI | $0.00015/s | 98% | ❌ | 3hrs free/month |

## 🎯 RECOMMENDED WORKFLOW

1. **Search for videos** using the content analyzer:
   ```bash
   python bible_content_analyzer.py --query "bible contradictions" --max_videos 10
   ```

2. **Download best videos** as MP3:
   ```bash
   python youtube_mp3_downloader.py "BEST_VIDEO_URL"
   ```

3. **Transcribe to text**:
   ```bash
   python free_tts_transcriber.py batch downloads/ --model base
   ```

4. **Search transcripts** for specific topics:
   ```bash
   grep -i "contradiction" transcripts/*.txt
   ```

## 🚨 TROUBLESHOOTING

### FFmpeg Issues:
- Make sure ffmpeg is in your PATH
- Windows: Add to System Environment Variables

### Memory Issues:
- Use smaller model: `--model tiny` or `--model base`
- Process one video at a time

### Slow Processing:
- Use GPU: Install CUDA version of PyTorch
- Use smaller model: `--model base`

### Accuracy Issues:
- Use larger model: `--model small` or `--model medium`
- Ensure audio quality is good

## 📞 EXAMPLE COMMANDS

```bash
# Download and transcribe a single video about Bible contradictions
python youtube_to_text.py "https://www.youtube.com/watch?v=VIDEO_ID" --output bible_studies

# Process first 3 videos from a playlist
python youtube_to_text.py "PLAYLIST_URL" --playlist --max-videos 3 --model small

# Just download MP3s from a playlist
python youtube_mp3_downloader.py "PLAYLIST_URL" --playlist --max-videos 5

# Transcribe all MP3s in a folder
python free_tts_transcriber.py batch downloads/ --model base --pattern "*.mp3"
```

## 🎯 NEXT STEPS

1. Install FFmpeg
2. Test with a short video first
3. Use "base" model for best balance
4. Process in batches for many videos
5. Search transcripts for specific topics
