import requests
import re
import os
from bs4 import BeautifulSoup

# Single URL variable to control base_url, Origin, and Referer
SITE_URL = "https://skystreaming.help/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": SITE_URL.rstrip('/'),
    "Referer": SITE_URL.rstrip('/')
}

# Immagine fissa da usare per tutti i canali e gruppi
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Funzione per trovare i link alle pagine evento
def find_event_pages():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'/view/[^/]+/[^/]+', href):
                full_url = SITE_URL + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://skystreaming\.help/view/[^/]+/[^/]+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

# Funzione per estrarre il flusso video dalla pagina evento
def get_video_stream(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                return src, iframe

        for embed in soup.find_all('embed'):
            src = embed.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                return src, embed

        for video in soup.find_all('video'):
            src = video.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                return src, video
            for source in video.find_all('source'):
                src = source.get('src')
                if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                    return src, source

        return None, None

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, None

# Funzione per estrarre il nome del canale
def extract_channel_name(event_url, element):
    event_name_match = re.search(r'/view/([^/]+)/[^/]+', event_url)
    if event_name_match:
        return event_name_match.group(1).replace('-', ' ').title()
    
    name_match = re.search(r'([^/]+?)(?:\.(m3u8|mp4|ts|html|php))?$', event_url)
    if name_match:
        return name_match.group(1).replace('-', ' ').title()
    
    parent = element.find_parent() if element else None
    if parent and parent.text.strip():
        return parent.text.strip()[:50].replace('\n', ' ').title()
    
    return "Unknown Channel"

# Funzione per aggiornare il file M3U8 con l'immagine fissa per gruppi e canali
def update_m3u_file(video_streams, m3u_file="skystreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Scrivi il file aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
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

        # Ordinamento alfabetico dei canali all'interno di ciascun gruppo
        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())
            # Aggiungi il logo al gruppo usando tvg-logo
            f.write(f"#EXTGRP:{group} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {channel_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")

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
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
