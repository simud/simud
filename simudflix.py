# Script Python aggiornato per estrarre flussi M3U8

import os
import logging
import requests
from bs4 import BeautifulSoup

# Configurazione logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "https://streamingcommunity.spa"

def get_page_html(url):
    """
    Scarica l'HTML di una pagina.
    """
    try:
        logger.debug(f"GetUrl - Richiesta URL con Requests: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.debug("GetUrl - HTML della pagina ottenuto con Requests")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Errore durante la richiesta: {e}")
        return None

def extract_categories(html):
    """
    Estrae le categorie dalla homepage.
    """
    soup = BeautifulSoup(html, 'html.parser')
    categories = {}
    for a in soup.find_all('a', href=True):
        if '/watch/' in a['href'] or '/serie-tv' in a['href'] or '/film' in a['href']:
            categories[a.text.strip()] = BASE_URL + a['href']
            logger.debug(f"Trovata categoria: {a.text.strip()} ({BASE_URL + a['href']})")
    if not categories:
        logger.warning("Nessuna categoria trovata - verifica il selettore HTML.")
    return categories

def extract_streams(category_url):
    """
    Estrae i flussi video da una categoria.
    """
    html = get_page_html(category_url)
    if not html:
        logger.error(f"Impossibile ottenere l'HTML per la categoria: {category_url}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    streams = []
    for a in soup.find_all('a', href=True):
        if '/watch/' in a['href']:
            streams.append((a.text.strip(), BASE_URL + a['href']))
            logger.debug(f"Trovato flusso: {a.text.strip()} ({BASE_URL + a['href']})")

    if not streams:
        logger.warning(f"Nessun flusso trovato per la categoria: {category_url}")
    return streams

def extract_m3u8_streams(page_url):
    """
    Estrae i flussi M3U8 da una pagina di film o episodio.
    """
    logger.info(f"Estrazione M3U8 dalla pagina: {page_url}")
    html = get_page_html(page_url)
    if not html:
        logger.error(f"Impossibile ottenere l'HTML per la pagina: {page_url}")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    m3u8_streams = []

    # Metodo 1: Usa BeautifulSoup per cercare link con estensione .m3u8
    for a in soup.find_all('a', href=True):
        if '.m3u8' in a['href']:
            m3u8_streams.append(a['href'])

    # Metodo 2: Cerca direttamente nell'HTML
    for line in html.splitlines():
        if '.m3u8' in line:
            start_idx = line.find('http')
            end_idx = line.find('.m3u8') + 5  # Include ".m3u8"
            m3u8_streams.append(line[start_idx:end_idx])

    if not m3u8_streams:
        logger.warning(f"Nessun flusso M3U8 trovato per la pagina: {page_url}")
    else:
        logger.info(f"Flussi M3U8 trovati: {m3u8_streams}")
    return m3u8_streams

def main():
    """
    Esegue il processo completo: categorie -> flussi -> M3U8.
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
                m3u8_links = extract_m3u8_streams(stream_url)
                if m3u8_links:
                    logger.info(f"Flussi M3U8 trovati per {stream_title}: {m3u8_links}")
                else:
                    logger.info(f"Nessun flusso M3U8 trovato per {stream_title}")
        else:
            logger.info(f"Nessun flusso trovato per {category_name}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise
