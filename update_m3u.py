import requests
import re
import os
from bs4 import BeautifulSoup

# ... (il resto del codice rimane invariato fino a create_m3u_file)

# Funzione per aggiornare il file M3U8 esistente
def update_m3u_file(video_streams, m3u_file="skystreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Leggi il contenuto esistente, se il file esiste
    existing_entries = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            current_channel = None
            for line in lines:
                if line.startswith("#EXTINF:"):
                    current_channel = line.strip()
                elif line.startswith("http") and current_channel:
                    existing_entries[current_channel] = line.strip()
                    current_channel = None

    # Prepara i nuovi flussi
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

    # Scrivi il file aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())  # Ordinamento alfabetico
            for channel_name, link in channels:
                extinf = f"#EXTINF:-1 group-title=\"{group}\", {channel_name}\n"
                f.write(extinf)
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")
                # Aggiorna il dizionario delle entries esistenti
                existing_entries[extinf] = link

    print(f"File M3U8 aggiornato con successo: {file_path}")

# Esegui lo script
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
            update_m3u_file(video_streams)  # Usa la nuova funzione
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
