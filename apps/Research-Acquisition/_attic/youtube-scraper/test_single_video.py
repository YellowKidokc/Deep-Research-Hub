"""Test a single video from TruthisChrist to see if transcripts work"""
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import os

load_dotenv()

# Test with a specific video ID from TruthisChrist
video_id = "qxZpwZiTKp4"  # From earlier test

print(f"Testing video: https://www.youtube.com/watch?v={video_id}")
print("=" * 60)

try:
    # List available transcripts
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    print("\n✅ Transcripts available:")
    for t in transcript_list:
        print(f"   - {t.language} ({t.language_code}) - Auto: {t.is_generated}")
    
    # Try to fetch using our improved method
    print("\n" + "=" * 60)
    print("Attempting to fetch transcript...")
    
    transcript = None
    
    # Try 1: Manual English
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        print("✅ Method 1 worked: Manual English")
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)[:100]}")
    
    # Try 2: List and find English
    if not transcript:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_transcript(['en']).fetch()
            print("✅ Method 2 worked: Find English from list")
        except Exception as e:
            print(f"❌ Method 2 failed: {str(e)[:100]}")
    
    # Try 3: Get generated English
    if not transcript:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            for t in transcript_list:
                if 'en' in t.language_code.lower():
                    transcript = t.fetch()
                    print(f"✅ Method 3 worked: Got {t.language_code}")
                    break
        except Exception as e:
            print(f"❌ Method 3 failed: {str(e)[:100]}")
    
    if transcript:
        print("\n" + "=" * 60)
        print(f"✅ SUCCESS! Got {len(transcript)} transcript entries")
        print("\nFirst 3 lines:")
        for i, line in enumerate(transcript[:3]):
            print(f"   {line['text']}")
        
        # Try to save it
        test_file = "test_output.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            for line in transcript:
                f.write(line["text"] + "\n")
        print(f"\n✅ Saved to {test_file}")
        
        # Check file size
        size = os.path.getsize(test_file)
        print(f"   File size: {size} bytes")
    else:
        print("\n❌ FAILED: Could not get transcript with any method")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
