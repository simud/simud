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

def save_html_to_file(html, filename="page_debug.html"):
    """
    Salva l'HTML in un file per analisi manuale.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(html)
        logger.info(f"HTML salvato nel file: {filename}")
    except Exception as e:
        logger.error(f"Errore durante il salvataggio dell'HTML: {e}")

def extract_categories(html):
    """
    Estrae le categorie dalla homepage.
    """
    logger.info("Parsing delle categorie dall'HTML")
    soup = BeautifulSoup(html, 'html.parser')
    categories = []
    
    # Modifica questo selettore in base alla struttura HTML
    for a in soup.find_all('a', href=True):  # Modificato per trovare tutti i link
        href = a['href']
        name = a.text.strip()
        if href and name:
            url = urljoin(BASE_URL, href)
            categories.append((name, url))
            logger.debug(f"Trovata categoria: {name} ({url})")
    
    if not categories:
        logger.warning("Nessuna categoria trovata - verifica il selettore HTML.")
    return categories

def extract_stream_links(category_url):
    """
    Estrae i link dei flussi video da una categoria.
    """
    logger.info(f"Estrazione flussi per la categoria: {category_url}")
    html = get_page_html(category_url)
    if not html:
        logger.error(f"Impossibile ottenere l'HTML per la categoria: {category_url}")
        return []

    save_html_to_file(html, filename="category_debug.html")  # Salva HTML della categoria per debug

    soup = BeautifulSoup(html, 'html.parser')
    streams = []

    # Modifica questo selettore in base alla struttura del sito
    for a in soup.find_all('a', href=True):  # Generico per iniziare
        href = a['href']
        title = a.text.strip()
        if href and title:
            url = urljoin(BASE_URL, href)
            streams.append((title, url))
            logger.debug(f"Trovato flusso: {title} ({url})")
    
    if not streams:
        logger.warning(f"Nessun flusso trovato per la categoria: {category_url}")
    return streams

def get_all_categories_and_streams():
    """
    Recupera tutte le categorie e i rispettivi flussi.
    """
    homepage_html = get_page_html(BASE_URL)
    if not homepage_html:
        logger.error("Impossibile ottenere l'HTML della homepage")
        return

    save_html_to_file(homepage_html, filename="homepage_debug.html")  # Salva HTML della homepage per debug

    categories = extract_categories(homepage_html)
    if not categories:
        logger.error("Nessuna categoria trovata - il parsing è fallito.")
        return

    for name, url in categories:
        logger.info(f"Processo della categoria: {name}")
        streams = extract_stream_links(url)
        if streams:
            logger.info(f"Flussi trovati per {name}: {streams}")
        else:
            logger.info(f"Nessun flusso trovato per {name}")

if __name__ == "__main__":
    try:
        get_all_categories_and_streams()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise