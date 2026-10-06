#!/usr/bin/env python3

import argparse
import json
import os
import time
import re
from urllib.parse import quote

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
            video_title = html_unescape(item["snippet"]["title"])
            video_description = html_unescape(item["snippet"]["description"])
            channel_title = html_unescape(item["snippet"]["channelTitle"])
            
            videos.append({
                "ID": video_id,
                "URL": video_url,
                "Title": video_title,
                "Description": video_description,
                "Channel": channel_title
            })
        
        return videos
    
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []

def html_unescape(text):
    """Unescape HTML entities"""
    import html
    return html.unescape(text)

def get_video_details(video_id):
    """
    Get detailed video information including duration, view count, etc.
    """
    try:
        video_response = youtube.videos().list(
            part="statistics,contentDetails,snippet",
            id=video_id
        ).execute()
        
        if not video_response["items"]:
            return None
        
        video = video_response["items"][0]
        return {
            "duration": video["contentDetails"]["duration"],
            "views": int(video["statistics"].get("viewCount", 0)),
            "likes": int(video["statistics"].get("likeCount", 0)),
            "comments": int(video["statistics"].get("commentCount", 0)),
        }
    except Exception as e:
        print(f"Error getting video details: {e}")
        return None

def highlight_text(text, search_terms):
    """Highlight search terms in text"""
    if not search_terms:
        return text
    
    highlighted = text
    for term in search_terms:
        pattern = re.compile(rf'(\b{re.escape(term)}\b)', re.IGNORECASE)
        highlighted = pattern.sub(r'**\1**', highlighted)
    
    return highlighted

def analyze_video_content(video, search_terms):
    """Analyze video title, description, and metadata for relevant content"""
    content = {
        "title": video["Title"],
        "description": video["Description"],
        "channel": video["Channel"],
        "url": video["URL"],
        "relevance_score": 0,
        "relevant_snippets": []
    }
    
    # Combine all text for analysis
    all_text = f"{video['Title']} {video['Description']}".lower()
    
    # Calculate relevance score
    for term in search_terms:
        term_lower = term.lower()
        count = all_text.count(term_lower)
        content["relevance_score"] += count
        
        # Find relevant snippets
        if term_lower in all_text:
            sentences = re.split(r'[.!?]+', video['Description'])
            for sentence in sentences:
                if term_lower in sentence.lower() and len(sentence.strip()) > 20:
                    content["relevant_snippets"].append(sentence.strip())
    
    # Get additional video details
    details = get_video_details(video["ID"])
    if details:
        content.update(details)
    
    return content

def format_duration(duration):
    """Convert ISO 8601 duration to readable format"""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    if not match:
        return "Unknown"
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def display_video_analysis(content, search_terms):
    """Display video analysis with highlighted relevant content"""
    print(f"\n{'='*80}")
    print(f"📺 VIDEO: {highlight_text(content['title'], search_terms)}")
    print(f"📺 Channel: {content['channel']}")
    print(f"🔗 URL: {content['url']}")
    
    if 'views' in content:
        print(f"👀 Views: {content['views']:,}")
        print(f"⏱️  Duration: {format_duration(content['duration'])}")
        if content.get('likes'):
            print(f"👍 Likes: {content['likes']:,}")
        if content.get('comments'):
            print(f"💬 Comments: {content['comments']:,}")
    
    print(f"🎯 Relevance Score: {content['relevance_score']}")
    
    print(f"\n📋 DESCRIPTION:")
    description = content['description']
    if len(description) > 500:
        description = description[:500] + "..."
    print(f"   {highlight_text(description, search_terms)}")
    
    if content['relevant_snippets']:
        print(f"\n🎯 RELEVANT EXCERPTS:")
        for snippet in content['relevant_snippets'][:5]:
            print(f"   • {highlight_text(snippet, search_terms)}")
    
    print(f"\n💡 ACTION: Visit {content['url']} to watch the full video")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search YouTube for biblical topics and analyze content")
    
    parser.add_argument("--query", help="Search query for YouTube videos", 
                       type=str, default="bible contradictions explained")
    parser.add_argument("--max_videos", help="Maximum number of videos to analyze", 
                       type=int, default=5)
    parser.add_argument("--search_terms", help="Comma-separated terms to look for", 
                       type=str, default="contradiction,error,bible,scripture,word of god,god,jesus,christ")
    parser.add_argument("--min_relevance", help="Minimum relevance score to display", 
                       type=int, default=1)
    
    args = parser.parse_args()
    
    search_terms = [term.strip() for term in args.search_terms.split(",")]
    
    print(f"🔍 Searching YouTube for: '{args.query}'")
    print(f"🎯 Looking for terms: {search_terms}")
    print(f"📊 Minimum relevance score: {args.min_relevance}")
    
    videos = search_videos_by_topic(args.query, args.max_videos)
    
    if not videos:
        print("❌ No videos found")
        exit(1)
    
    print(f"\n📺 Found {len(videos)} videos, analyzing content...")
    
    analyzed_videos = []
    
    for video in tqdm(videos):
        analysis = analyze_video_content(video, search_terms)
        if analysis["relevance_score"] >= args.min_relevance:
            analyzed_videos.append(analysis)
        time.sleep(1)  # Small delay to avoid rate limiting
    
    # Sort by relevance score
    analyzed_videos.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    print(f"\n📊 ANALYSIS COMPLETE:")
    print(f"   📺 Total videos analyzed: {len(videos)}")
    print(f"   🎯 Relevant videos found: {len(analyzed_videos)}")
    
    if analyzed_videos:
        print(f"\n🏆 TOP RELEVANT VIDEOS:")
        for i, content in enumerate(analyzed_videos, 1):
            print(f"\n🥇 VIDEO #{i}")
            display_video_analysis(content, search_terms)
    else:
        print(f"\n❌ No videos found matching the relevance criteria (score >= {args.min_relevance})")
        print("💡 Try lowering the --min_relevance threshold or using different search terms")
