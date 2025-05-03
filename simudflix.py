import logging
import requests
from bs4 import BeautifulSoup

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# URL principale
main_url = "https://streamingcommunity.spa"
categories = {
    f"{main_url}/browse/top10": "Top 10 di oggi",
    f"{main_url}/browse/trending": "I Titoli Del Momento",
    f"{main_url}/browse/latest": "Aggiunti di Recente",
    f"{main_url}/browse/genre?g=Animazione": "Animazione",
    f"{main_url}/browse/genre?g=Avventura": "Avventura",
    f"{main_url}/browse/genre?g=Azione": "Azione",
    f"{main_url}/browse/genre?g=Commedia": "Commedia",
    f"{main_url}/browse/genre?g=Crime": "Crime",
    f"{main_url}/browse/genre?g=Documentario": "Documentario",
    f"{main_url}/browse/genre?g=Dramma": "Dramma",
    f"{main_url}/browse/genre?g=Famiglia": "Famiglia",
    f"{main_url}/browse/genre?g=Fantascienza": "Fantascienza",
    f"{main_url}/browse/genre?g=Fantasy": "Fantasy",
    f"{main_url}/browse/genre?g=Horror": "Horror",
    f"{main_url}/browse/genre?g=Reality": "Reality",
    f"{main_url}/browse/genre?g=Romance": "Romance",
    f"{main_url}/browse/genre?g=Thriller": "Thriller",
}

def fetch_html(url):
    try:
        logger.debug(f"GetUrl - Richiesta URL con Requests: {url}")
        response = requests.get(url)
        response.raise_for_status()
        logger.debug(f"GetUrl - HTML della pagina ottenuto con Requests")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Errore durante la richiesta: {e}")
        return None

def parse_flows(html):
    soup = BeautifulSoup(html, 'html.parser')
    flows = []
    for tag in soup.find_all('a', href=True):
        link = tag['href']
        if "m3u8" in link:
            flows.append(link)
            logger.debug(f"Trovato flusso: {link}")
    return flows

def process_categories():
    for url, name in categories.items():
        logger.info(f"Processo della categoria: {name}")
        html = fetch_html(url)
        if not html:
            logger.error(f"Impossibile ottenere l'HTML per la categoria: {url}")
            continue
        flows = parse_flows(html)
        if not flows:
            logger.info(f"Nessun flusso trovato per {name}")
        else:
            logger.info(f"Flussi trovati per {name}: {flows}")

if __name__ == "__main__":
    process_categories()