#!/usr/bin/env python3

import argparse
import json
import os
import time
import re

import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()
api_key = os.getenv("YTB_API_KEY")
youtube = build("youtube", "v3", developerKey=api_key)

def search_videos_by_topic(query, max_results=10):
    """
    Search for YouTube videos by topic/query
    Args:
        query: Search query string
        max_results: Maximum number of results to return
    Returns:
        List of video dictionaries with ID, title, URL
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

def fetch_and_display_transcript(video_id, video_title, video_url, search_terms=None):
    """
    Fetches and displays the transcript of a video directly to console.
    Highlights content related to search terms if provided.
    """
    transcript = None
    transcript_language = None
    
    # Try 1: Manual English transcript
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        transcript_language = "English (manual)"
    except Exception as e:
        pass
    
    # Try 2: Auto-generated English transcript
    if not transcript:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en-US", "en-GB"])
            transcript_language = "English (auto-generated)"
        except Exception as e:
            pass
    
    # Try 3: Any available transcript
    if not transcript:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = list(transcript_list)
            if available_transcripts:
                transcript = available_transcripts[0].fetch()
                transcript_language = available_transcripts[0].language_code
        except Exception as e:
            pass
    
    # Try 4: Get any available language and translate to English
    if not transcript:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            for t in transcript_list:
                try:
                    transcript = t.translate('en').fetch()
                    transcript_language = f"{t.language_code} (translated to English)"
                    break
                except:
                    continue
        except Exception as e:
            pass
    
    if not transcript:
        print(f"\n❌ No transcript available for: {video_title}")
        print(f"   URL: {video_url}")
        return False
    
    # Display transcript directly to console
    print(f"\n📝 Transcript for: {video_title}")
    print(f"🌐 Language: {transcript_language}")
    print(f"🔗 URL: {video_url}")
    print("─" * 80)
    
    full_text = []
    highlighted_lines = []
    
    # Prepare search terms for highlighting
    search_patterns = []
    if search_terms:
        for term in search_terms:
            # Create case-insensitive regex patterns for each term
            search_patterns.append(re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE))
    
    for line in transcript:
        text = line["text"].strip()
        if text:  # Skip empty lines
            full_text.append(text)
            
            # Check if line contains search terms
            is_relevant = False
            if search_patterns:
                for pattern in search_patterns:
                    if pattern.search(text):
                        is_relevant = True
                        break
            
            if is_relevant:
                print(f"🎯 {text}")  # Highlight relevant lines
                highlighted_lines.append(text)
            else:
                print(f"   {text}")  # Regular lines
    
    print("─" * 80)
    print(f"✅ Transcript complete ({len(full_text)} lines)")
    if highlighted_lines:
        print(f"🎯 Found {len(highlighted_lines)} relevant lines matching search terms")
        print("\n🎯 RELEVANT EXCERPTS:")
        for line in highlighted_lines[:10]:  # Show first 10 relevant lines
            print(f"   • {line}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search YouTube for videos about biblical topics and extract transcripts")
    
    parser.add_argument("--query", help="Search query for YouTube videos", 
                       type=str, default="bible contradictions errors word of god")
    parser.add_argument("--max_videos", help="Maximum number of videos to process", 
                       type=int, default=5)
    parser.add_argument("--search_terms", help="Comma-separated terms to highlight in transcripts", 
                       type=str, default="contradiction,error,bible,scripture,word of god,god,jesus,christ")
    
    args = parser.parse_args()
    
    # Parse search terms
    search_terms = [term.strip() for term in args.search_terms.split(",")]
    
    print(f"🔍 Searching YouTube for: '{args.query}'")
    print(f"🎯 Looking for terms: {search_terms}")
    
    # Search for videos
    videos = search_videos_by_topic(args.query, args.max_videos)
    
    if not videos:
        print("❌ No videos found for the search query")
        exit(1)
    
    print(f"📺 Found {len(videos)} videos")
    
    # Process each video
    cnt = 0
    failed_cnt = 0
    
    for i, video in enumerate(tqdm(videos)):
        print(f"\n{'='*60}")
        print(f"Processing video {i+1}/{len(videos)}")
        
        # Display transcript directly to console
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
        
        # Add delay to avoid rate limiting
        time.sleep(2)
        
        # Ask user if they want to continue
        response = input("\nContinue to next video? (y/n): ").lower()
        if response != 'y':
            break

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ Successfully processed: {cnt} videos")
    print(f"   ❌ No transcripts available: {failed_cnt} videos")
    print(f"   📈 Success rate: {cnt/(cnt+failed_cnt)*100:.1f}%" if (cnt+failed_cnt) > 0 else "   📈 Success rate: 0%")
