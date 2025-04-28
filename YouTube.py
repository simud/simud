import os
import requests

# Sostituisci con la tua chiave API
API_KEY = "AIzaSyBm7DGqt4_D4sIiBex02s2-GBYFvOR4WSU"
CHANNEL_ID = "UCB8ANPeDVnJFiBQpXibJFCQ"  # ID del canale Sky Sport
OUTPUT_FILE = "highlights.m3u8"

def fetch_videos(channel_id, query, max_results=20):
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "q": query,
        "type": "video",
        "order": "date",
        "maxResults": max_results,
        "key": API_KEY,
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.json()

def create_m3u8(videos, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for video in videos:
            title = video["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
            f.write(f"#EXTINF:-1,logo={thumbnail},{title}\n")
            f.write(f"{url}\n")

def main():
    print("Fetching videos...")
    query = "gol e highlights"
    data = fetch_videos(CHANNEL_ID, query)
    videos = data.get("items", [])
    if videos:
        create_m3u8(videos, OUTPUT_FILE)
        print(f"Playlist saved to {OUTPUT_FILE}")
    else:
        print("No videos found.")

if __name__ == "__main__":
    main()