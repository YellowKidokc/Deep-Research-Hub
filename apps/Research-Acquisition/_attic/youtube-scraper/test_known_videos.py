#!/usr/bin/env python3

from youtube_transcript_api import YouTubeTranscriptApi

def test_known_videos():
    """Test with videos that typically have transcripts"""
    
    # Test video IDs that commonly have transcripts
    test_videos = [
        "dQw4w9WgXcQ",  # Rick Roll - very likely to have transcripts
        "jNQXAC9IVRw",  # "Me at the zoo" - first YouTube video
        "9bZkp7q19f0",  # Gangnam Style - popular video
    ]
    
    for video_id in test_videos:
        print(f"\nTesting video: {video_id}")
        try:
            # List all available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print("Available transcripts:")
            for transcript in transcript_list:
                print(f"  - {transcript.language_code} ({transcript.language}) - Generated: {transcript.is_generated}")
            
            # Try to get transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            print(f"✅ Got transcript with {len(transcript)} lines")
            print("First line:", transcript[0]['text'] if transcript else "No content")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_known_videos()
