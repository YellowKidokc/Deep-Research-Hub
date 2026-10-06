import argparse
import json
import os
import time

import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi


load_dotenv()
api_key = os.getenv("YTB_API_KEY")
youtube = build("youtube", "v3", developerKey=api_key)


def get_channel_id(channel_name):
    """
    Retrieves the id of a youtube channel from its channel name.

    Args:
      channel_name: Name of the youtube channel which is not the full name of channel but the name after the '@'
                    the channel link.

    Returns:
      The id of of the given channel.
    """
    try:
        # Method 1: Try direct HTML parsing
        url = "https://www.youtube.com/@" + channel_name
        r = requests.get(url)
        text = r.text
        
        # Try original method
        if "youtube.com/channel/" in text:
            id = text.split("youtube.com/channel/")[1].split('"')[0]
            return id
        
        # Method 2: Try alternative pattern
        import re
        match = re.search(r'"channelId":"([^"]+)"', text)
        if match:
            return match.group(1)
        
        # Method 3: Use YouTube API search to find channel
        try:
            search_response = youtube.search().list(
                part="snippet",
                q=channel_name,
                type="channel",
                maxResults=1
            ).execute()
            
            if search_response["items"]:
                return search_response["items"][0]["snippet"]["channelId"]
        except:
            pass
            
        raise Exception(f"Could not find channel ID for {channel_name}")
        
    except Exception as e:
        print(f"Error getting channel ID: {e}")
        raise


def fetch_video_ids(channel_name):
    """
    Fetches the video IDs of the videos in the uploads playlist of a channel.
    Args:
      channel_name: The name of the channel.
    Returns:
      A list of {video ID, video url, title}.
    """
    # Make a request to youtube api
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_id = get_channel_id(channel_name)
    params = {"part": "contentDetails", "id": channel_id, "key": api_key}
    try:
        response = requests.get(base_url, params=params)
        response = json.loads(response.content)
    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return []

    if "items" not in response or not response["items"]:
        raise Exception(f"No playlist found for {channel_name}")

    # Retrieve the uploads playlist ID for the given channel
    playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Retrieve all videos from uploads playlist
    videos = []
    next_page_token = None

    while True:
        playlist_items_response = (
            youtube.playlistItems()
            .list(
                # part="contentDetails",
                part="snippet",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            )
            .execute()
        )

        videos += playlist_items_response["items"]

        next_page_token = playlist_items_response.get("nextPageToken")

        if not next_page_token:
            break

    # Extract video URLs
    video_urls = []

    for video in videos:
        video_id = video["snippet"]["resourceId"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_title = video["snippet"]["title"]
        video_urls.append({"ID": video_id, "URL": video_url, "Title": video_title})

    return video_urls


def fetch_and_display_transcript(video_id, video_title, video_url):
    """
    Fetches and displays the transcript of a video directly to console.
    Also saves to file if needed.
    Args:
      video_id: The YouTube video ID
      video_title: The video title
      video_url: The video URL
    Returns:
        True if a transcript was found and processed, False otherwise.
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
                # Get the first available transcript
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
    for line in transcript:
        text = line["text"].strip()
        if text:  # Skip empty lines
            full_text.append(text)
            print(text)
    
    print("─" * 80)
    print(f"✅ Transcript complete ({len(full_text)} lines)")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--channel_name", help="The name of the channel.", type=str)
    parser.add_argument(
        "--results_dir",
        help="The directory to save the transcripts.",
        type=str,
        default="transcripts",
    )
    parser.add_argument(
        "--max_videos",
        help="The max number of transcripts.",
        type=int,
        default=None,
    )

    args = parser.parse_args()
    max_videos = args.max_videos
    channel_name = args.channel_name
    results_dir = args.results_dir

    TRANSCRIPTS_DIR = os.path.join(os.getcwd(), results_dir)
    os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

    print(f"Fetching video IDs for {channel_name}...")
    videos = fetch_video_ids(channel_name)
    if max_videos:
        videos = videos[:max_videos]

    print(f"Fetching transcripts for {channel_name}...")
    cnt = 0
    failed_cnt = 0
    
    for i, video in enumerate(tqdm(videos)):
        print(f"\n{'='*60}")
        print(f"Processing video {i+1}/{len(videos)}")
        
        # Display transcript directly to console
        success = fetch_and_display_transcript(video["ID"], video["Title"], video["URL"])
        
        if success:
            cnt += 1
        else:
            failed_cnt += 1
        
        # Add delay to avoid rate limiting
        time.sleep(2)
        
        # Ask user if they want to continue (for testing)
        if max_videos and max_videos <= 5:  # Only for small test runs
            response = input("\nContinue to next video? (y/n): ").lower()
            if response != 'y':
                break

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY for {channel_name}:")
    print(f"   ✅ Successfully processed: {cnt} videos")
    print(f"   ❌ No transcripts available: {failed_cnt} videos")
    print(f"   📈 Success rate: {cnt/(cnt+failed_cnt)*100:.1f}%" if (cnt+failed_cnt) > 0 else "   📈 Success rate: 0%")
