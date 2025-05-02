import requests
import logging
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin

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
        logger.error(f"GetUrl - Errore durante la richiesta: {e}")
        return None

# Funzione per ottenere i link dei titoli dalla categoria tramite HTML
def get_urls_from_category(category_url):
    html = get_page_html(category_url)
    if not html:
        logger.error(f"GetUrlsFromCategory - Impossibile ottenere HTML per: {category_url}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    # Cerca elementi che contengono i titoli (modifica il selettore in base alla struttura del sito)
    title_elements = soup.select('a[href*="/titles/"]')  # Selettore generico, da adattare
    for element in title_elements:
        href = element.get('href')
        if href:
            full_url = urljoin(BASE_URL, href)
            links.append(full_url)
    
    logger.debug(f"GetUrlsFromCategory - Link trovati: {links}")
    if not links:
        logger.error(f"GetUrlsFromCategory - Nessun titolo trovato nella categoria: {category_url}")
    return links

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
            logger.debug(f"TryApi - Dati API ottenuti: {data}")
            return data.get('titles', [])
        except requests.RequestException as e:
            logger.error(f"TryApi - Errore API per {api_url}: {e}")
    
    logger.error(f"TryApi - Nessuna API valida trovata per: {category_url}")
    return []

# Funzione per estrarre l'iframe o il link video dalla pagina del titolo
def get_video_url(title_url):
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
    
    # Cerca elementi <video> come alternativa
    video = soup.find('video')
    if video and video.get('src'):
        logger.debug(f"GetVideoUrl - Video trovato: {video['src']}")
        return video['src']
    
    # Cerca link a risorse video (es. mp4, m3u8) nelle richieste di rete
    for script in soup.find_all('script'):
        script_text = script.string
        if script_text and ('mp4' in script_text or 'm3u8' in script_text):
            # Estrai URL video (logica semplificata, da affinare)
            logger.debug(f"GetVideoUrl - Possibile link video trovato nello script: {script_text[:100]}")
            # Qui dovresti parsare il contenuto dello script per estrarre l'URL effettivo
            return None  # Sostituisci con logica di parsing reale

    logger.error(f"GetVideoUrl - Nessun iframe o video trovato nella pagina: {title_url}")
    return None

# Funzione principale per processare tutte le categorie
def get_all_categories():
    categories = [
        {"name": "Top 10 di oggi", "url": f"{BASE_URL}/browse/top10"},
        {"name": "I Titoli Del Momento", "url": f"{BASE_URL}/browse/trending"},
    ]

    for category in categories:
        logger.info(f"GetAllCategories - Processing category: {category['name']} ({category['url']})")
        
        # Prova prima con l'API
        titles = try_api(category['url'])
        if not titles:
            logger.info("GetAllCategories - API non disponibile, tentativo con scraping HTML")
            title_urls = get_urls_from_category(category['url'])
        else:
            title_urls = [f"{BASE_URL}/titles/{title['id']}-{title['slug']}" for title in titles]
        
        # Processa ogni titolo
        for title_url in title_urls:
            logger.debug(f"TryApi - Processing title URL: {title_url}")
            video_url = get_video_url(title_url)
            if video_url:
                logger.info(f"Titolo: {title_url} - Video URL: {video_url}")
            else:
                logger.error(f"Nessun video trovato per: {title_url}")
            
            # Rispetta i limiti di rate limiting
            time.sleep(1)

# Esecuzione principale
if __name__ == "__main__":
    try:
        get_all_categories()
    except Exception as e:
        logger.error(f"Errore principale: {e}")