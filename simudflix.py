import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

SITE_URL = "https://altadefinizionegratis.sbs/"
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Referer": SITE_URL.rstrip('/'),
    "Origin": SITE_URL.rstrip('/')
}

def find_movie_pages():
    try:
        response = requests.get(SITE_URL, headers=headers)
        response.raise_for_status()

        # DEBUG: Salva la homepage HTML
        with open("debug_homepage.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')
        movie_links = set()

        for a in soup.find_all('a', href=True):
            href = a['href']
            title = a.get_text(strip=True)
            if re.match(r'/[^/]+-streaming(?:-gratis)?\.html', href) and title:
                full_url = urljoin(SITE_URL, href)
                movie_links.add(full_url)

        return list(movie_links)

    except requests.RequestException as e:
        print(f"Errore durante la ricerca delle pagine dei film: {e}")
        return []

def get_embed_link(movie_url):
    try:
        response = requests.get(movie_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                return src, iframe

        return None, None

    except requests.RequestException as e:
        print(f"Errore durante il caricamento della pagina {movie_url}: {e}")
        return None, None

def extract_title(url, element):
    title_match = re.search(r'/([^/]+)-streaming(?:-gratis)?\.html', url)
    if title_match:
        return title_match.group(1).replace('-', ' ').title()

    return element.text.strip()[:50].replace('\n', ' ') if element else "Unknown Title"

def update_m3u_file(video_items, m3u_file="streaming.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for url, embed_url, element in video_items:
            title = extract_title(url, element)
            f.write(f"#EXTINF:-1 group-title=\"Cinema\" tvg-logo=\"{DEFAULT_IMAGE_URL}\",{title}\n")
            f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
            f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
            f.write(f"{embed_url}\n")

    print(f"File M3U8 aggiornato: {file_path}")

if __name__ == "__main__":
    movie_pages = find_movie_pages()
    if not movie_pages:
        print("Nessuna pagina di film trovata.")
    else:
        video_items = []
        for url in movie_pages[:50]:
            print(f"Analizzo: {url}")
            embed_url, element = get_embed_link(url)
            if embed_url:
                video_items.append((url, embed_url, element))
            else:
                print(f"Nessun embed trovato per {url}")

        if video_items:
            update_m3u_file(video_items)
        else:
            print("Nessun embed trovato per le pagine film.")