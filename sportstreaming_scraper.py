import requests
import re
import os
from bs4 import BeautifulSoup

# URL di partenza (homepage o pagina con elenco eventi)
base_url = "https://www.sportstreaming.net/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://www.sportstreaming.net",
    "Referer": "https://www.sportstreaming.net/"
}

# Immagine fissa da usare per tutti i canali
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Funzione per trovare i link alle pagine evento
def find_event_pages():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        event_links = set()
        # Cerca link che corrispondano a /live-[numero] o /live-perma-[numero]
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'/live-(perma-)?\d+', href):
                full_url = base_url + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://www\.sportstreaming\.net/live-(perma-)?\d+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

# Funzione per estrarre il flusso video e la descrizione dalla pagina evento
def get_video_stream_and_description(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Cerca il flusso video
        stream_url = None
        element = None
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                stream_url = src
                element = iframe
                break

        if not stream_url:
            for embed in soup.find_all('embed'):
                src = embed.get('src')
                if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                    stream_url = src
                    element = embed
                    break

        if not stream_url:
            for video in soup.find_all('video'):
                src = video.get('src')
                if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                    stream_url = src
                    element = video
                    break
                for source in video.find_all('source'):
                    src = source.get('src')
                    if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                        stream_url = src
                        element = source
                        break

        # Cerca la descrizione nella pagina evento
        channel_name = "Unknown Channel"
        if element:
            # Cerca un <p>, <div> o <h*> subito dopo l'elemento del flusso
            next_element = element.find_next(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if next_element and next_element.get_text(strip=True):
                # Prendi solo la prima riga della descrizione e sostituisci trattini con spazi
                channel_name = next_element.get_text(strip=True).split('\n')[0].strip()
                channel_name = re.sub(r'[-_]+', ' ', channel_name)  # Sostituisci trattini o underscore con spazio
            else:
                # Fallback: cerca il primo <p> o <h*> nella pagina
                description = soup.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if description and description.get_text(strip=True):
                    channel_name = description.get_text(strip=True).split('\n')[0].strip()
                    channel_name = re.sub(r'[-_]+', ' ', channel_name)  # Sostituisci trattini o underscore con spazio

        return stream_url, element, channel_name

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, None, "Unknown Channel"

# Funzione per aggiornare il file M3U8 con i nomi estratti dalla descrizione
def update_m3u_file(video_streams, m3u_file="sportstreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Scrivi il file aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        groups = {}
        for event_url, stream_url, element, channel_name in video_streams:
            if not stream_url:
                continue
            # Tutto viene messo nel gruppo "Sport" dato che il sito è sportstreaming
            group = "Eventi"
            
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
            stream_url, element, channel_name = get_video_stream_and_description(event_url)
            if stream_url:
                video_streams.append((event_url, stream_url, element, channel_name))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
