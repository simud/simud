import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Prefisso del sito definito direttamente nello script
SITE_PREFIX = "Skystreaming"

# Funzione per trovare il dominio di Skystreaming dal sito giardiniblog.it
def find_skystreaming_domain():
    target_url = "https://www.giardiniblog.it/migliori-siti-streaming-calcio/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    }
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.text.lower()
            if 'skystreaming' in text or 'skystreaming' in href.lower():
                domain_match = re.match(r'(https?://[^/]+)', href)
                if domain_match:
                    return domain_match.group(1) + "/"
        print("Nessun dominio Skystreaming trovato su giardiniblog.it")
        return None
    except requests.RequestException as e:
        print(f"Errore durante lo scraping di {target_url}: {e}")
        return None

# Trova il dominio di Skystreaming
new_domain = find_skystreaming_domain()
if new_domain:
    SITE_URL = new_domain
    print(f"Dominio Skystreaming trovato: {SITE_URL}")
else:
    SITE_URL = "https://skystreaming.yoga/"  # Fallback se non trovato
    print(f"Dominio Skystreaming non trovato, utilizzato il dominio di fallback: {SITE_URL}")

# Aggiorna gli headers con il nuovo SITE_URL
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": SITE_URL.rstrip('/'),
    "Referer": SITE_URL.rstrip('/')
}

# Immagine fissa da usare per tutti i canali e gruppi
DEFAULT_IMAGE_URL = "https://seekvectorlogo.com/wp-content/uploads/2021/12/sky-for-business-vector-logo-2021.png"

# Funzione per leggere i flussi esistenti dal file M3U8
def read_existing_streams(m3u_file="skystreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)
    existing_streams = []

    if os.path.exists(file_path):
        current_group = "Eventi"  # Default se non specificato
        current_channel = None
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#EXTGRP:"):
                    current_group = line.replace("#EXTGRP:", "").split(" tvg-logo=")[0]
                elif line.startswith("#EXTINF:"):
                    current_channel = line.split(",")[-1].strip()
                elif line and not line.startswith("#"):
                    if current_channel:
                        existing_streams.append((current_channel, line, current_group))
                    current_channel = None

    print(f"Trovati {len(existing_streams)} flussi esistenti nel file M3U8.")
    return existing_streams

# Funzione per trovare le sottocategorie
def find_subcategories():
    try:
        response = requests.get(SITE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        subcategories = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(SITE_URL, href)
            if re.match(r'.*/channel/video/[^/]+/?$', full_url) and SITE_URL in full_url:
                subcategories.add(full_url)

        print(f"Trovate {len(subcategories)} sottocategorie: {list(subcategories)}")
        return list(subcategories)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle sottocategorie: {e}")
        return []

# Funzione per trovare i link alle pagine evento
def find_event_pages(subcategory_url):
    try:
        response = requests.get(subcategory_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(SITE_URL, href)
            if (re.match(r'.*/view/[^/]+/[^/]+/?$', full_url) or 
                re.match(r'.*/view/[^/]+/[A-Za-z0-9]+$', full_url)) and SITE_URL in full_url:
                event_links.add(full_url)

        print(f"Trovati {len(event_links)} eventi nella sottocategoria {subcategory_url}")
        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {subcategory_url}: {e}")
        return []

# Funzione per estrarre il flusso video
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

# Funzione per rimuovere i canali "clone"
def remove_clone_channels(m3u_file="skystreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)
    
    if not os.path.exists(file_path):
        print(f"File M3U8 non trovato: {file_path}")
        return

    streams = []
    current_group = "Eventi"
    current_channel = None
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#EXTGRP:"):
                current_group = line.replace("#EXTGRP:", "").split(" tvg-logo=")[0]
            elif line.startswith("#EXTINF:"):
                current_channel = line.split(",")[-1].strip()
            elif line and not line.startswith("#"):
                if current_channel:
                    streams.append((current_channel, line, current_group))
                current_channel = None

    unique_streams = {}
    for channel_name, stream_url, group in streams:
        unique_streams[stream_url] = (channel_name, stream_url, group)

    print(f"Trovati {len(unique_streams)} flussi unici dopo la rimozione dei cloni.")

    groups = {}
    for channel_name, stream_url, group in unique_streams.values():
        if group not in groups:
            groups[group] = []
        groups[group].append((channel_name, stream_url))

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for group, channels in sorted(groups.items()):
            channels.sort(key=lambda x: x[0].lower())
            f.write(f"#EXTGRP:{group} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {channel_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")

    print(f"File M3U8 aggiornato con cloni rimossi: {file_path}")

# Funzione per aggiornare il file M3U8
def update_m3u_file(video_streams, existing_streams, m3u_file="skystreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Combina flussi esistenti e nuovi
    all_streams = existing_streams.copy()
    for event_url, stream_url, element in video_streams:
        if stream_url:
            channel_name = extract_channel_name(event_url, element)
            # Assegna il gruppo in base a parole chiave nel nome del canale
            channel_name_lower = channel_name.lower()
            if "serie" in channel_name_lower or "diretta goal" in channel_name_lower:
                group = "Diretta Goal"
            elif "sport" in channel_name_lower:
                group = "Sky Sport Backup SD"
            elif "film" in channel_name_lower or "cinema" in channel_name_lower:
                group = "Sky Cinema Backup SD"
            else:
                group = "Eventi Sky Streaming"  # Gruppo di default
            all_streams.append((channel_name, stream_url, group))

    # Organizza i flussi per gruppo
    groups = {}
    for channel_name, stream_url, group in all_streams:
        if group not in groups:
            groups[group] = []
        groups[group].append((channel_name, stream_url))

    # Scrivi il file M3U8
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        # Ordina i gruppi in un ordine specifico
        group_order = [
            "Diretta Goal",
            "Eventi Sky Streaming",
            "Sky Sport Backup SD",
            "Sky Cinema Backup SD"
        ]
        for group in group_order:
            if group in groups:
                channels = groups[group]
                channels.sort(key=lambda x: x[0].lower())
                f.write(f"#EXTGRP:{group} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
                for channel_name, link in channels:
                    f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {channel_name}\n")
                    f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                    f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                    f.write(f"{link}\n")

    print(f"File M3U8 generato con successo: {file_path}")

    # Rimuovi i cloni
    remove_clone_channels(m3u_file)

# Esegui lo script
if __name__ == "__main__":
    existing_streams = read_existing_streams()
    subcategories = find_subcategories()
    if not subcategories:
        print("Nessuna sottocategoria trovata.")
        exit()

    all_event_pages = []
    for subcategory in subcategories:
        print(f"Analizzo sottocategoria: {subcategory}")
        event_pages = find_event_pages(subcategory)
        all_event_pages.extend(event_pages)
        time.sleep(1)

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
            time.sleep(1)

        if video_streams or existing_streams:
            update_m3u_file(video_streams, existing_streams)
        else:
            print("Nessun flusso video trovato e nessun flusso esistente.")
