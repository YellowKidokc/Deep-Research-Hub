#!/usr/bin/env python3

import argparse
import json
import os
import time
import random
import re

import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, TooManyRequests

load_dotenv()
api_key = os.getenv("YTB_API_KEY")
youtube = build("youtube", "v3", developerKey=api_key)

def search_videos_by_topic(query, max_results=10):
    """
    Search for YouTube videos by topic/query
    """
    try:
        search_response = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            order="relevance"
        ).execute()
        
        videos = []
        for item in search_response["items"]:
            video_id = item["id"]["videoId"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_title = item["snippet"]["title"]
            video_description = item["snippet"]["description"]
            
            videos.append({
                "ID": video_id,
                "URL": video_url,
                "Title": video_title,
                "Description": video_description
            })
        
        return videos
    
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []

def fetch_transcript_with_retry(video_id, max_retries=3):
    """
    Fetch transcript with retry logic and different strategies
    """
    
    strategies = [
        # Strategy 1: Try manual English
        lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=["en"]),
        
        # Strategy 2: Try auto-generated English
        lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=["en-US", "en-GB"]),
        
        # Strategy 3: Try any available transcript
        lambda: list(YouTubeTranscriptApi.list_transcripts(video_id))[0].fetch(),
        
        # Strategy 4: Try translate any available to English
        lambda: next((t.translate('en').fetch() for t in YouTubeTranscriptApi.list_transcripts(video_id) if t.is_translatable), None)
    ]
    
    for strategy_num, strategy in enumerate(strategies, 1):
        for attempt in range(max_retries):
            try:
                transcript = strategy()
                if transcript:
                    print(f"✅ Strategy {strategy_num} succeeded on attempt {attempt + 1}")
                    return transcript, f"Strategy {strategy_num}"
            except TooManyRequests:
                wait_time = random.uniform(5, 15)  # Random wait between 5-15 seconds
                print(f"⏳ Rate limited. Waiting {wait_time:.1f}s... (Strategy {strategy_num}, attempt {attempt + 1})")
                time.sleep(wait_time)
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                print(f"❌ Strategy {strategy_num}: {type(e).__name__}")
                break  # This strategy won't work, try next one
            except Exception as e:
                print(f"⚠️  Strategy {strategy_num} attempt {attempt + 1} failed: {type(e).__name__}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 5))
    
    return None, None

def fetch_and_display_transcript(video_id, video_title, video_url, search_terms=None):
    """
    Fetches and displays transcript with enhanced error handling
    """
    print(f"\n📝 Processing: {video_title}")
    print(f"🔗 URL: {video_url}")
    
    transcript, method = fetch_transcript_with_retry(video_id)
    
    if not transcript:
        print("❌ No transcript available after all strategies")
        return False
    
    print(f"✅ Retrieved transcript using {method}")
    
    # Prepare search terms for highlighting
    search_patterns = []
    if search_terms:
        for term in search_terms:
            search_patterns.append(re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE))
    
    print("─" * 80)
    
    # Display transcript with highlighting
    highlighted_lines = []
    
    for i, line in enumerate(transcript):
        text = line["text"].strip()
        if not text:
            continue
        
        # Check if line contains search terms
        is_relevant = False
        if search_patterns:
            for pattern in search_patterns:
                if pattern.search(text):
                    is_relevant = True
                    break
        
        if is_relevant:
            print(f"🎯 [{i:04d}] {text}")
            highlighted_lines.append(text)
        else:
            # Only show every 10th line that's not relevant to reduce output
            if i % 10 == 0:
                print(f"   [{i:04d}] {text}")
    
    print("─" * 80)
    print(f"✅ Transcript complete ({len(transcript)} lines)")
    
    if highlighted_lines:
        print(f"🎯 Found {len(highlighted_lines)} relevant lines")
        print("\n🎯 RELEVANT EXCERPTS:")
        for line in highlighted_lines[:15]:  # Show first 15 relevant lines
            print(f"   • {line}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search YouTube for biblical topics with robust transcript fetching")
    
    parser.add_argument("--query", help="Search query for YouTube videos", 
                       type=str, default="bible contradictions explained")
    parser.add_argument("--max_videos", help="Maximum number of videos to process", 
                       type=int, default=3)
    parser.add_argument("--search_terms", help="Comma-separated terms to highlight", 
                       type=str, default="contradiction,error,bible,scripture,word of god,god,jesus,christ")
    parser.add_argument("--delay", help="Delay between videos in seconds", 
                       type=float, default=10.0)
    
    args = parser.parse_args()
    
    search_terms = [term.strip() for term in args.search_terms.split(",")]
    
    print(f"🔍 Searching YouTube for: '{args.query}'")
    print(f"🎯 Looking for terms: {search_terms}")
    print(f"⏱️  Delay between videos: {args.delay}s")
    
    videos = search_videos_by_topic(args.query, args.max_videos)
    
    if not videos:
        print("❌ No videos found")
        exit(1)
    
    print(f"📺 Found {len(videos)} videos")
    
    cnt = 0
    failed_cnt = 0
    
    for i, video in enumerate(tqdm(videos)):
        print(f"\n{'='*60}")
        print(f"Processing video {i+1}/{len(videos)}")
        
        success = fetch_and_display_transcript(
            video["ID"], 
            video["Title"], 
            video["URL"], 
            search_terms
        )
        
        if success:
            cnt += 1
        else:
            failed_cnt += 1
        
        # Wait between videos with randomization
        if i < len(videos) - 1:  # Don't wait after last video
            wait_time = args.delay + random.uniform(-2, 2)  # Add some randomness
            print(f"⏳ Waiting {wait_time:.1f}s before next video...")
            time.sleep(wait_time)
        
        response = input("\nContinue to next video? (y/n): ").lower()
        if response != 'y':
            break

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ Successfully processed: {cnt} videos")
    print(f"   ❌ No transcripts available: {failed_cnt} videos")
    if (cnt + failed_cnt) > 0:
        print(f"   📈 Success rate: {cnt/(cnt+failed_cnt)*100:.1f}%")
