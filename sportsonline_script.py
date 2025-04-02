import requests
import re
import os

# Single URL variable to control base_url, Origin, and Referer
SITE_URL = "https://sportsonline.gl/prog.txt"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://sportzonline.gl",
    "Referer": "https://sportsonline.gl/"
}

# Fixed image to use for all channels and groups
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Dictionary to translate days to Italian
DAY_TRANSLATION = {
    "MONDAY": "Lunedì",
    "TUESDAY": "Martedì",
    "WEDNESDAY": "Mercoledì",
    "THURSDAY": "Giovedì",
    "FRIDAY": "Venerdì",
    "SATURDAY": "Sabato",
    "SUNDAY": "Domenica"
}

# Function to fetch the page content
def fetch_page_content():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()
        return response.text.splitlines()
    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {SITE_URL}: {e}")
        return []

# Function to extract events and streams, organized by day
def extract_events_and_streams(lines):
    events_by_day = {}
    current_day = None

    event_pattern = re.compile(r'(\d{2}:\d{2})\s+(.+?)\s+\|\s+(https://sportzonline\.ps/[^ ]+\.php)')

    for line in lines:
        line = line.strip()
        # Check if the line is a day
        if line in DAY_TRANSLATION:
            current_day = DAY_TRANSLATION[line]
            events_by_day[current_day] = []
        # Check if the line matches an event pattern
        elif current_day:
            match = event_pattern.search(line)
            if match:
                time, event_title, stream_url = match.groups()
                full_title = f"{time} {event_title}"
                events_by_day[current_day].append((full_title, stream_url))

    return events_by_day

# Function to update the M3U8 file with events grouped by day
def update_m3u_file(events_by_day, m3u_file="sportsonline_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for day, events in events_by_day.items():
            if not events:
                continue
            # Sort events by time and title
            events.sort(key=lambda x: (x[0].split()[0], x[0].lower()))
            # Add the day as a group with the fixed logo
            f.write(f"#EXTGRP:{day} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
            for event_title, stream_url in events:
                f.write(f"#EXTINF:-1 group-title=\"{day}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {event_title}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{stream_url}\n")

    print(f"File M3U8 aggiornato con successo: {file_path}")

# Execute the script
if __name__ == "__main__":
    lines = fetch_page_content()
    if not lines:
        print("Impossibile caricare il contenuto della pagina.")
    else:
        events_by_day = extract_events_and_streams(lines)
        if events_by_day:
            update_m3u_file(events_by_day)
        else:
            print("Nessun evento o flusso trovato nella pagina.")
