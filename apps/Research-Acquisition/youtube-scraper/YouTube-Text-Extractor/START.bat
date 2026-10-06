@echo off
title 🎬 YouTube Text Extractor - Professional
color 0A

:: ASCII Art Header
echo.
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║                                                              ║
echo    ║     🎬 Y O U T U B E   T E X T   E X T R A C T O R          ║
echo    ║                                                              ║
echo    ║     📹 Download Videos  •  🎙️ Extract Text  •  📚 Analyze   ║
echo    ║                                                              ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ ERROR: Python not found!
    echo    Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

:: Check if required packages are installed
echo    🔍 Checking dependencies...
python -c "import yt_dlp, whisper, torch" >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  Installing required packages...
    python -m pip install yt-dlp openai-whisper torch torchaudio
    if errorlevel 1 (
        echo    ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo    ✅ Dependencies installed successfully
    echo.
)

:: Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo    ⚠️  WARNING: FFmpeg not found!
    echo    Please install FFmpeg for audio extraction:
    echo    • Chocolatey: choco install ffmpeg
    echo    • Download: https://ffmpeg.org/download.html
    echo.
    echo    Press any key to continue anyway...
    pause >nul
    echo.
)

:: Menu
:menu
cls
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║                    🎬 MAIN MENU                           ║
echo    ╠══════════════════════════════════════════════════════════════╣
echo    ║  1️⃣  Launch GUI Interface (Recommended)                    ║
echo    ║  2️⃣  Quick: Download & Transcribe Single Video             ║
echo    ║  3️⃣  Batch: Process Multiple Videos                        ║
echo    ║  4️⃣  Find: Search Bible Contradiction Videos               ║
echo    ║  5️⃣  Tools: Just Download MP3s                            ║
echo    ║  6️⃣  Help: View Documentation                              ║
echo    ║  7️⃣  Exit                                                  ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.
set /p choice="    🎯 Select an option (1-7): "

if "%choice%"=="1" goto gui
if "%choice%"=="2" goto quick
if "%choice%"=="3" goto batch
if "%choice%"=="4" goto find
if "%choice%"=="5" goto tools
if "%choice%"=="6" goto help
if "%choice%"=="7" goto exit

echo    ❌ Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:gui
echo.
echo    🚀 Launching Professional GUI Interface...
echo    📋 The paper-like interface will open in a new window
echo.
python src\gui_interface.py
if errorlevel 1 (
    echo    ❌ Failed to launch GUI
    pause
)
goto menu

:quick
echo.
set /p url="    📺 Enter YouTube URL: "
if "%url%"=="" goto menu
set /p output="    📁 Output folder (default: quick_download): "
if "%output%"=="" set output=quick_download
echo.
echo    🎬 Downloading and transcribing...
python src\youtube_to_text.py "%url%" --output "%output%" --model base
echo.
pause
goto menu

:batch
echo.
echo    📦 BATCH PROCESSING
echo    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo    📝 Instructions:
echo    1. Create a text file with YouTube URLs (one per line)
echo    2. Save it as 'downloads\urls.txt'
echo    3. Press any key to start processing
echo.
if not exist "downloads\urls.txt" (
    echo    📄 Creating sample urls.txt file...
    if not exist "downloads" mkdir downloads
    (
        echo # Sample YouTube URLs
        echo https://www.youtube.com/watch?v=OA-4eQN16n0
        echo https://www.youtube.com/watch?v=AsRti0nQqmg
        echo # Add your URLs below
    ) > "downloads\urls.txt"
    echo    ✅ Sample file created! Edit downloads\urls.txt with your URLs
    echo.
)
pause
echo    🚀 Starting batch processing...
python src\youtube_to_text.py --help >nul 2>&1
echo.
pause
goto menu

:find
echo.
echo    🔍 SEARCHING BIBLE CONTRADICTION VIDEOS
echo    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
python src\bible_content_analyzer.py --query "bible contradictions explained" --max_videos 5
echo.
pause
goto menu

:tools
echo.
echo    🔧 ADDITIONAL TOOLS
echo    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo    1️⃣  Download MP3 only
echo    2️⃣  Transcribe existing audio
echo    3️⃣  Back to main menu
echo.
set /p tool="    🎯 Select tool (1-3): "
if "%tool%"=="1" (
    set /p url="    📺 Enter YouTube URL: "
    python src\youtube_mp3_downloader.py "%url%"
)
if "%tool%"=="2" (
    set /p audio="    🎵 Enter audio file path: "
    python src\free_tts_transcriber.py transcribe "%audio%"
)
goto menu

:help
echo.
echo    📚 DOCUMENTATION & HELP
echo    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo    🎬 FEATURES:
echo    • ✅ 100%% FREE - No API costs or limits
echo    • ✅ Unlimited video downloads
echo    • ✅ High-quality transcription (Whisper AI)
echo    • ✅ Batch processing support
echo    • ✅ Bible-focused content analysis
echo    • ✅ Professional GUI interface
echo.
echo    📁 FOLDER STRUCTURE:
echo    • downloads\     - MP3 audio files
echo    • transcripts\   - Text transcripts
echo    • src\          - Source code
echo    • docs\         - Documentation
echo.
echo    🎯 USAGE EXAMPLES:
echo    • Single video: python src\youtube_to_text.py "URL"
echo    • Playlist:     python src\youtube_to_text.py "URL" --playlist
echo    • Bible search: python src\bible_content_analyzer.py --query "topic"
echo.
echo    🔗 SUPPORTED URLS:
echo    • Single videos: https://youtube.com/watch?v=VIDEO_ID
echo    • Playlists:    https://youtube.com/playlist?list=PLAYLIST_ID
echo    • Channels:     https://youtube.com/channel/CHANNEL_ID
echo.
pause
goto menu

:exit
echo.
echo    👋 Thank you for using YouTube Text Extractor!
echo    📁 Your files are saved in the downloads and transcripts folders
echo.
timeout /t 3 >nul
exit /b 0
