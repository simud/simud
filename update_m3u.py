import requests
import re
from bs4 import BeautifulSoup
import os

# Configurazione GitHub
REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
FILE_PATH = os.path.join(REPO_PATH, "skystreaming_playlist.m3u")

# URL di partenza (homepage o pagina con elenco eventi)
base_url = "https://skystreaming.onl/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://skystreaming.onl",
    "Referer": "https://skystreaming.onl/"
}

# [Tutte le altre funzioni rimangono identiche...]
# (find_event_pages, get_video_stream, extract_channel_name)

def create_m3u_file(video_streams):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        groups = {}
        for event_url, stream_url, element in video_streams:
            if not stream_url:
                continue
            channel_name = extract_channel_name(event_url, element)
            if "sport" in channel_name.lower():
                group = "Sport"
            elif "serie" in channel_name.lower():
                group = "Serie TV"
            elif "film" in channel_name.lower():
                group = "Cinema"
            else:
                group = "Eventi"
            
            if group not in groups:
                groups[group] = []
            groups[group].append((channel_name, stream_url))

        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())
            
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\", {channel_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")

    print(f"File M3U creato con successo: {FILE_PATH}")

if __name__ == "__main__":
    event_pages = find_event_pages()
    if not event_pages:
        print("Nessuna pagina evento trovata.")
    else:
        video_streams = []
        for event_url in event_pages:
            print(f"Analizzo: {event_url}")
            stream_url, element = get_video_stream(event_url)
            if stream_url:
                video_streams.append((event_url, stream_url, element))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            create_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
