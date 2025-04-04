import requests
import re
import os

# URL della pagina principale
SITE_URL = "https://sportsonline.gl/prog.txt"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://sportsonline.gl",
    "Referer": "https://sportsonline.gl/"
}

# Immagine fissa per i canali (lasciata solo per gli eventi)
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Dizionario per tradurre i giorni in italiano
DAY_TRANSLATION = {
    "MONDAY": "Lunedì",
    "TUESDAY": "Martedì",
    "WEDNESDAY": "Mercoledì",
    "THURSDAY": "Giovedì",
    "FRIDAY": "Venerdì",
    "SATURDAY": "Sabato",
    "SUNDAY": "Domenica"
}

# Funzione per ottenere il contenuto della pagina
def fetch_page_content():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {SITE_URL}: {e}")
        return []

# Funzione per estrarre eventi e URL .php, organizzati per giorno
def extract_events_and_streams(lines):
    events_by_day = {}
    current_day = None

    event_pattern = re.compile(r'(\d{2}:\d{2})\s+(.+?)\s+\|\s+(https://sportzonline\.ps/channels/[^\s]+\.php)')

    for line in lines:
        line = line.strip()
        if line in DAY_TRANSLATION:
            current_day = DAY_TRANSLATION[line]
            if current_day not in events_by_day:
                events_by_day[current_day] = []
        elif current_day:
            match = event_pattern.search(line)
            if match:
                time, event_title, stream_url = match.groups()
                channel_name = re.search(r'channels/[^/]+/([^/]+)\.php', stream_url).group(1)
                full_title = f"{time} {event_title} ({channel_name})"
                events_by_day[current_day].append((full_title, stream_url))

    return events_by_day

# Funzione per aggiornare il file M3U8
def update_m3u_file(events_by_day, m3u_file="sportsonline_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for day, events in events_by_day.items():
            if not events:
                continue
            # Gruppo senza tvg-logo
            f.write(f"#EXTGRP:{day}\n")
            for event_title, stream_url in events:
                f.write(f"#EXTINF:-1 group-title=\"{day}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {event_title}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"{stream_url}\n")

    print(f"File M3U8 aggiornato con successo: {file_path}")

# Esegui lo script
if __name__ == "__main__":
    lines = fetch_page_content()
    if not lines:
        print("Impossibile caricare il contenuto della pagina.")
    else:
        events_by_day = extract_events_and_streams(lines)
        if events_by_day:
            update_m3u_file(events_by_day)
        else:
            print("Nessun evento o flusso .php trovato nella pagina.")
