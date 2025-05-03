import requests
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

# Configurazione di Selenium
def setup_selenium():
    """
    Configura il driver di Selenium per Chrome in modalità headless.
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Esegui in modalità headless
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# Funzioni per estrarre video e generare M3U8
def get_page_html(url):
    """
    Ottiene l'HTML della pagina usando Selenium per gestire contenuti dinamici.
    """
    driver = None
    try:
        logger.debug(f"GetUrl - Richiesta URL con Selenium: {url}")
        driver = setup_selenium()
        
        # Carica i cookie salvati in cookies.txt
        driver.get(BASE_URL)  # Prima vai alla homepage per impostare il dominio
        if os.path.exists(COOKIE_FILE):
            cookie_jar = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
            cookie_jar.load()
            for cookie in cookie_jar:
                driver.add_cookie({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'secure': cookie.secure,
                    'expiry': cookie.expires
                })
        
        # Carica la pagina desiderata
        driver.get(url)
        
        # Aspetta che la pagina sia completamente caricata (es. un elemento specifico)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Ottieni l'HTML
        html = driver.page_source
        logger.debug("GetUrl - HTML della pagina ottenuto con Selenium")
        return html
    except Exception as e:
        logger.error(f"GetUrl - Errore durante la richiesta {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def try_api(category_url):
    pass  # Implementazione da aggiungere

def get_video_url_yt_dlp(player_url):
    pass  # Implementazione da aggiungere

def get_video_url(title_id, is_series=False, season=1, episode=1):
    pass  # Implementazione da aggiungere

def generate_m3u8(titles, output_file="streaming.m3u8"):
    pass  # Implementazione da aggiungere

def get_all_categories():
    """
    Recupera tutte le categorie dal sito usando Selenium.
    """
    logger.info("Recupero delle categorie dal sito")
    url = BASE_URL
    html = get_page_html(url)
    if not html:
        logger.error("Impossibile ottenere l'HTML della homepage")
        return
    
    driver = setup_selenium()
    try:
        driver.get(url)
        # Aspetta che le categorie siano visibili (adatta il selettore)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.category-link'))  # Selettore ipotetico
        )
        
        # Trova i link delle categorie
        categories = driver.find_elements(By.CSS_SELECTOR, 'a.category-link')  # Adatta il selettore
        for category in categories:
            category_name = category.text.strip()
            category_url = category.get_attribute('href')
            if not category_url.startswith('http'):
                category_url = urljoin(BASE_URL, category_url)
            logger.info(f"Elaborazione categoria: {category_name} ({category_url})")
            try_api(category_url)
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione delle categorie: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    try:
        get_all_categories()
    except Exception as e:
        logger.error(f"Errore principale: {e}")
        raise