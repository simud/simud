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

# Immagine fissa per tutti i canali e gruppi
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
        print("Contenuto della pagina ricevuto con successo. Prime 10 righe:")
        lines = response.text.splitlines()
        for i, line in enumerate(lines[:10], 1):
            print(f"Riga {i}: {line}")
        return lines
    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {SITE_URL}: {e}")
        return []

# Funzione per estrarre eventi e URL .php, organizzati per giorno
def extract_events_and_streams(lines):
    events_by_day = {}
    current_day = None

    event_pattern = re.compile(r'(\d{2}:\d{2})\s+(.+?)\s+\|\s+(https://sportzonline\.ps/channels/[^\s]+\.php)')

    print("\nAnalisi delle righe per trovare eventi:")
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line in DAY_TRANSLATION:
            current_day = DAY_TRANSLATION[line]
            if current_day not in events_by_day:
                events_by_day[current_day] = []
            print(f"Trovato giorno: {current_day}")
        elif current_day:
            match = event_pattern.search(line)
            if match:
                time, event_title, stream_url = match.groups()
                full_title = f"{time} {event_title}"
                events_by_day[current_day].append((full_title, stream_url))
                print(f"Trovato evento (riga {i}): {full_title} | {stream_url}")
            else:
                print(f"Nessun evento trovato (riga {i}): {line}")

    return events_by_day

# Funzione per aggiornare il file M3U8
def update_m3u_file(events_by_day, m3u_file="sportsonline_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Controlla se il file esiste prima
    if os.path.exists(file_path):
        print(f"File {file_path} esiste già. Contenuto prima della modifica:")
        with open(file_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print(f"File {file_path} non esiste ancora, verrà creato.")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            
            for day, events in events_by_day.items():
                if not events:
                    print(f"Nessun evento per il giorno: {day}")
                    continue
                events.sort(key=lambda x: x[0].split()[0])
                f.write(f"#EXTGRP:{day} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
                for event_title, stream_url in events:
                    f.write(f"#EXTINF:-1 group-title=\"{day}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {event_title}\n")
                    f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                    f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                    f.write(f"{stream_url}\n")
        print(f"File M3U8 aggiornato con successo: {file_path}")
    except Exception as e:
        print(f"Errore durante la scrittura del file M3U8: {e}")

    # Verifica il contenuto dopo la scrittura
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            print("\nContenuto del file M3U8 dopo la modifica:")
            print(f.read())
    else:
        print(f"Errore: il file {file_path} non è stato creato.")

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
