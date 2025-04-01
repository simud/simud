import requests
import re
import os
from bs4 import BeautifulSoup

# URL di partenza (pagina con elenco eventi)
base_url = "https://calcio.tires/"
start_url = "https://calcio.tires/streaming-gratis-calcio-1.php"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://calcio.tires",
    "Referer": "https://calcio.tires/"
}

# Immagine fissa da usare per tutti i canali
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Funzione per trovare i link alle pagine evento
def find_event_pages():
    try:
        response = requests.get(start_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Pattern generico per link a eventi - da personalizzare
            if re.match(r'/live/[^/]+', href):  # Esempio: /live/arsenal-vs-fulham
                full_url = base_url + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://calcio\.tires/live/[^/]+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

# Funzione per estrarre tutti i flussi video dalla pagina evento
def get_all_video_streams(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        streams = []
        # Cerca tutti gli iframe
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                streams.append((src, iframe))

        # Cerca tutti gli embed
        for embed in soup.find_all('embed'):
            src = embed.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                streams.append((src, embed))

        # Cerca tutti i video
        for video in soup.find_all('video'):
            src = video.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                streams.append((src, video))
            for source in video.find_all('source'):
                src = source.get('src')
                if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                    streams.append((src, source))

        return streams if streams else [(None, None)]

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return [(None, None)]

# Funzione per estrarre il nome del canale
def extract_channel_name(event_url, element, stream_index):
    # Estrai il nome dall'URL (es. /live/arsenal-vs-fulham -> "Arsenal Vs Fulham")
    event_name_match = re.search(r'/live/([^/]+)', event_url)
    if event_name_match:
        base_name = event_name_match.group(1).replace('-', ' ').title()
        return f"{base_name} Player {stream_index + 1}"
    
    name_match = re.search(r'([^/]+?)(?:\.(m3u8|mp4|ts|html|php))?$', event_url)
    if name_match:
        base_name = name_match.group(1).replace('-', ' ').title()
        return f"{base_name} Player {stream_index + 1}"
    
    parent = element.find_parent() if element else None
    if parent and parent.text.strip():
        base_name = parent.text.strip()[:50].replace('\n', ' ').title()
        return f"{base_name} Player {stream_index + 1}"
    
    return f"Unknown Channel Player {stream_index + 1}"

# Funzione per aggiornare il file M3U8 con più flussi per evento
def update_m3u_file(video_streams, m3u_file="calcio_tires_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Scrivi il file aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        groups = {}
        for event_url, stream_list in video_streams:
            for index, (stream_url, element) in enumerate(stream_list):
                if not stream_url:
                    continue
                channel_name = extract_channel_name(event_url, element, index)
                group = "Sport"  # Gruppo fisso dato che è un sito di calcio
                
                if group not in groups:
                    groups[group] = []
                groups[group].append((channel_name, stream_url))

        # Ordinamento alfabetico dei canali all'interno di ciascun gruppo
        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())
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
            streams = get_all_video_streams(event_url)
            if any(stream_url for stream_url, _ in streams):
                video_streams.append((event_url, streams))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
