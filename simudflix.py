import requests
import logging
import json
import time
import subprocess
import os
import http.cookiejar
from datetime import datetime

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Intestazioni HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://streamingcommunity.spa/',
    'Connection': 'keep-alive',
}

# URL di base
BASE_URL = "https://streamingcommunity.spa"

# Caricamento dei cookie
COOKIE_FILE = "cookies.txt"
session = requests.Session()
if os.path.exists(COOKIE_FILE):
    cookie_jar = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
    try:
        cookie_jar.load()
        session.cookies = cookie_jar
        logger.debug("Cookies caricati da cookies.txt")
    except Exception as e:
        logger.error(f"Errore nel caricamento di cookies.txt: {e}")
else:
    logger.error("File cookies.txt non trovato. L'autenticazione è necessaria per accedere ai flussi video.")

# Funzione per ottenere i titoli da una categoria
def get_titles_from_category(category_slug):
    api_url = f"{BASE_URL}/api/browse/{category_slug}"
    try:
        logger.debug(f"Richiesta API: {api_url}")
        response = session.get(api_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        titles = data.get('titles', [])
        logger.debug(f"Trovati {len(titles)} titoli nella categoria '{category_slug}'")
        return titles
    except requests.RequestException as e:
        logger.error(f"Errore durante la richiesta API per la categoria '{category_slug}': {e}")
        return []

# Funzione per ottenere il link video utilizzando yt-dlp
def get_video_url(title_id):
    player_url = f"{BASE_URL}/watch/{title_id}"
    try:
        logger.debug(f"Esecuzione yt-dlp per: {player_url}")
        cmd = [
            'yt-dlp', '--get-url', '--user-agent', HEADERS['User-Agent'],
            '--referer', BASE_URL, '--cookies', COOKIE_FILE, player_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        video_url = result.stdout.strip()
        if video_url:
            logger.debug(f"Link video ottenuto: {video_url}")
            return video_url
        else:
            logger.debug("Nessun link video ottenuto da yt-dlp")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Errore durante l'esecuzione di yt-dlp: {e}")
        return None
    except FileNotFoundError:
        logger.error("yt-dlp non trovato. Assicurati che sia installato e nel PATH.")
        return None
    except subprocess.TimeoutExpired:
        logger.error("yt-dlp ha impiegato troppo tempo per rispondere.")
        return None

# Funzione per generare il file M3U8
def generate_m3u8(titles, output_file="streaming.m3u8"):
    try:
        m3u8_content = f"#EXTM3U\n# Generated on {datetime.utcnow().isoformat()}\n"
        for title in titles:
            title_name = title.get('name', 'Senza titolo')
            title_id = title.get('id')
            if not title_id:
                logger.warning(f"ID mancante per il titolo: {title_name}")
                continue
            logger.debug(f"Elaborazione titolo: {title_name} (ID: {title_id})")
            video_url = get_video_url(title_id)
            if video_url:
                m3u8_content += f"#EXTINF:-1,{title_name}\n{video_url}\n"
            else:
                m3u8_content += f"#EXTINF:-1,{title_name}\n# Nessun flusso video disponibile\n"
            time.sleep(2)  # Ritardo per evitare blocchi
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(m3u8_content)
        logger.info(f"File M3U8 '{output_file}' generato con successo.")
    except Exception as e:
        logger.error(f"Errore durante la generazione del file M3U8: {e}")

# Funzione principale
def main():
    categories = [
        {"name": "Top 10 di oggi", "slug": "top10"},
        {"name": "I Titoli Del Momento", "slug": "trending"},
    ]
    for category in categories:
        logger.info(f"Elaborazione categoria: {category['name']}")
        titles = get_titles_from_category(category['slug'])
        if titles:
            output_filename = f"{category['slug']}.m3u8"
            generate_m3u8(titles, output_file=output_filename)
        else:
            logger.warning(f"Nessun titolo trovato per la categoria: {category['name']}")

if __name__ == "__main__":
    main()