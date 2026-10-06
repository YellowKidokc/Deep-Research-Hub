# Troubleshooting Guide

## Phase 4 — Test Scenarios Executed

### Scenario 1: Happy Path (Fixed)

**Input:** 20 channels, 3 videos each, valid API key  
**Expected:** Download 60 transcripts successfully  
**Observed:** Rate limiting (429 errors) on initial run  
**Fix Applied:** Added 2-second delay between requests  
**Status:** ✅ Fixed

### Scenario 2: Missing API Key

**Input:** Empty or invalid API key in `.env`  
**Expected:** Error message before execution  
**Observed:** Script detects and shows clear error message  
**Output:**

```
⚠️  YouTube API key not configured!
Please add your API key to the .env file:
YTB_API_KEY=your-actual-api-key
```

**Status:** ✅ Working as expected

### Scenario 3: Invalid Channel Name

**Input:** Non-existent channel handle  
**Expected:** Skip channel and continue with others  
**Observed:** Error logged, script continues  
**Output:**

```
❌ Failed to process @InvalidChannel
   Error: No playlist found for InvalidChannel
```

**Status:** ✅ Working as expected

---

## Phase 5 — Failure Modes & Recovery

### 1. Rate Limiting (429 Too Many Requests)

**How it breaks:**

- Making too many rapid requests to YouTube
- Happens when processing many videos without delays

**Detection:**

```
An error occurred: 429 Client Error: Too Many Requests
```

**Recovery:**

- ✅ **Already fixed** with 2-second delays in code
- If still occurring: Increase delay in `ytb_scraper.py` line 160
  ```python
  time.sleep(5)  # Increase from 2 to 5 seconds
  ```
- No reinstall needed

---

### 2. API Quota Exceeded

**How it breaks:**

- YouTube API free tier: 10,000 units/day
- Each video fetch: ~3-5 units
- Limit: ~2,000-3,000 videos/day

**Detection:**

```
quotaExceeded: The request cannot be completed because you have exceeded your quota
```

**Recovery:**

- **Wait 24 hours** for quota to reset (resets at midnight Pacific Time)
- Or upgrade to paid quota at Google Cloud Console
- Track usage: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- No reinstall needed

---

### 3. No Transcripts Available

**How it breaks:**

- Video doesn't have captions/transcripts
- Channel disabled transcripts
- Language mismatch

**Detection:**

```
Could not retrieve a transcript for the video
Saved 0 transcripts for <channel_name>
```

**Recovery:**

- This is normal - not all videos have transcripts
- Script automatically skips and continues
- Check `transcripts.json` for success/failure status
- No action needed

---

### 4. Invalid/Missing API Key

**How it breaks:**

- `.env` file missing
- API key empty or incorrect
- API key revoked/disabled

**Detection:**

```
⚠️  YouTube API key not configured!
```

or

```
google.auth.exceptions.DefaultCredentialsError
```

**Recovery:**

1. Check `.env` file exists in project root
2. Verify API key format: `YTB_API_KEY=AIzaSy...`
3. Test key at: https://console.cloud.google.com/apis/credentials
4. Generate new key if needed
5. No reinstall needed

---

### 5. Network/Connection Issues

**How it breaks:**

- No internet connection
- Firewall blocking YouTube
- DNS resolution failure

**Detection:**

```
requests.exceptions.ConnectionError
Failed to connect to youtube.com
```

**Recovery:**

- Check internet connection
- Test: `ping youtube.com`
- Check firewall/proxy settings
- Retry script after connection restored
- No reinstall needed

---

### 6. Virtual Environment Not Activated

**How it breaks:**

- Running script with system Python instead of venv
- Missing dependencies

**Detection:**

```
ModuleNotFoundError: No module named 'googleapiclient'
```

**Recovery:**

- **Always use:** `.\venv\Scripts\python.exe easy_scrape.py`
- Or double-click `run.bat` (handles this automatically)
- Don't use: `python easy_scrape.py` (uses system Python)
- No reinstall needed

---

### 7. Corrupted Dependencies

**How it breaks:**

- Package installation interrupted
- Version conflicts
- Corrupted cache

**Detection:**

```
ImportError: cannot import name 'X' from 'Y'
AttributeError in installed packages
```

**Recovery:**

```powershell
# Reinstall dependencies
.\venv\Scripts\pip.exe install --force-reinstall -r requirements.txt

# Or recreate venv from scratch
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt
```

---

### 8. Disk Space Full

**How it breaks:**

- Transcripts folder fills disk
- Each transcript: 10-100 KB
- 1000 videos ≈ 50-100 MB

**Detection:**

```
OSError: [Errno 28] No space left on device
```

**Recovery:**

1. Check disk space: `Get-PSDrive C`
2. Delete old transcripts: `Remove-Item transcripts\* -Recurse`
3. Change output directory in `easy_scrape.py`:
   ```python
   RESULTS_DIR = "D:\other_drive\transcripts"
   ```
4. No reinstall needed

---

### 9. Permission Denied

**How it breaks:**

- Running in protected directory
- Antivirus blocking file writes
- File locked by another process

**Detection:**

```
PermissionError: [Errno 13] Permission denied: 'transcripts\...'
```

**Recovery:**

1. Run as Administrator (right-click `run.bat` → Run as administrator)
2. Move project to user directory (e.g., `C:\Users\YourName\youtube-scraper`)
3. Check antivirus exclusions
4. Close any programs accessing transcript files
5. No reinstall needed

---

### 10. Channel Handle Changed

**How it breaks:**

- YouTube channel renamed their handle
- Channel deleted/suspended
- Typo in channel name

**Detection:**

```
No playlist found for <channel_name>
```

**Recovery:**

1. Visit channel on YouTube
2. Check current handle (after `@` in URL)
3. Update `easy_scrape.py` with correct handle
4. No reinstall needed

---

## Quick Recovery Checklist

Before asking for help, verify:

- [ ] `.env` file exists with valid API key
- [ ] Using venv Python: `.\venv\Scripts\python.exe`
- [ ] Internet connection working
- [ ] Not exceeded daily API quota (10,000 units)
- [ ] Disk space available
- [ ] Channel names are correct (check YouTube URLs)
- [ ] Running from project directory: `d:\GitHub\youtube-scraper`

---

## Emergency Reset

If everything is broken, full reset:

```powershell
# 1. Backup any transcripts you want to keep
Copy-Item transcripts backup_transcripts -Recurse

# 2. Clean everything
Remove-Item -Recurse -Force venv, transcripts

# 3. Reinstall
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt

# 4. Verify API key in .env
Get-Content .env

# 5. Test
.\venv\Scripts\python.exe ytb_scraper.py --help
```

Total time: ~2 minutes

---

## Getting Help

If issues persist:

1. Check error message against this guide
2. Verify all checklist items above
3. Check GitHub issues: https://github.com/imomayiz/youtube_scraper/issues
4. Check YouTube Transcript API issues: https://github.com/jdepoix/youtube-transcript-api/issues
5. Provide: Error message, Python version, OS version, steps to reproduce
