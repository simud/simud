import requests

# Sostituisci con la tua chiave API
API_KEY = "LA_TUA_API_KEY"
USERNAME = "skysport"  # Nome del canale YouTube
QUERY = "gol e highlights"  # Testo da cercare nei titoli
OUTPUT_FILE = "highlights.m3u8"
MAX_RESULTS = 20

def get_channel_id(username):
    """Ottieni l'ID del canale YouTube dato il nome utente."""
    base_url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "id",
        "forUsername": username,
        "key": API_KEY,
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    if data["items"]:
        return data["items"][0]["id"]
    else:
        raise ValueError(f"Impossibile trovare il canale con username: {username}")

def fetch_videos(channel_id, query, max_results):
    """Ottieni i video dal canale filtrati per una query."""
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
    """Crea un file .m3u8 con i video forniti."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for video in videos:
            title = video["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            thumbnail = video["snippet"]["thumbnails"]["high"]["url"]
            f.write(f"#EXTINF:-1,logo={thumbnail},{title}\n")
            f.write(f"{url}\n")
    print(f"Playlist salvata in {output_file}")

def main():
    print("Ottieni l'ID del canale...")
    channel_id = get_channel_id(USERNAME)
    print(f"ID del canale: {channel_id}")
    
    print("Scarica i video...")
    data = fetch_videos(channel_id, QUERY