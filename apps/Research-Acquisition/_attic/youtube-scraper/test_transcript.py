"""Quick test to see what transcripts are available"""
from youtube_transcript_api import YouTubeTranscriptApi
import requests

# Get a video from TruthisChrist channel
channel_url = "https://www.youtube.com/@TruthisChrist"
print(f"Testing channel: {channel_url}")

# Try to get channel's first video
try:
    # Get channel page
    r = requests.get(channel_url)
    text = r.text
    
    # Find first video ID (very basic extraction)
    if '"videoId":"' in text:
        video_id = text.split('"videoId":"')[1].split('"')[0]
        print(f"\nFound video ID: {video_id}")
        print(f"Video URL: https://www.youtube.com/watch?v={video_id}")
        
        # Try to get transcript
        print("\nAttempting to fetch transcript...")
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print("\nAvailable transcripts:")
            for transcript in transcript_list:
                print(f"  - {transcript.language} ({transcript.language_code}) - Generated: {transcript.is_generated}")
            
            # Try to get English
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                print(f"\n✅ Successfully fetched English transcript!")
                print(f"   First 3 lines:")
                for i, line in enumerate(transcript[:3]):
                    print(f"   {line['text']}")
            except Exception as e:
                print(f"\n❌ Could not fetch English transcript: {e}")
                
        except Exception as e:
            print(f"❌ No transcripts available: {e}")
    else:
        print("Could not find video ID on channel page")
        
except Exception as e:
    print(f"Error: {e}")
