import requests
import re
import os
from bs4 import BeautifulSoup

# URL di partenza
base_url = "https://guardacalcio.art/partite-streaming.html"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://guardacalcio.art",
    "Referer": "https://guardacalcio.art/"
}

# Immagine fissa da usare per tutti i canali
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Canale ADMIN da aggiungere alla fine
ADMIN_CHANNEL = '''#EXTINF:-1 tvg-id="ADMIN" tvg-name="ADMIN" tvg-logo="https://i.postimg.cc/4ysKkc1G/photo-2025-03-28-15-49-45.png" group-title="Eventi", ADMIN
https://static.vecteezy.com/system/resources/previews/033/861/932/mp4/gherkins-close-up-loop-free-video.mp4'''

# Funzione per trovare i link alle partite
def find_event_pages():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        # Cerca link che potrebbero portare a pagine di streaming
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Filtra link che sembrano relativi a streaming o partite
            if re.search(r'streaming|partita|watch|live', href, re.IGNORECASE):
                if href.startswith('/'):
                    full_url = "https://guardacalcio.art" + href
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                event_links.add(full_url)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

# Funzione per estrarre il flusso video e la descrizione dalla pagina della partita
def get_video_stream_and_description(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stream_url = None
        element = None
        # Cerca iframe che potrebbero contenere il flusso video
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and re.search(r'\.(m3u8|mp4|ts|html|php)|stream|player', src, re.IGNORECASE):
                stream_url = src
                element = iframe
                break

        # Cerca embed se non trovato in iframe
        if not stream_url:
            for embed in soup.find_all('embed'):
                src = embed.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts|html|php)|stream|player', src, re.IGNORECASE):
                    stream_url = src
                    element = embed
                    break

        # Cerca video tag
        if not stream_url:
            for video in soup.find_all('video'):
                src = video.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts)|stream|player', src, re.IGNORECASE):
                    stream_url = src
                    element = video
                    break
                for source in video.find_all('source'):
                    src = source.get('src')
                    if src and re.search(r'\.(m3u8|mp4|ts)|stream|player', src, re.IGNORECASE):
                        stream_url = src
                        element = source
                        break

        # Estrai il nome del canale (es. "Inter - Milan")
        channel_name = "Unknown Match"
        if element:
            # Cerca il testo vicino all'elemento (es. titolo partita)
            next_element = element.find_previous(['h1', 'h2', 'h3', 'div', 'p'])
            if next_element and next_element.get_text(strip=True):
                channel_name = next_element.get_text(strip=True).split('\n')[0].strip()
                channel_name = re.sub(r'[-_]+', ' ', channel_name)
            else:
                # Fallback: cerca il titolo della pagina
                title = soup.find('title')
                if title and title.get_text(strip=True):
                    channel_name = title.get_text(strip=True).split('|')[0].strip()
                    channel_name = re.sub(r'[-_]+', ' ', channel_name)

        return stream_url, element, channel_name

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, None, "Unknown Match"

# Funzione per aggiornare il file M3U8
def update_m3u_file(video_streams, m3u_file="guardacalcio_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        groups = {}
        for event_url, stream_url, element, channel_name in video_streams:
            if not stream_url:
                continue
            group = "Partite"
            
            if group not in groups:
                groups[group] = []
            groups[group].append((channel_name, stream_url))

        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {channel_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")
        
        # Aggiungi il canale ADMIN alla fine
        f.write("\n")
        f.write(ADMIN_CHANNEL)

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
            stream_url, element, channel_name = get_video_stream_and_description(event_url)
            if stream_url:
                video_streams.append((event_url, stream_url, element, channel_name))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
