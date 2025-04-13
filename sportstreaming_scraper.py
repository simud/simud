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
                full_url = base_url + href.lstrip('/')
                event_links.add(full_url)
            elif re.match(r'https://www\.sportstreaming\.net/live-(perma-)?\d+', href):
                event_links.add(href)

        return list(event_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

def get_video_stream_and_description(event_url):
    try:
        response = requests.get(event_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        stream_url = None
        element = None
        for tag in ['iframe', 'embed', 'video']:
            for el in soup.find_all(tag):
                src = el.get('src') or (el.find('source').get('src') if el.name == 'video' and el.find('source') else None)
                if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                    stream_url = src
                    element = el
                    break
            if stream_url:
                break

        # Titolo
        channel_name = "Unknown Channel"
        if element:
            next_element = element.find_next(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if next_element and next_element.get_text(strip=True):
                channel_name = next_element.get_text(strip=True).split('\n')[0].strip()
        if not channel_name or channel_name == "Unknown Channel":
            description = soup.find(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if description and description.get_text(strip=True):
                channel_name = description.get_text(strip=True).split('\n')[0].strip()

        # Pulisci nome
        channel_name = re.sub(r'[-_]+', ' ', channel_name)
        channel_name = re.sub(r'\s+', ' ', channel_name).strip().title()

        # Data/ora dell’evento dal titolo (es. 13/04 - 20:45)
        event_datetime = None
        match = re.search(r'(\d{1,2}/\d{1,2})[^\d]*(\d{1,2}:\d{2})', channel_name)
        if match:
            try:
                day_month = match.group(1)
                time = match.group(2)
                full_str = f"{day_month} {time}"
                event_datetime = datetime.strptime(full_str, "%d/%m %H:%M")
                now = datetime.now()
                event_datetime = event_datetime.replace(year=now.year)
            except Exception:
                pass

        # Copertina (immagine vicino al player)
        image_url = DEFAULT_IMAGE_URL
        if element:
            for img in element.find_all_next('img', limit=3):
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

        # Ordina per data e nome
        video_streams.sort(key=lambda x: (x[4] if x[4] else datetime.max, x[2].lower()))

        for event_url, stream_url, channel_name, image_url, event_datetime in video_streams:
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
                video_streams.append((event_url, stream_url, channel_name, image_url, event_datetime))
            else:
                print(f"Nessun flusso trovato per {event_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
