import requests
import logging
from bs4 import BeautifulSoup
import json
import time
import re
import subprocess
from urllib.parse import urljoin
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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

# Funzione per ottenere i dati dalla pagina HTML
def get_page_html(url):
    try:
        logger.debug(f"GetUrl - Richiesta URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
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
            response = requests.get(api_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"TryApi - Dati API ottenuti: {json.dumps(data, indent=2)}")
            return data.get('titles', [])
        except requests.RequestException as e:
            logger.error(f"TryApi - Errore API per {api_url}: {e}")
    
    logger.error(f"TryApi - Nessuna API valida trovata per: {category_url}")
    return []

# Funzione per estrarre il token di autenticazione
def get_auth_token(title_url):
    html = get_page_html(title_url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script'):
        script_text = script.string
        if script_text:
            token_match = re.search(r'(?:token|wmsAuthSign|hdnts)[\'"]?\s*[:=]\s*[\'"]([^\'"]+)[\'"]', script_text)
            if token_match:
                logger.debug(f"GetAuthToken - Token trovato: {token_match.group(1)}")
                return token_match.group(1)
    
    logger.debug("GetAuthToken - Nessun token trovato")
    return None

# Funzione per estrarre il flusso video con yt-dlp
def get_video_url_yt_dlp(title_url):
    try:
        result = subprocess.run(
            ['yt-dlp', '--get-url', '--user-agent', HEADERS['User-Agent'], '--referer', BASE_URL, title_url],
            capture_output=True, text=True, check=True
        )
        video_url = result.stdout.strip()
        if video_url and ('.m3u8' in video_url or '.mp4' in video_url):
            logger.debug(f"GetVideoUrl - Link video trovato con yt-dlp: {video_url}")
            return video_url
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"GetVideoUrl - Errore con yt-dlp: {e}")
    return None

# Funzione per estrarre il flusso video con Selenium
def get_video_url_selenium(title_url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    try:
        logger.debug(f"GetVideoUrl - Avvio Selenium per: {title_url}")
        driver.get(title_url)
        time.sleep(5)  # Attendi il caricamento del player
        
        # Cerca il pulsante "Play" e clicca
        try:
            play_button = driver.find_element(By.CSS_SELECTOR, 'button.play, .vjs-play-control, [aria-label="Play"]')
            play_button.click()
            logger.debug("GetVideoUrl - Pulsante Play cliccato")
            time.sleep(3)  # Attendi il caricamento del flusso
        except:
            logger.debug("GetVideoUrl - Pulsante Play non trovato")

        # Cerca iframe
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for iframe in iframes:
            src = iframe.get_attribute('src')
            if src and ('.m3u8' in src or '.mp4' in src):
                logger.debug(f"GetVideoUrl - Iframe trovato con Selenium: {src}")
                return src
        
        # Cerca elementi <video>
        videos = driver.find_elements(By.TAG_NAME, 'video')
        for video in videos:
            src = video.get_attribute('src')
            if src:
                logger.debug(f"GetVideoUrl - Video trovato con Selenium: {src}")
                return src
            sources = video.find_elements(By.TAG_NAME, 'source')
            for source in sources:
                src = source.get_attribute('src')
                if src:
                    logger.debug(f"GetVideoUrl - Source trovato con Selenium: {src}")
                    return src
    
    except Exception as e:
        logger.error(f"GetVideoUrl - Errore con Selenium: {e}")
    finally:
        driver.quit()
    return None

# Funzione per estrarre il link video dalla pagina del titolo
def get_video_url(title_url, title_id):
    # Prima prova con yt-dlp
    video_url = get_video_url_yt_dlp(title_url)
    if video_url:
        return video_url

    # Poi prova con Selenium
    video_url = get_video_url_selenium(title_url)
    if video_url:
        return video_url

    html = get_page_html(title_url)
    if not html:
        logger.error(f"GetVideoUrl - Impossibile ottenere HTML per: {title_url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')
    
    # Cerca iframe
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        logger.debug(f"GetVideoUrl - Iframe trovato: {iframe['src']}")
        return iframe['src']
    
    # Cerca elementi <video>
    video = soup.find('video')
    if video:
        src = video.get('src') or (video.find('source') and video.find('source').get('src'))
        if src:
            logger.debug(f"GetVideoUrl - Video trovato: {src}")
            return src
    
    # Cerca link .m3u8 o .mp4 negli script
    for script in soup.find_all('script'):
        script_text = script.string
        if script_text:
            video_urls = re.findall(r'(https?://[^\s\'"]+\.(m3u8|mp4)(?:\?[^\'"]*)?)', script_text)
            if video_urls:
                video_url = video_urls[0][0]
                logger.debug(f"GetVideoUrl - Link video trovato nello script: {video_url}")
                return video_url
            
            config_match = re.search(r'playerConfig\s*=\s*({.*?});', script_text, re.DOTALL)
            if config_match:
                try:
                    config = json.loads(config_match.group(1))
                    video_url = config.get('url') or config.get('stream_url') or config.get('hls_src')
                    if video_url:
                        logger.debug(f"GetVideoUrl - Link video trovato in playerConfig: {video_url}")
                        return video_url
                except json.JSONDecodeError:
                    logger.debug("GetVideoUrl - Errore nel parsing di playerConfig")
            
            hls_match = re.search(r'hls_src\s*=\s*[\'"](https?://[^\s\'"]+\.m3u8[^\'"]*)[\'"]', script_text)
            if hls_match:
                logger.debug(f"GetVideoUrl - Link hls_src trovato: {hls_match.group(1)}")
                return hls_match.group(1)
    
    # Tenta di ottenere il token di autenticazione
    token = get_auth_token(title_url)
    auth_headers = HEADERS.copy()
    if token:
        auth_headers['Authorization'] = f"Bearer {token}"
    
    # Tenta endpoint API alternativi
    api_endpoints = [
        f"{BASE_URL}/api/stream/{title_id}",
        f"{BASE_URL}/api/playlist/{title_id}",
        f"{BASE_URL}/titles/{title_id}/hls/playlist.m3u8",
        f"{BASE_URL}/api/video/{title_id}",
    ]
    
    for api_url in api_endpoints:
        try:
            logger.debug(f"GetVideoUrl - Tentativo di accesso all'API video: {api_url}")
            response = requests.get(api_url, headers=auth_headers, timeout=10)
            response.raise_for_status()
            if api_url.endswith('.m3u8'):
                logger.debug(f"GetVideoUrl - Link video diretto trovato: {api_url}")
                return api_url
            data = response.json()
            video_url = data.get('url') or data.get('stream_url') or data.get('hls_url')
            if video_url:
                logger.debug(f"GetVideoUrl - Link video trovato tramite API: {video_url}")
                return video_url
        except (requests.RequestException, ValueError) as e:
            logger.debug(f"GetVideoUrl - Nessun flusso video trovato tramite API: {api_url} ({e})")

    logger.error(f"GetVideoUrl - Nessun iframe, video, link, API, yt-dlp o Selenium trovato per: {title_url}")
    return None

# Funzione per generare il file M3U8
def generate_m3u8(titles, output_file="streaming.m3u8"):
    m3u8_content = f"#EXTM3U\n# Generated on {datetime.utcnow().isoformat()}\n"
    for title in titles:
        title_url = f"{BASE_URL}/titles/{title['id']}-{title['slug']}"
        video_url = get_video_url(title_url, title['id'])
        if video_url:
            m3u8_content += f"#EXTINF:-1,{title['name']}\n{video_url}\n"
        else:
            m3u8_content += f"#EXTINF:-1,{title['name']}\n# Nessun flusso video disponibile\n"
        time.sleep(1)  # Ritardo per evitare blocchi
    
    # Scrivi il file M3U8
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(m3u8_content)
    logger.info(f"generate_m3u8 - File {output_file} generato con successo")

# Funzione principale per processare tutte le categorie
def get_all_categories():
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
            logger.info(f"Titolo: {title['name']} - URL: {BASE_URL}/titles/{title['id']}-{title['slug']}")

# Esecuzione principale
if __name__ == "__main__":
    try:
        get_all_categories()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise