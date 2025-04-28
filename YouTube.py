import requests
import json
import yt_dlp
import os
import re

# Configurazioni
API_KEY = os.getenv("YOUTUBE_API_KEY", "AIzaSyAzgoV9ZuB0JoTmyQ7kkwXxYSpnVGjYENI")
# NOTA: 'simud chiave' è un segnaposto. Per test locali, sostituirlo con una nuova chiave API valida generata da Google Cloud Console.
# Per GitHub Actions, la chiave viene caricata automaticamente dal segreto YOUTUBE_API_KEY.
CHANNEL_ID = "UCV5c7W3qFazn4fiJ0N7m9qw"  # ID del canale ufficiale Sky Sport Italia (@SkySport)
QUERY = "highlight"  # Query generica per catturare più risultati
OUTPUT_FILE = "highlights.m3u8"
MAX_RESULTS = 20

def fetch_videos(channel_id, query, max_results):
    """Ottieni i video dal canale filtrati per una query."""
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "q": query,
        "type": "video",  # Restringe i risultati ai video
        "order": "date",
        "maxResults": max_results,
        "key": API_KEY,
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        print("Risposta API completa:", json.dumps(data, indent=2))  # Debug dettagliato
        
        # Filtra i video con "highlights" (o varianti) nel titolo
        filtered_videos = []
        for video in data.get("items", []):
            # Verifica che l'elemento sia un video
            if video.get("id", {}).get("kind") != "youtube#video":
                print(f"Elemento scartato (non è un video): {video.get('snippet', {}).get('title', 'N/A')}")
                continue
            title = video["snippet"]["title"]
            print(f"Titolo video: {title}")  # Debug: mostra ogni titolo
            # Cerca varianti di "highlights" (case-insensitive, con o senza trattini)
            if re.search(r'\bhigh-?lights?\b', title, re.IGNORECASE):
                filtered_videos.append(video)
        
        if not filtered_videos:
            print(f"Nessun video con 'highlights' (o varianti) nel titolo trovato per la query '{query}' nel canale {channel_id}")
        else:
            print(f"Trovati {len(filtered_videos)} video con 'highlights' nel titolo")
        
        return filtered_videos
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta API per i video: {e}")
        raise

def get_hls_url(video_url):
    """Estrae l'URL del flusso HLS usando yt-dlp."""
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "force_generic_extractor": False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            for format in info.get("formats", []):
                if format.get("ext") == "m3u8":
                    return format.get("url")
            return info.get("url", video_url)
    except Exception as e:
        print(f"Errore durante l'estrazione del flusso per {video_url}: {e}")
        return video_url

def create_m3u8(videos, output_file):
    """Crea un file .m3u8 con i flussi HLS dei video."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for video in videos:
            title = video["snippet"]["title"].replace(",", " ")
            video_id = video["id"].get("videoId")
            if not video_id:
                print(f"Errore: Nessun videoId trovato per il video '{title}'")
                continue
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            thumbnail = video["snippet"]["thumbnails"].get("high", {}).get("url", "")
            hls_url = get_hls_url(video_url)
            f.write(f"#EXTINF:-1 tvg-logo=\"{thumbnail}\",{title}\n")
            f.write(f"{hls_url}\n")
    print(f"Playlist salvata in {output_file}")

def main():
    try:
        print(f"Ottieni i video dal canale {CHANNEL_ID}...")
        videos = fetch_videos(CHANNEL_ID, QUERY, MAX_RESULTS)
        if videos:
            print("Generazione della playlist M3U8 con flussi HLS...")
            create_m3u8(videos, OUTPUT_FILE)
        else:
            print("Nessun video trovato con 'highlights' (o varianti) nel titolo.")
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")

if __name__ == "__main__":
    main()