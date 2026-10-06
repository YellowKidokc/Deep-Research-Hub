#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

def test_video_transcript(video_id):
    """Test transcript fetching for a specific video"""
    print(f"Testing transcript for video ID: {video_id}")
    
    # List all available transcripts
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print("Available transcripts:")
        for transcript in transcript_list:
            print(f"  - Language: {transcript.language_code} ({transcript.language})")
            print(f"    Generated: {transcript.is_generated}")
            print(f"    Translatable: {transcript.is_translatable}")
        
        # Try to get English transcript
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            print(f"\n✅ Found English manual transcript ({len(transcript)} lines)")
            return transcript
        except:
            print("❌ No manual English transcript")
        
        # Try auto-generated English
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-US', 'en-GB'])
            print(f"✅ Found English auto-generated transcript ({len(transcript)} lines)")
            return transcript
        except:
            print("❌ No auto-generated English transcript")
        
        # Try first available and translate
        try:
            first_transcript = list(transcript_list)[0]
            if first_transcript.is_translatable:
                transcript = first_transcript.translate('en').fetch()
                print(f"✅ Found translated transcript ({len(transcript)} lines)")
                return transcript
        except:
            print("❌ Could not translate transcript")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    # Test with a known video that should have transcripts
    test_video_id = "GdDrYgXzBew"  # Khan Academy video
    transcript = test_video_transcript(test_video_id)
    
    if transcript:
        print("\nFirst 5 lines of transcript:")
        for i, line in enumerate(transcript[:5]):
            print(f"{i+1}: {line['text']}")
    else:
        print("\nNo transcript found!")
