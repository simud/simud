import requests
import re
import os
from bs4 import BeautifulSoup
from datetime import datetime

base_url = "https://www.sportstreaming.net/"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": base_url,
    "Referer": base_url
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
                full_url = base_url + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://www\.sportstreaming\.net/live-(perma-)?\d+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

def extract_event_datetime(soup):
    text = soup.get_text()
    match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2})', text)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")
        except ValueError:
            return None
    return None

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
        if element:
            next_element = element.find_next(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if next_element and next_element.get_text(strip=True):
                channel_name = next_element.get_text(strip=True).split('\n')[0].strip()
            else:
                description = soup.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if description and description.get_text(strip=True):
                    channel_name = description.get_text(strip=True).split('\n')[0].strip()
        channel_name = re.sub(r'[-_]+', ' ', channel_name)

        event_datetime = extract_event_datetime(soup)

        image_url = DEFAULT_IMAGE_URL
        if element:
            for img in element.find_all_next('img', limit=5):
                img_src = img.get('src')
                if img_src and re.search(r'\.(jpg|jpeg|png|webp)$', img_src, re.IGNORECASE):
                    if not img_src.startswith("http"):
                        img_src = base_url + img_src.lstrip("/")
                    if not re.search(r'/live\d+\.png$', img_src):
                        image_url = img_src
                        break

        return stream_url, channel_name, image_url, event_datetime

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, "Unknown Channel", DEFAULT_IMAGE_URL, None

def update_m3u_file(video_streams, m3u_file="sportstreaming_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        video_streams.sort(key=lambda x: (x[3] or datetime.max, x[1].lower()))

        for stream_url, channel_name, image_url, event_datetime in video_streams:
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
            stream_url, channel_name, image_url, event_datetime = get_video_stream_and_description(event_url)
            if stream_url:
                video_streams.append((stream_url, channel_name, image_url, event_datetime))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
