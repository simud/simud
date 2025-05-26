import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurazione del browser Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # modalità headless
chrome_options.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
driver = webdriver.Chrome(options=chrome_options)

# Inizializzazione di Cloudscraper
scraper = cloudscraper.create_scraper()

# URL base
base_url = "https://altadefinizionegratis.icu/cinema/"
m3u8_content = "#EXTM3U\n"

# Funzione per ottenere link film/serie da una pagina, con Cloudscraper + Selenium
def get_movie_links_from_page(page_url):
    try:
        movie_links = set()

        # Cloudscraper (HTML statico)
        logging.info(f"Caricamento pagina (Cloudscraper): {page_url}")
        response = scraper.get(page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        dle_content = soup.find('div', id='dle-content')
        if dle_content:
            for link in dle_content.find_all('a', href=True):
                href = link['href']
                if re.search(r'/\d+-', href) and any(
                    ending in href for ending in [
                        '-streaming-gratis.html',
                        '-streaming-ita.html',
                        '-gratis.html',
                        '-hd.html',
                        '-streaming-community-hd.html',
                        '-streaming.html',
                        '-ita.html'
                    ]
                ):
                    if not href.startswith('http'):
                        href = 'https://altadefinizionegratis.icu' + href
                    movie_links.add(href)
                    logging.info(f"Trovato link (Cloudscraper): {href}")

        # Selenium (contenuti dinamici)
        logging.info(f"Caricamento pagina (Selenium): {page_url}")
        driver.get(page_url)
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "dle-content")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        dle_content = soup.find('div', id='dle-content')
        if dle_content:
            for link in dle_content.find_all('a', href=True):
                href = link['href']
                if re.search(r'/\d+-', href) and any(
                    ending in href for ending in [
                        '-streaming-gratis.html',
                        '-streaming-ita.html',
                        '-gratis.html',
                        '-hd.html',
                        '-streaming-community-hd.html',
                        '-streaming.html',
                        '-ita.html'
                    ]
                ):
                    if not href.startswith('http'):
                        href = 'https://altadefinizionegratis.icu' + href
                    movie_links.add(href)
                    logging.info(f"Trovato link (Selenium): {href}")

        logging.info(f"Trovati {len(movie_links)} link film/serie in {page_url}")
        return movie_links
    except Exception as e:
        logging.error(f"Errore recupero link pagina {page_url}: {e}")
        return set()

# Ottieni tutti i link film/serie da più pagine
def get_movie_links():
    movie_links = set()
    movie_links.update(get_movie_links_from_page(base_url))
    for page_num in range(2, 11):
        page_url = f"{base_url}page/{page_num}/"
        movie_links.update(get_movie_links_from_page(page_url))
    logging.info(f"Trovati in totale {len(movie_links)} film/serie")
    return list(movie_links)

# Estrai iframe da pagina film con Selenium
def get_providers(movie_url):
    try:
        logging.info(f"Caricamento pagina film: {movie_url}")
        driver.get(movie_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        iframe = soup.find('iframe', src=True)
        if iframe:
            iframe_url = iframe['src']
            if not iframe_url.startswith('http'):
                iframe_url = 'https:' + iframe_url
            logging.info(f"Trovato iframe: {iframe_url}")
            return get_provider_links(iframe_url)
        logging.warning(f"Nessun iframe trovato in {movie_url}")
        return []
    except Exception as e:
        logging.error(f"Errore recupero iframe {movie_url}: {e}")
        return []

# Estrai link provider da pagina iframe con Selenium
def get_provider_links(iframe_url):
    try:
        logging.info(f"Caricamento pagina iframe: {iframe_url}")
        driver.get(iframe_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "_player-mirrors")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        providers = []
        valid_providers = ['supervideo', 'dropload', 'mixdrop', 'doodstream']
        for li in soup.find_all('li', {'data-link': True}):
            provider_url = li['data-link']
            if not provider_url.startswith('http'):
                provider_url = 'https:' + provider_url
            provider_name = li.text.strip().lower()
            if provider_name in valid_providers:
                providers.append((provider_name, provider_url))
                logging.info(f"Trovato provider: {provider_name} - {provider_url}")
        logging.info(f"Trovati {len(providers)} provider validi in {iframe_url}")
        return providers
    except Exception as e:
        logging.error(f"Errore recupero provider {iframe_url}: {e}")
        return []

# Ottieni link diretto .m3u8 se presente o fallback a embed
def get_stream_url(provider_name, provider_url):
    try:
        logging.info(f"Recupero flusso per {provider_name}: {provider_url}")
        response = scraper.get(provider_url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
            'Referer': provider_url,
            'Origin': provider_url
        })
        soup = BeautifulSoup(response.text, 'html.parser')
        video_source = soup.find('source', src=re.compile(r'\.m3u8$'))
        if video_source:
            logging.info(f"Trovato flusso diretto: {video_source['src']}")
            return video_source['src']
        logging.info(f"Nessun flusso diretto trovato, uso embed: {provider_url}")
        return provider_url
    except Exception as e:
        logging.error(f"Errore recupero flusso {provider_url}: {e}")
        return provider_url

# Genera voce M3U8 per VLC
def generate_m3u8_entry(title, provider_name, stream_url):
    provider_domain = provider_name
    return f"""#EXTINF:-1 group-title="{provider_name}" tvg-name="{title}",{title}
#EXTVLCOPT:http-user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1
#EXTVLCOPT:http-referrer=https://{provider_domain}
#EXTVLCOPT:http-origin=https://{provider_domain}
{stream_url}\n"""

# Funzione principale
def main():
    global m3u8_content
    movie_links = get_movie_links()
    logging.info(f"Elaborazione di {len(movie_links)} film/serie")

    for movie_url in movie_links:
        try:
            # Pulizia titolo dal link
            title = movie_url.split('/')[-1]
            for ending in [
                '-streaming-gratis.html',
                '-streaming-ita.html',
                '-gratis.html',
                '-hd.html',
                '-streaming-community-hd.html',
                '-streaming.html',
                '-ita.html'
            ]:
                title = title.replace(ending, '')
            title = re.sub(r'^\d+-', '', title)
            title = title.replace('-', ' ').title()
            logging.info(f"Titolo pulito: {title}")

            providers = get_providers(movie_url)
            for provider_name, provider_url in providers:
                stream_url = get_stream_url(provider_name, provider_url)
                m3u8_content += generate_m3u8_entry(title, provider_name, stream_url)

            time.sleep(1)  # evita sovraccarico
        except Exception as e:
            logging.error(f"Errore elaborazione {movie_url}: {e}")

    with open('films.m3u8', 'w', encoding='utf-8') as f:
        f.write(m3u8_content)
    logging.info("File M3U8 generato con successo: films.m3u8")

# Esecuzione
if __name__ == "__main__":
    try:
        main()
    finally:
        driver.quit()
