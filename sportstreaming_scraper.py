import requests
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime

base_url = "https://www.sportstreaming.net/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://www.sportstreaming.net",
    "Referer": "https://www.sportstreaming.net/"
}

DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

ADMIN_CHANNEL = '''#EXTINF:-1 tvg-id="ADMIN" tvg-name="ADMIN" tvg-logo="https://i.postimg.cc/4ysKkc1G/photo-2025-03-28-15-49-45.png" group-title="Eventi", ADMIN
https://static.vecteezy.com/system/resources/previews/033/861/932/mp4/gherkins-close-up-loop-free-video.mp4'''

def find_event_pages():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'/live-(perma-)?\d+', href):
                event_links.add(base_url + href.lstrip('/'))
            elif re.match(r'https://www\.sportstreaming\.net/live-(perma-)?\d+', href):
                event_links.add(href)
        return list(event_links)
    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

def extract_event_datetime(text):
    # Cerca date nel formato italiano: 13 Aprile 2025 - 20:45
    match = re.search(r'(\d{1,2})\s([A-Za-z]+)\s(\d{4})\s*[-–—]?\s*(\d{1,2}):(\d{2})', text)
    if match:
        day, month_text, year, hour, minute = match.groups()
        months = {
            "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5,
            "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9,
            "ottobre": 10, "novembre": 11, "dicembre": 12
        }
        month = months.get(month_text.lower())
        if month:
            try:
                return datetime(int(year), month, int(day), int(hour), int(minute))
            except ValueError:
                return None
    return None

def clean_channel_name(name):
    name = re.sub(r'[-_]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

def get_video_stream_and_description(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

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

        channel_name = "Unknown Channel"
        event_datetime = None
        if element:
            next_el = element.find_next(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if next_el:
                text = next_el.get_text(strip=True)
                event_datetime = extract_event_datetime(text)
                channel_name = clean_channel_name(text)
        if channel_name == "Unknown Channel":
            h = soup.find(['h1', 'h2', 'h3'])
            if h:
                channel_name = clean_channel_name(h.get_text(strip=True))
                if not event_datetime:
                    event_datetime = extract_event_datetime(channel_name)

        image_url = DEFAULT_IMAGE_URL
        for img in soup.find_all('img'):
            img_src = img.get('src')
            if img_src and re.search(r'\.(jpg|jpeg|png|webp)$', img_src, re.IGNORECASE):
                if not img_src.startswith("http"):
                    img_src = base_url + img_src.lstrip("/")
                image_url = img_src
                break

        return stream_url, element, channel_name, image_url, event_datetime

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, None, "Unknown Channel", DEFAULT_IMAGE_URL, None

def update_m3u_file(video_streams, m3u_file="sportstreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        # Ordina prima per data, poi per nome
        video_streams.sort(key=lambda x: (x[4] or datetime.max, x[2].lower()))

        for event_url, stream_url, element, channel_name, image_url, event_datetime in video_streams:
            if not stream_url:
                continue
            f.write(f"#EXTINF:-1 group-title=\"Eventi\" tvg-logo=\"{image_url}\", {channel_name}\n")
            f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
            f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
            f.write(f"{stream_url}\n")

        f.write("\n")
        f.write(ADMIN_CHANNEL)

    print(f"File M3U8 aggiornato con successo: {file_path}")

if __name__ == "__main__":
    event_pages = find_event_pages()
    if not event_pages:
        print("Nessuna pagina evento trovata.")
    else:
        video_streams = []
        for event_url in event_pages:
            print(f"Analizzo: {event_url}")
            stream_url, element, channel_name, image_url, event_datetime = get_video_stream_and_description(event_url)
            if stream_url:
                video_streams.append((event_url, stream_url, element, channel_name, image_url, event_datetime))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
