import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Variabili di configurazione
SITE_URL = "https://altadefinizionegratis.sbs"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": SITE_URL.rstrip('/'),
    "Referer": SITE_URL.rstrip('/')
}

DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Funzione per trovare i link ai film/serie dalla home page
def find_movie_pages():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trova tutti i collegamenti ai film/serie dalla home
        movie_links = set()

        # Identifica i titoli dei film/serie dalla struttura della pagina
        for a in soup.find_all('a', href=True):
            href = a['href']
            title = a.get_text(strip=True)
            
            # Verifica se il link contiene il formato del film (ad esempio "streaming gratis")
            if re.match(r'/[^/]+-streaming-gratis\.html', href) and title:
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

        # Trova il flusso video nelle pagine degli iframe, embed o video
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts|html|php)', src, re.IGNORECASE)):
                return src, iframe

        # In alternativa cerca nei tag video
        for video in soup.find_all('video'):
            src = video.get('src')
            if src and ("stream" in src.lower() or re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE)):
                return src, video

        return None, None

    except requests.RequestException as e:
        print(f"Errore durante l'accesso a {movie_url}: {e}")
        return None, None

# Funzione per estrarre il nome del film
def extract_movie_name(movie_url, element):
    movie_name_match = re.search(r'/([^/]+)-streaming-gratis\.html', movie_url)
    if movie_name_match:
        return movie_name_match.group(1).replace('-', ' ').title()

    return "Unknown Movie"

# Funzione per aggiornare il file M3U8 con i flussi video
def update_m3u_file(video_streams, m3u_file="streaming.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    # Scrivi il file M3U8
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        groups = {}
        for movie_url, stream_url, element in video_streams:
            if not stream_url:
                continue
            movie_name = extract_movie_name(movie_url, element)
            group = "Film"

            if group not in groups:
                groups[group] = []
            groups[group].append((movie_name, stream_url))

        # Ordinamento alfabetico dei film
        for group, movies in groups.items():
            movies.sort(key=lambda x: x[0].lower())
            # Aggiungi il logo al gruppo
            f.write(f"#EXTGRP:{group} tvg-logo=\"{DEFAULT_IMAGE_URL}\"\n")
            for movie_name, link in movies:
                f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {movie_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")

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