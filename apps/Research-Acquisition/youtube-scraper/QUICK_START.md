# Quick Start Guide

## Super Simple Usage (Recommended)

### 1. Get Your API Key

1. Go to https://console.cloud.google.com/
2. Create a project → Enable "YouTube Data API v3"
3. Create Credentials → API Key
4. Copy the key

### 2. Add API Key to .env

Open `.env` file and paste your key:

```
YTB_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. Edit Channel List

Open `easy_scrape.py` and edit the `CHANNELS` list (around line 9):

```python
CHANNELS = [
    "mkbhd",           # MKBHD channel
    "veritasium",      # Veritasium channel
    "3blue1brown",     # 3Blue1Brown channel
]
```

**Channel names**: Use the part after `@` in the YouTube URL

- Example: `youtube.com/@mkbhd` → use `"mkbhd"`

### 4. Run It

```powershell
.\venv\Scripts\python.exe easy_scrape.py
```

That's it! All transcripts will be saved to `transcripts/` folder.

---

## Optional Settings

Edit these variables in `easy_scrape.py`:

```python
# Limit videos per channel (None = all videos)
MAX_VIDEOS_PER_CHANNEL = 10

# Change output folder
RESULTS_DIR = "my_transcripts"
```

---

## Advanced Usage (Original CLI)

If you want more control, use the original command-line interface:

```powershell
.\venv\Scripts\python.exe ytb_scraper.py --channel_name "mkbhd" --results_dir "transcripts" --max_videos 10
```

**Arguments:**

- `--channel_name`: Channel name (required)
- `--results_dir`: Output folder (default: "transcripts")
- `--max_videos`: Limit number of videos (optional)

---

## Output

For each channel, you'll get:

- `transcripts/<channel>_0.txt` - First video transcript
- `transcripts/<channel>_1.txt` - Second video transcript
- `transcripts/<channel>_N.txt` - Nth video transcript
- `transcripts/transcripts.json` - Metadata (URLs, titles, status)

**Note**: Not all videos have transcripts! Videos without transcripts will be skipped.

---

## Troubleshooting

**"API key not configured"**
→ Make sure `.env` has your real API key

**"No playlist found"**
→ Check the channel name (use the part after `@`)

**"Quota exceeded"**
→ YouTube API has 10,000 units/day free limit. Wait 24 hours or upgrade quota.

**Script won't run**
→ Make sure you're using the virtual environment:

```powershell
.\venv\Scripts\python.exe easy_scrape.py
```
