import requests
import re
import os
from bs4 import BeautifulSoup

# Single URL variable to control base_url, Origin, and Referer
SITE_URL = "https://sportsonline.gl/prog.txt"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://sportsonline.gl",
    "Referer": "https://sportsonline.gl/"
}

# Fixed image to use for all channels and groups
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Dictionary to translate days to Italian
DAY_TRANSLATION = {
    "Monday": "Lunedì",
    "Tuesday": "Martedì",
    "Wednesday": "Mercoledì",
    "Thursday": "Giovedì",
    "Friday": "Venerdì",
    "Saturday": "Sabato",
    "Sunday": "Domenica"
}

# Function to fetch and parse the page content
def fetch_page_content():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {SITE_URL}: {e}")
        return None

# Function to extract events and streams, organized by day
def extract_events_and_streams(soup):
    if not soup:
        return {}

    events_by_day = {}
    current_day = None

    # Find all text and links in the page
    for element in soup.find_all(['p', 'div', 'span', 'a'], recursive=True):
        text = element.get_text(strip=True)
        if text in DAY_TRANSLATION:
            current_day = DAY_TRANSLATION[text]
            events_by_day[current_day] = []
        elif current_day and element.name == 'a' and 'href' in element.attrs:
            href = element['href']
            if re.search(r'\.(m3u8|mp4|ts|html|php)', href, re.IGNORECASE):
                # Look for the event title before the link (e.g., "12:00 ATP World Tour 250: Marrakech")
                prev_text = element.find_previous(string=True, recursive=False)
                if prev_text:
                    event_title = prev_text.strip()
                    if event_title and not event_title.startswith('http'):
                        events_by_day[current_day].append((event_title, href))

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
            # Sort events alphabetically by title
            events.sort(key=lambda x: x[0].lower())
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
    soup = fetch_page_content()
    if not soup:
        print("Impossibile caricare il contenuto della pagina.")
    else:
        events_by_day = extract_events_and_streams(soup)
        if events_by_day:
            update_m3u_file(events_by_day)
        else:
            print("Nessun evento o flusso trovato nella pagina.")
