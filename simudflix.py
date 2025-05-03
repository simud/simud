import logging
import requests
from bs4 import BeautifulSoup
import os
import http.cookiejar
from urllib.parse import urljoin

# Configurazione del logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Intestazioni ispirate al plugin Kotlin
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://streamingcommunity.spa/',
    'Connection': 'keep-alive',
}

# URL di base
BASE_URL = "https://streamingcommunity.spa"

# File dei cookie
COOKIE_FILE = "cookies.txt"
session = requests.Session()

def generate_default_cookies():
    """
    Genera e salva i cookie predefiniti necessari per accedere al sito.
    """
    logger.info("GenerateDefaultCookies - Creazione dei cookie predefiniti")
    default_cookies = [
        {
            "domain": "streamingcommunity.spa",
            "name": "session_id",
            "value": "dummy_session_value",
            "path": "/",
            "secure": True,
            "httpOnly": True,
        },
    ]

    # Scrive i cookie nel file cookies.txt
    cookie_jar = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
    for cookie in default_cookies:
        cookie_jar.set_cookie(http.cookiejar.Cookie(
            version=0,
            name=cookie["name"],
            value=cookie["value"],
            port=None,
            port_specified=False,
            domain=cookie["domain"],
            domain_specified=True,
            domain_initial_dot=False,
            path=cookie["path"],
            path_specified=True,
            secure=cookie["secure"],
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': cookie["httpOnly"]},
            rfc2109=False,
        ))
    cookie_jar.save()
    logger.info("GenerateDefaultCookies - Cookie predefiniti salvati con successo")

# Gestione dei cookie
if not os.path.exists(COOKIE_FILE):
    logger.warning("File cookies.txt non trovato, generazione automatica dei cookie")
    generate_default_cookies()
else:
    try:
        cookie_jar = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
        cookie_jar.load()
        session.cookies = cookie_jar
        logger.debug("Cookies caricati da cookies.txt")
    except Exception as e:
        logger.error(f"Errore nel caricamento di cookies.txt: {e}")
        generate_default_cookies()

def get_page_html(url):
    """
    Ottiene l'HTML della pagina utilizzando la libreria requests.
    """
    try:
        logger.debug(f"GetUrl - Richiesta URL con Requests: {url}")
        response = session.get(url, headers=HEADERS)
        response.raise_for_status()
        logger.debug("GetUrl - HTML della pagina ottenuto con Requests")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"GetUrl - Errore durante la richiesta {url}: {e}")
        return None

def get_all_categories():
    """
    Recupera tutte le categorie dal sito usando BeautifulSoup per fare il parsing HTML.
    """
    logger.info("Recupero delle categorie dal sito")
    url = BASE_URL
    html = get_page_html(url)
    if not html:
        logger.error("Impossibile ottenere l'HTML della homepage")
        return

    soup = BeautifulSoup(html, 'html.parser')

    # Trova i link delle categorie (adatta il selettore)
    categories = soup.find_all('a', class_='category-link')  # Selettore ipotetico
    for category in categories:
        category_name = category.text.strip()
        category_url = category.get('href')
        if not category_url.startswith('http'):
            category_url = urljoin(BASE_URL, category_url)
        logger.info(f"Elaborazione categoria: {category_name} ({category_url})")
        try_api(category_url)

def try_api(category_url):
    """
    Funzione da implementare per gestire l'API per ogni categoria.
    """
    pass  # Implementazione da aggiungere

if __name__ == "__main__":
    try:
        get_all_categories()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise