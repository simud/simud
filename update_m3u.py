import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Single URL variable to control base_url, Origin, and Referer
SITE_URL = "https://skystreaming.help/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": SITE_URL.rstrip('/'),
    "Referer": SITE_URL.rstrip('/')
}

# Immagine fissa da usare per tutti i canali e gruppi
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Funzione per trovare le sottocategorie (es. /channel/video/serie-a)
def find_subcategories():
    try:
        response = requests.get(SITE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        subcategories = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(SITE_URL, href)
            # Cerca sottocategorie come /channel/video/...
            if re.match(r'.*/channel/video/[^/]+/?$', full_url) and SITE_URL in full_url:
                subcategories.add(full_url)

        print(f"Trovate {len(subcategories)} sottocategorie: {list(subcategories)}")
        return list(subcategories)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle sottocategorie: {e}")
        return []

# Funzione per trovare i link alle pagine evento da una sottocategoria
def find_event_pages(subcategory_url):
    try:
        response = requests.get(subcategory_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(SITE_URL, href)
            # Cerca pattern di URL evento (es. /view/...)
            if (re.match(r'.*/view/[^/]+/[^/]+/?$',	full_url) or 
                re.match(r'.*/view/[^/]+/[A-Za-z0-9]+$', full_url)) and SITE_URL in full_url:
                event_links.add(full_url)

        print(f"Trovati {len(event_links)} eventi nella sottocategoria {subcategory_url}: {list(event_links)}")
        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {subcategory_url}: {e}")
        return []

# Funzione per estrarre il flusso video dalla pagina evento
def get_video_stream(event_url):
    try:
        response = requests.get(event_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and re.search(r'\.(m3u8|mp4|ts|html|php)|stream', src, re.IGNORECASE):
                return src, iframe

        for embed in soup.find_all('embed'):
            src = embed.get('src')
            if src and re.search(r'\.(m3u8|mp4|ts|html|php)|stream', src, re.IGNORECASE):
                return src, embed

        for video in soup.find_all('video'):
            src = video.get('src')
            if src and re.search(r'\.(m3u8|mp4|ts)|stream', src, re.IGNORECASE):
                return src, video
            for source in video.find_all('source'):
                src = source.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts)|stream', src, re.IGNORECASE):
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
                group = "Dirette Goal"
            elif "film" in channel_name.lower():
                group = "Cinema"
            else:
                group = "Eventi"

            if group not in groups:
                groups[group] = []
            groups[group].append((channel_name, stream_url))

        for group, channels in sorted(groups.items()):
            channels.sort(key=lambda x: x[0].lower())
            f.write(f"#EXTGRP:{group} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {channel_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")

        print(f"File M3U8 aggiornato con successo: {file_path}")

# Esegui lo script
if __name__ == "__main__":
    # Trova tutte le sottocategorie
    subcategories = find_subcategories()
    if not subcategories:
        print("Nessuna sottocategoria trovata.")
        exit()

    # Trova gli eventi in tutte le sottocategorie
    all_event_pages = []
    for subcategory in subcategories:
        print(f"Analizzo sottocategoria: {subcategory}")
        event_pages = find_event_pages(subcategory)
        all_event_pages.extend(event_pages)
        time.sleep(1)  # Ritardo per evitare blocchi del server

    if not all_event_pages:
        print("Nessuna pagina evento trovata in tutte le sottocategorie.")
    else:
        video_streams = []
        for event_url in all_event_pages:
            print(f"Analizzo evento: {event_url}")
            stream_url, element = get_video_stream(event_url)
            if stream_url:
                video_streams.append((event_url, stream_url, element))
            else:
                print(f"Nessun flusso trovato per {event_url}")
            time.sleep(1)  # Ritardo per evitare blocchi del server

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")