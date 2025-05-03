import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# URL base del sito
SITE_URL = "https://altadefinizionegratis.sbs"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Origin": SITE_URL.rstrip('/'),
    "Referer": SITE_URL.rstrip('/')
}

# Funzione per trovare i link alle pagine dei film/serie
def find_movie_pages():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        movie_links = set()

        # Trova tutti i collegamenti a film/serie
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'/film/[^/]+', href):
                full_url = urljoin(SITE_URL, href)
                movie_links.add(full_url)

        return list(movie_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine dei film: {e}")
        return []

# Funzione per estrarre il flusso video dalla pagina del film
def get_video_stream(movie_url):
    try:
        response = requests.get(movie_url, headers=headers)
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
        print(f"Errore durante l'accesso a {movie_url}: {e}")
        return None, None

# Funzione per estrarre il nome del film
def extract_movie_name(movie_url, element):
    movie_name_match = re.search(r'/film/([^/]+)', movie_url)
    if movie_name_match:
        return movie_name_match.group(1).replace('-', ' ').title()

    name_match = re.search(r'([^/]+?)(?:\.(m3u8|mp4|ts|html|php))?$', movie_url)
    if name_match:
        return name_match.group(1).replace('-', ' ').title()

    parent = element.find_parent() if element else None
    if parent and parent.text.strip():
        return parent.text.strip()[:50].replace('\n', ' ').title()

    return "Unknown Movie"

# Funzione per aggiornare il file M3U8 con i film trovati
def update_m3u_file(video_streams, m3u_file="streaming.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Scrivi il file aggiornato
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for movie_url, stream_url, element in video_streams:
            if not stream_url:
                continue
            movie_name = extract_movie_name(movie_url, element)
            f.write(f"#EXTINF:-1, {movie_name}\n")
            f.write(f"{stream_url}\n")

    print(f"File M3U8 aggiornato con successo: {file_path}")

# Esegui lo script
if __name__ == "__main__":
    movie_pages = find_movie_pages()
    if not movie_pages:
        print("Nessuna pagina di film trovata.")
    else:
        video_streams = []
        for movie_url in movie_pages:
            print(f"Analizzo: {movie_url}")
            stream_url, element = get_video_stream(movie_url)
            if stream_url:
                video_streams.append((movie_url, stream_url, element))
            else:
                print(f"Nessun flusso trovato per {movie_url}")

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine dei film.")