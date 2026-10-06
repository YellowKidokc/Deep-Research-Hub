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

def get_captions_via_api(video_id):
    """
    Get captions using YouTube API directly (more reliable than transcript API)
    """
    try:
        captions_response = youtube.captions().list(
            part="snippet",
            videoId=video_id
        ).execute()
        
        captions = []
        for caption in captions_response.get("items", []):
            if caption["snippet"]["language"].startswith("en"):
                captions.append({
                    "id": caption["id"],
                    "language": caption["snippet"]["language"],
                    "name": caption["snippet"]["name"],
                    "isAuto": caption["snippet"]["trackKind"] == "asr"
                })
        
        return captions
    
    except HttpError as e:
        print(f"Error getting captions: {e}")
        return []

def download_caption_text(caption_id):
    """
    Download the actual caption text
    """
    try:
        caption_response = youtube.captions().download(
            id=caption_id,
            tfmt="srt"  # SubRip format
        ).execute()
        
        # The response is the raw SRT content
        return caption_response
    
    except HttpError as e:
        print(f"Error downloading caption: {e}")
        return None

def parse_srt_to_text(srt_content):
    """
    Parse SRT format to plain text
    """
    if not srt_content:
        return ""
    
    lines = srt_content.split('\n')
    text_lines = []
    
    for line in lines:
        # Skip line numbers and timestamps
        if line.strip() and not line.isdigit() and '-->' not in line:
            # Remove HTML tags and clean up
            clean_line = re.sub(r'<[^>]+>', '', line.strip())
            if clean_line:
                text_lines.append(clean_line)
    
    return '\n'.join(text_lines)

def fetch_and_display_transcript(video_id, video_title, video_url, search_terms=None):
    """
    Fetches and displays captions using YouTube API
    """
    print(f"\n📝 Processing: {video_title}")
    print(f"🔗 URL: {video_url}")
    
    # Get available captions
    captions = get_captions_via_api(video_id)
    
    if not captions:
        print("❌ No English captions available")
        return False
    
    print(f"📝 Found {len(captions)} caption tracks:")
    for cap in captions:
        print(f"   - {cap['name']} ({cap['language']}) {'(auto)' if cap['isAuto'] else ''}")
    
    # Try to download the best English caption
    best_caption = None
    for cap in captions:
        if not cap['isAuto']:  # Prefer manual captions
            best_caption = cap
            break
    
    if not best_caption and captions:
        best_caption = captions[0]  # Use first available if no manual
    
    if not best_caption:
        print("❌ No suitable caption found")
        return False
    
    print(f"📥 Downloading: {best_caption['name']}")
    
    srt_content = download_caption_text(best_caption['id'])
    
    if not srt_content:
        print("❌ Failed to download caption content")
        return False
    
    # Parse SRT to plain text
    transcript_text = parse_srt_to_text(srt_content)
    
    if not transcript_text:
        print("❌ No content in caption")
        return False
    
    # Prepare search terms for highlighting
    search_patterns = []
    if search_terms:
        for term in search_terms:
            search_patterns.append(re.compile(rf'\b{re.escape(term)}\b', re.IGNORECASE))
    
    print("─" * 80)
    
    # Display transcript with highlighting
    lines = transcript_text.split('\n')
    highlighted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line contains search terms
        is_relevant = False
        if search_patterns:
            for pattern in search_patterns:
                if pattern.search(line):
                    is_relevant = True
                    break
        
        if is_relevant:
            print(f"🎯 {line}")
            highlighted_lines.append(line)
        else:
            print(f"   {line}")
    
    print("─" * 80)
    print(f"✅ Transcript complete ({len(lines)} lines)")
    
    if highlighted_lines:
        print(f"🎯 Found {len(highlighted_lines)} relevant lines")
        print("\n🎯 RELEVANT EXCERPTS:")
        for line in highlighted_lines[:10]:
            print(f"   • {line}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search YouTube for biblical topics using API captions")
    
    parser.add_argument("--query", help="Search query for YouTube videos", 
                       type=str, default="bible contradictions explained")
    parser.add_argument("--max_videos", help="Maximum number of videos to process", 
                       type=int, default=3)
    parser.add_argument("--search_terms", help="Comma-separated terms to highlight", 
                       type=str, default="contradiction,error,bible,scripture,word of god,god,jesus,christ")
    
    args = parser.parse_args()
    
    search_terms = [term.strip() for term in args.search_terms.split(",")]
    
    print(f"🔍 Searching YouTube for: '{args.query}'")
    print(f"🎯 Looking for terms: {search_terms}")
    
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
        
        time.sleep(3)  # Longer delay to avoid rate limiting
        
        response = input("\nContinue to next video? (y/n): ").lower()
        if response != 'y':
            break

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY:")
    print(f"   ✅ Successfully processed: {cnt} videos")
    print(f"   ❌ No captions available: {failed_cnt} videos")
    if (cnt + failed_cnt) > 0:
        print(f"   📈 Success rate: {cnt/(cnt+failed_cnt)*100:.1f}%")
