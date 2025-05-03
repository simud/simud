import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Intestazioni HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
}

BASE_URL = "https://streamingcommunity.spa"

def get_page_html(url):
    """
    Ottiene l'HTML della pagina utilizzando Requests.
    """
    try:
        logger.debug(f"GetUrl - Richiesta URL con Requests: {url}")
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        logger.debug("GetUrl - HTML della pagina ottenuto con Requests")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"GetUrl - Errore durante la richiesta {url}: {e}")
        return None

def extract_categories(html):
    """
    Estrae le categorie principali dalla homepage.
    """
    logger.info("Parsing delle categorie dall'HTML")
    soup = BeautifulSoup(html, 'html.parser')
    categories = {}

    # Modifica i selettori per corrispondere alla struttura del sito
    for a in soup.find_all('a', href=True):
        name = a.text.strip().lower()
        href = a['href']
        if "film" in name or "serie tv" in name:  # Filtra solo le categorie rilevanti
            categories[name] = urljoin(BASE_URL, href)
            logger.debug(f"Trovata categoria: {name} ({categories[name]})")
    
    if not categories:
        logger.warning("Nessuna categoria rilevante trovata.")
    return categories

def extract_streams(category_url):
    """
    Estrae i flussi video da una categoria specifica.
    """
    logger.info(f"Estrazione flussi per la categoria: {category_url}")
    html = get_page_html(category_url)
    if not html:
        logger.error(f"Impossibile ottenere l'HTML per la categoria: {category_url}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    streams = []

    # Modifica questo selettore in base alla struttura del sito
    for a in soup.find_all('a', href=True, class_="stream-link"):  # Es. "stream-link" è da sostituire con il selettore reale
        title = a.text.strip()
        href = a['href']
        if href and title:
            streams.append((title, urljoin(BASE_URL, href)))
            logger.debug(f"Trovato flusso: {title} ({streams[-1][1]})")
    
    if not streams:
        logger.warning(f"Nessun flusso trovato per la categoria: {category_url}")
    return streams

def extract_episodes(stream_url):
    """
    Estrae gli episodi da una pagina specifica.
    """
    logger.info(f"Estrazione episodi per il flusso: {stream_url}")
    html = get_page_html(stream_url)
    if not html:
        logger.error(f"Impossibile ottenere l'HTML per il flusso: {stream_url}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    episodes = []

    # Modifica questo selettore in base alla struttura del sito
    for a in soup.find_all('a', href=True, class_="episode-link"):  # Es. "episode-link" è da sostituire
        title = a.text.strip()
        href = a['href']
        if href and title:
            episodes.append((title, urljoin(BASE_URL, href)))
            logger.debug(f"Trovato episodio: {title} ({episodes[-1][1]})")
    
    if not episodes:
        logger.warning(f"Nessun episodio trovato per il flusso: {stream_url}")
    return episodes

def main():
    """
    Esegue il processo completo: categorie -> flussi -> episodi.
    """
    homepage_html = get_page_html(BASE_URL)
    if not homepage_html:
        logger.error("Impossibile ottenere l'HTML della homepage")
        return

    categories = extract_categories(homepage_html)
    if not categories:
        logger.error("Nessuna categoria rilevante trovata")
        return

    for category_name, category_url in categories.items():
        logger.info(f"Processo della categoria: {category_name}")
        streams = extract_streams(category_url)
        if streams:
            for stream_title, stream_url in streams:
                logger.info(f"Processo del flusso: {stream_title}")
                episodes = extract_episodes(stream_url)
                if episodes:
                    logger.info(f"Episodi trovati per {stream_title}: {episodes}")
                else:
                    logger.info(f"Nessun episodio trovato per {stream_title}")
        else:
            logger.info(f"Nessun flusso trovato per {category_name}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise