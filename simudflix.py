import requests
import logging
from bs4 import BeautifulSoup
import json
import time
import re
import subprocess
from urllib.parse import urljoin
from datetime import datetime
import http.cookiejar
import os

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Intestazioni per emulare un browser reale
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://streamingcommunity.spa/',
    'Connection': 'keep-alive',
}

# URL di base
BASE_URL = "https://streamingcommunity.spa"

# Carica cookie da file (se esiste)
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
    logger.warning("File cookies.txt non trovato, procedo senza cookie")

# Funzione per ottenere i dati dalla pagina HTML
def get_page_html(url):
    try:
        logger.debug(f"GetUrl - Richiesta URL: {url}")
        response = session.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        logger.debug("GetUrl - HTML della pagina ottenuto")
        return response.text
    except requests.RequestException as e:
        logger.error(f"GetUrl - Errore durante la richiesta {url}: {e}")
        return None

# Funzione per ottenere i dati tramite API
def try_api(category_url):
    api_urls = [
        f"{BASE_URL}/api/browse/{category_url.split('/')[-1]}",
        f"{BASE_URL}/api/titles?category={category_url.split('/')[-1]}",
        f"{BASE_URL}/api/{category_url.split('/')[-1]}",
    ]

    for api_url in api_urls:
        try:
            logger.debug(f"TryApi - Tentativo di accesso all'API: {api_url}")
            response = session.get(api_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"TryApi - Dati API ottenuti: {json.dumps(data, indent=2)}")
            return data.get('titles', [])
        except requests.RequestException as e:
            logger.error(f"TryApi - Errore API per {api_url}: {e}")
    
    logger.error(f"TryApi - Nessuna API valida trovata per: {category_url}")
    return []

# Funzione per estrarre il flusso video con yt-dlp
def get_video_url_yt_dlp(player_url):
    try:
        logger.debug(f"GetVideoUrlYtDlp - Esecuzione yt-dlp per: {player_url}")
        cmd = [
            'yt-dlp', '--get-url', '--user-agent', HEADERS['User-Agent'],
            '--referer', BASE_URL, '--cookies', COOKIE_FILE, player_url
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        video_url = result.stdout.strip()
        if video_url and ('.m3u8' in video_url or '.mp4' in video_url):
            logger.debug(f"GetVideoUrlYtDlp - Link video trovato: {video_url}")
            return video_url
        else:
            logger.debug(f"GetVideoUrlYtDlp - Nessun link valido trovato: {video_url}")
    except subprocess.CalledProcessError as e:
        logger.error(f"GetVideoUrlYtDlp - Errore con yt-dlp: {e}\nCommand: {cmd}\nOutput: {e.output}\nErrore: {e.stderr}")
    except FileNotFoundError as e:
        logger.error(f"GetVideoUrlYtDlp - yt-dlp non trovato: {e}")
    except subprocess.TimeoutExpired as e:
        logger.error(f"GetVideoUrlYtDlp - Timeout yt-dlp: {e}")
    return None

# Funzione per estrarre il link video dalla pagina del player
def get_video_url(title_id, is_series=False, season=1, episode=1):
    # URL del player
    player_url = f"{BASE_URL}/watch/{title_id}"
    if is_series:
        player_url += f"?season={season}&episode={episode}"
    
    logger.debug(f"GetVideoUrl - Tentativo di estrazione per: {player_url}")
    
    # Ottieni l'HTML della pagina del player
    html = get_page_html(player_url)
    if not html:
        logger.error(f"GetVideoUrl - Impossibile ottenere HTML per: {player_url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')
    
    # Cerca iframe
    logger.debug("GetVideoUrl - Ricerca iframe")
    iframe = soup.find('iframe')
    if iframe and iframe.get('src') and 'vixcloud.co' in iframe.get('src'):
        logger.debug(f"GetVideoUrl - Iframe trovato: {iframe['src']}")
        return iframe['src']
    
    # Cerca elementi <video>
    logger.debug("GetVideoUrl - Ricerca elemento video")
    video = soup.find('video')
    if video:
        src = video.get('src') or (video.find('source') and video.find('source').get('src'))
        if src and 'vixcloud.co' in src:
            logger.debug(f"GetVideoUrl - Video trovato: {src}")
            return src
    
    # Cerca link .m3u8 di vixcloud.co negli script
    logger.debug("GetVideoUrl - Ricerca link .m3u8 negli script")
    for script in soup.find_all('script'):
        script_text = script.string
        if script_text:
            video_urls = re.findall(r'(https?://vixcloud\.co/playlist/\d+\?[^\'"]+)', script_text)
            if video_urls:
                video_url = video_urls[0]
                logger.debug(f"GetVideoUrl - Link video trovato nello script: {video_url}")
                return video_url
            
            config_match = re.search(r'playerConfig\s*=\s*({.*?});', script_text, re.DOTALL)
            if config_match:
                try:
                    config = json.loads(config_match.group(1))
                    video_url = config.get('url') or config.get('stream_url') or config.get('hls_src')
                    if video_url and 'vixcloud.co' in video_url:
                        logger.debug(f"GetVideoUrl - Link video trovato in playerConfig: {video_url}")
                        return video_url
                except json.JSONDecodeError as e:
                    logger.debug(f"GetVideoUrl - Errore nel parsing di playerConfig: {e}")
            
            hls_match = re.search(r'hls_src\s*=\s*[\'"](https?://vixcloud\.co/playlist/\d+\?[^\'"]*)[\'"]', script_text)
            if hls_match:
                logger.debug(f"GetVideoUrl - Link hls_src trovato: {hls_match.group(1)}")
                return hls_match.group(1)
    
    # Tenta con API di streaming
    api_urls = [
        f"{BASE_URL}/api/stream/{title_id}",
        f"{BASE_URL}/api/watch/{title_id}",
        f"{BASE_URL}/api/video/{title_id}",
    ]
    if is_series:
        api_urls = [url + f"?season={season}&episode={episode}" for url in api_urls]
    
    for api_url in api_urls:
        try:
            logger.debug(f"GetVideoUrl - Tentativo di accesso all'API: {api_url}")
            response = session.get(api_url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            data = response.json()
            video_url = data.get('url') or data.get('stream_url') or data.get('hls_url') or data.get('hls_src')
            if video_url and 'vixcloud.co' in video_url:
                logger.debug(f"GetVideoUrl - Link video trovato tramite API: {video_url}")
                return video_url
        except (requests.RequestException, ValueError) as e:
            logger.debug(f"GetVideoUrl - Nessun flusso video trovato tramite API: {api_url} ({e})")

    # Prova con yt-dlp
    logger.debug("GetVideoUrl - Tentativo con yt-dlp")
    video_url = get_video_url_yt_dlp(player_url)
    if video_url:
        return video_url

    logger.error(f"GetVideoUrl - Nessun flusso video trovato per: {player_url}")
    return None

# Funzione per generare il file M3U8
def generate_m3u8(titles, output_file="streaming.m3u8"):
    try:
        m3u8_content = f"#EXTM3U\n# Generated on {datetime.utcnow().isoformat()}\n"
        for title in titles:
            try:
                logger.debug(f"GenerateM3U8 - Elaborazione titolo: {title['name']} (ID: {title['id']})")
                # Determina se è una serie TV
                is_series = title.get('type') == 'tv' or title.get('seasons_count', 0) > 0
                video_url = get_video_url(title['id'], is_series=is_series, season=1, episode=1)
                if video_url:
                    m3u8_content += f"#EXTINF:-1,{title['name']}\n{video_url}\n"
                else:
                    m3u8_content += f"#EXTINF:-1,{title['name']}\n# Nessun flusso video disponibile\n"
                time.sleep(1)  # Ritardo per evitare blocchi
            except Exception as e:
                logger.error(f"GenerateM3U8 - Errore durante l'elaborazione del titolo {title['name']}: {e}")
                m3u8_content += f"#EXTINF:-1,{title['name']}\n# Errore: {str(e)}\n"
        
        # Scrivi il file M3U8
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(m3u8_content)
        logger.info(f"GenerateM3U8 - File {output_file} generato con successo")
    except Exception as e:
        logger.error(f"GenerateM3U8 - Errore durante la generazione del file M3U8: {e}")
        raise

# Funzione principale per processare tutte le categorie
def get_all_categories():
    try:
        categories = [
            {"name": "Top 10 di oggi", "url": f"{BASE_URL}/browse/top10"},
            {"name": "I Titoli Del Momento", "url": f"{BASE_URL}/browse/trending"},
        ]

        for category in categories:
            logger.info(f"GetAllCategories - Processing category: {category['name']} ({category['url']})")
            
            # Ottieni i titoli dall'API
            titles = try_api(category['url'])
            if not titles:
                logger.error(f"GetAllCategories - Nessun titolo trovato per: {category['name']}")
                continue
            
            # Genera il file M3U8
            generate_m3u8(titles)
            
            # Log dei titoli trovati
            for title in titles:
                logger.info(f"Titolo: {title['name']} - Player URL: {BASE_URL}/watch/{title['id']}")
    except Exception as e:
        logger.error(f"GetAllCategories - Errore durante l'elaborazione delle categorie: {e}")
        raise

# Esecuzione principale
if __name__ == "__main__":
    try:
        get_all_categories()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise