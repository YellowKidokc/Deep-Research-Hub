# 📚 User Guide

## 🎬 Getting Started

### Step 1: Launch the Application
1. **Double-click `START.bat`** - This opens the professional launcher
2. **Choose option 1** - Launch GUI Interface (recommended)
3. **Wait for the window** - The paper-like interface will appear

### Step 2: Add YouTube URLs
1. **Click in the URL box** - The large text area at the top
2. **Paste your URLs** - One per line, or single URL
3. **Examples accepted:**
   - Single video: `https://www.youtube.com/watch?v=VIDEO_ID`
   - Playlist: `https://www.youtube.com/playlist?list=PLAYLIST_ID`
   - Channel: `https://www.youtube.com/channel/CHANNEL_ID`

### Step 3: Choose Settings
- **Model Quality**: 
  - Tiny (Fastest) - For quick drafts
  - Base (Recommended) - Best balance
  - Small/Medium/Large - Higher quality, slower
- **Output Folder**: Where to save your files

### Step 4: Start Processing
- **Click "Download & Transcribe"** - Processing begins automatically
- **Watch the progress** - Real-time updates in the log area
- **Files are saved** - MP3s in downloads/, text in transcripts/

## 📋 Alternative Methods

### Quick Single Video
1. Run `START.bat`
2. Choose option 2
3. Paste URL when prompted
4. Choose output folder
5. Wait for completion

### Batch Processing
1. Create `downloads/urls.txt` with your URLs
2. Run `START.bat`
3. Choose option 3
4. All URLs processed automatically

### Find Bible Videos
1. Run `START.bat`
2. Choose option 4
3. Automatically searches for relevant content

## 🎯 Bible Study Workflow

### Step 1: Find Relevant Videos
```
Search for: "bible contradictions explained"
Search for: "bible errors solved"
Search for: "scripture difficulties"
```

### Step 2: Download & Transcribe
- Use Base model for best balance
- Organize by topic in different folders
- Process playlists from trusted channels

### Step 3: Analyze Content
- Search transcripts for specific topics
- Compare different explanations
- Build your understanding

## 🔍 Advanced Features

### Custom Search Terms
The Bible content analyzer can be customized:
```bash
python src/bible_content_analyzer.py --query "your search terms" --max_videos 10
```

### Quality vs Speed
- **Tiny**: 32MB, 10x speed, 85% accuracy
- **Base**: 142MB, 6x speed, 90% accuracy ✅
- **Small**: 466MB, 2x speed, 94% accuracy
- **Medium**: 1.5GB, 1x speed, 96% accuracy
- **Large**: 2.9GB, 0.5x speed, 98% accuracy

### Batch File Management
- Organize URLs by topic in separate files
- Use descriptive output folder names
- Keep transcripts for future reference

## 🛠️ Troubleshooting

### Common Issues

**"Python not found"**
- Install Python from python.org
- Make sure to add to PATH during installation

**"FFmpeg not found"**
- Install with: `choco install ffmpeg`
- Or download from ffmpeg.org

**"Download failed"**
- Check internet connection
- Verify video is not private/deleted
- Try different video

**"No transcript"**
- Video may not have captions
- Try higher quality model
- Some videos have no available captions

### Performance Tips

- **Use SSD storage** for faster processing
- **Close other programs** to free memory
- **Process in batches** for many videos
- **Use Base model** for best balance

## 📁 File Organization

### Recommended Structure
```
YouTube-Text-Extractor/
├── downloads/
│   ├── bible_contradictions/
│   ├── bible_prophecy/
│   └── bible_history/
└── transcripts/
    ├── bible_contradictions/
    ├── bible_prophecy/
    └── bible_history/
```

### Naming Convention
- Use descriptive folder names
- Include date for research projects
- Keep original video titles in files

## 🎓 Best Practices

### For Bible Study
1. **Start with broad searches** then narrow down
2. **Cross-reference multiple sources**
3. **Keep notes on different interpretations**
4. **Organize by biblical topics**

### For Research
1. **Document sources** carefully
2. **Use consistent naming**
3. **Back up important transcripts**
4. **Search across multiple transcripts**

### For Content Creation
1. **Extract key quotes** easily
2. **Find statistical data** in videos
3. **Create accessible content** with transcripts
4. **Repurpose content** across platforms

## 🔗 Supported URLs

### ✅ Works With:
- YouTube videos (`youtube.com/watch?v=`)
- YouTube shorts (`youtube.com/shorts/`)
- YouTube playlists (`youtube.com/playlist?list=`)
- YouTube channels (`youtube.com/channel/`)
- YouTube user pages (`youtube.com/user/`)
- YouTube custom URLs (`youtube.com/c/`)

### ❌ Doesn't Work With:
- Private videos (need access)
- Age-restricted videos
- Deleted videos
- Live streams (after they end)

## 📞 Getting Help

### Self-Service
- Check this guide first
- Try the troubleshooting steps
- Test with a short, public video

### Common Questions
**Q: How many videos can I process?**
A: Unlimited! No restrictions or limits.

**Q: Is this really free?**
A: 100% free. No API costs, no subscriptions.

**Q: Can I use this commercially?**
A: Yes, MIT license allows commercial use.

**Q: How accurate are the transcripts?**
A: 85-99% depending on model and audio quality.

**Q: Can it process other languages?**
A: Yes, Whisper supports 99+ languages.

---

Need more help? Check the full documentation or create an issue on GitHub.
