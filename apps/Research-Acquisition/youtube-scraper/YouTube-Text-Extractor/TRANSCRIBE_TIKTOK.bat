@echo off
title 🚀 LIGHTNING FAST TIKTOK TRANSCRIBER
color 0B

echo.
echo    ╔══════════════════════════════════════════════════════════════╗
echo    ║                                                              ║
echo    ║     ⚡ LIGHTNING FAST TIKTOK VIDEO TRANSCRIBER              ║
echo    ║                                                              ║
echo    ║     🎬 Process 80+ Videos in Minutes                        ║
echo    ║                                                              ║
echo    ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🔍 CHECKING DEPENDENCIES...
python -c "import whisper, torch" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Installing Whisper AI...
    python -m pip install openai-whisper torch
)

echo ✅ Ready to transcribe!

set VIDEO_DIR=C:\Users\lowes\Videos\4K Tokkit\ppe_clips

echo.
echo 📁 Target Directory: %VIDEO_DIR%
echo 📊 Found Videos: 
dir /b "%VIDEO_DIR%\*.mp4" 2>nul | find /c /v "" > temp_count.txt
set /p VIDEO_COUNT=<temp_count.txt
del temp_count.txt
echo    📹 %VIDEO_COUNT% MP4 files found
echo.

echo ⚡ SPEED OPTIONS:
echo    1️⃣  🚀 ULTRA FAST (Parallel, Tiny Model) - ~30 seconds per video
echo    2️⃣  📝 FAST (Sequential, Tiny Model) - ~45 seconds per video  
echo    3️⃣  🎯 HIGH QUALITY (Sequential, Small Model) - ~2 minutes per video
echo.

set /p MODE="🎯 Choose speed mode (1-3, default=1): "

if "%MODE%"=="2" (
    set MODEL=tiny
    set METHOD=sequential
    echo 📝 FAST MODE selected
) else if "%MODE%"=="3" (
    set MODEL=small  
    set METHOD=sequential
    echo 🎯 HIGH QUALITY MODE selected
) else (
    set MODEL=tiny
    set METHOD=parallel
    echo 🚀 ULTRA FAST MODE selected
)

echo.
echo 🚀 STARTING TRANSCRIPTION...
echo 📊 Estimated time: %VIDEO_COUNT% videos × ~30 seconds = %VIDEO_COUNT% minutes
echo ⏰ Start time: %time%
echo.

python fast_video_transcriber.py

echo.
echo 🎉 TRANSCRIPTION COMPLETE!
echo 📁 Check the "transcripts" folder for all text files
echo 📋 Summary report available in transcripts folder
echo.
pause
