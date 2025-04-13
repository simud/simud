import requests
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# URL di partenza
base_url = "https://guardacalcio.art/partite-streaming.html"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
    "Origin": "https://guardacalcio.art",
    "Referer": "https://guardacalcio.art/"
}

# Immagine fissa da usare per tutti i canali
DEFAULT_IMAGE_URL = "https://i.postimg.cc/kXbk78v9/Picsart-25-04-01-23-37-12-396.png"

# Canale ADMIN
ADMIN_CHANNEL = '''#EXTINF:-1 tvg-id="ADMIN" tvg-name="ADMIN" tvg-logo="https://i.postimg.cc/4ysKkc1G/photo-2025-03-28-15-49-45.png" group-title="Eventi", ADMIN
https://static.vecteezy.com/system/resources/previews/033/861/932/mp4/gherkins-close-up-loop-free-video.mp4'''

# Configura Selenium
def setup_selenium():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={headers['User-Agent']}")
    driver = webdriver.Chrome(options=options)
    return driver

# Funzione per ottenere la pagina con Selenium
def get_dynamic_page(url):
    try:
        driver = setup_selenium()
        driver.get(url)
        # Aspetta che eventuali iframe siano caricati
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source
        driver.quit()
        return BeautifulSoup(page_source, 'html.parser')
    except Exception as e:
        print(f"Errore Selenium per {url}: {e}")
        return None

# Funzione per trovare i link alle partite
def find_event_pages():
    try:
        soup = get_dynamic_page(base_url)
        if not soup:
            print("Impossibile caricare la pagina principale con Selenium")
            return []

        event_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.search(r'(streaming|partita|watch|live|diretta)', href, re.IGNORECASE):
                if href.startswith('/'):
                    full_url = "https://guardacalcio.art" + href
                elif href.startswith('https://guardacalcio.art'):
                    full_url = href
                else:
                    continue
                if full_url not in event_links:
                    event_links.add(full_url)
                    print(f"Trovato link: {full_url}")

        return list(event_links)

    except Exception as e:
        print(f"Errore durante la ricerca delle pagine evento: {e}")
        return []

# Funzione per estrarre il flusso effettivo da una pagina iframe
def extract_stream_from_iframe(iframe_url):
    try:
        soup = get_dynamic_page(iframe_url)
        if not soup:
            print(f"Impossibile caricare iframe {iframe_url}")
            return None

        stream_url = None
        # Cerca in <video>, <source>
        for video in soup.find_all('video'):
            src = video.get('src')
            if src and re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE):
                stream_url = src
                print(f"Trovato flusso video in iframe: {src}")
                break
            for source in video.find_all('source'):
                src = source.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE):
                    stream_url = src
                    print(f"Trovato flusso source in iframe: {src}")
                    break

        # Cerca in <iframe> annidati
        if not stream_url:
            for iframe in soup.find_all('iframe'):
                src = iframe.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts)|stream|player', src, re.IGNORECASE):
                    stream_url = src
                    print(f"Trovato flusso iframe annidato: {src}")
                    break

        # Cerca in script
        if not stream_url:
            for script in soup.find_all('script'):
                script_content = script.string
                if script_content and re.search(r'https?://[^\s]*\.(m3u8|mp4|ts)', script_content, re.IGNORECASE):
                    match = re.search(r'(https?://[^\s]*\.(m3u8|mp4|ts))', script_content, re.IGNORECASE)
                    if match:
                        stream_url = match.group(1)
                        print(f"Trovato flusso in script iframe: {stream_url}")
                        break

        # Cerca attributi data-
        if not stream_url:
            for element in soup.find_all(True, {'data-src': True, 'data-url': True}):
                src = element.get('data-src') or element.get('data-url')
                if src and re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE):
                    stream_url = src
                    print(f"Trovato flusso in attributo data: {src}")
                    break

        return stream_url

    except Exception as e:
        print(f"Errore durante l'accesso all'iframe {iframe_url}: {e}")
        return None

# Funzione per estrarre il flusso video e la descrizione
def get_video_stream_and_description(event_url):
    try:
        soup = get_dynamic_page(event_url)
        if not soup:
            print(f"Impossibile caricare {event_url}")
            return None, None, "Unknown Match"

        stream_url = None
        element = None
        # Cerca iframe
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                print(f"Trovato iframe con src: {src}")
                stream_url = extract_stream_from_iframe(src)
                if stream_url:
                    element = iframe
                    break

        # Cerca embed
        if not stream_url:
            for embed in soup.find_all('embed'):
                src = embed.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts|html|php)|stream|player', src, re.IGNORECASE):
                    stream_url = src
                    element = embed
                    print(f"Trovato embed con src: {src}")
                    break

        # Cerca video
        if not stream_url:
            for video in soup.find_all('video'):
                src = video.get('src')
                if src and re.search(r'\.(m3u8|mp4|ts)|stream|player', src, re.IGNORECASE):
                    stream_url = src
                    element = video
                    print(f"Trovato video con src: {src}")
                    break
                for source in video.find_all('source'):
                    src = source.get('src')
                    if src and re.search(r'\.(m3u8|mp4|ts)|stream|player', src, re.IGNORECASE):
                        stream_url = src
                        element = source
                        print(f"Trovato source con src: {src}")
                        break

        # Cerca in script
        if not stream_url:
            for script in soup.find_all('script'):
                script_content = script.string
                if script_content and re.search(r'https?://[^\s]*\.(m3u8|mp4|ts)', script_content, re.IGNORECASE):
                    match = re.search(r'(https?://[^\s]*\.(m3u8|mp4|ts))', script_content, re.IGNORECASE)
                    if match:
                        stream_url = match.group(1)
                        element = script
                        print(f"Trovato flusso in script: {stream_url}")
                        break

        # Cerca attributi data-
        if not stream_url:
            for elem in soup.find_all(True, {'data-src': True, 'data-url': True}):
                src = elem.get('data-src') or elem.get('data-url')
                if src and re.search(r'\.(m3u8|mp4|ts)', src, re.IGNORECASE):
                    stream_url = src
                    element = elem
                    print(f"Trovato flusso in attributo data: {src}")
                    break

        # Estrai il nome del canale
        channel_name = "Unknown Match"
        if element:
            next_element = element.find_previous(['h1', 'h2', 'h3', 'div', 'p'])
            if next_element and next_element.get_text(strip=True):
                channel_name = next_element.get_text(strip=True).split('\n')[0].strip()
                channel_name = re.sub(r'[-_]+', ' ', channel_name)
            else:
                title = soup.find('title')
                if title and title.get_text(strip=True):
                    channel_name = title.get_text(strip=True).split('|')[0].strip()
                    channel_name = re.sub(r'[-_]+', ' ', channel_name)
        else:
            title = soup.find('title')
            if title and title.get_text(strip=True):
                channel_name = title.get_text(strip=True).split('|')[0].strip()
                channel_name = re.sub(r'[-_]+', ' ', channel_name)

        if not stream_url:
            print(f"Nessun flusso trovato per {event_url}")
        else:
            print(f"Flusso valido trovato per {event_url}: {stream_url}")

        return stream_url, element, channel_name

    except Exception as e:
        print(f"Errore durante l'accesso a {event_url}: {e}")
        return None, None, "Unknown Match"

# Funzione per aggiornare il file M3U8
def update_m3u_file(video_streams, m3u_file="guardacalcio_playlist.m3u8"):
    REPO_PATH = os.getenv('GITHUB_WORKSPACE', '.')
    file_path = os.path.join(REPO_PATH, m3u_file)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        groups = {}
        for event_url, stream_url, element, channel_name in video_streams:
            if not stream_url:
                continue
            group = "Partite"
            
            if group not in groups:
                groups[group] = []
            groups[group].append((channel_name, stream_url))
            print(f"Aggiunto al file M3U8: {channel_name} -> {stream_url}")

        for group, channels in groups.items():
            channels.sort(key=lambda x: x[0].lower())
            for channel_name, link in channels:
                f.write(f"#EXTINF:-1 group-title=\"{group}\" tvg-logo=\"{DEFAULT_IMAGE_URL}\", {channel_name}\n")
                f.write(f"#EXTVLCOPT:http-user-agent={headers['User-Agent']}\n")
                f.write(f"#EXTVLCOPT:http-referrer={headers['Referer']}\n")
                f.write(f"{link}\n")
        
        f.write("\n")
        f.write(ADMIN_CHANNEL)

    print(f"File M3U8 aggiornato con successo: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        print("Contenuto del file M3U8:")
        print(f.read())

# Esegui lo script
if __name__ == "__main__":
    event_pages = find_event_pages()
    if not event_pages:
        print("Nessuna pagina evento trovata.")
    else:
        video_streams = []
        for event_url in event_pages:
            if any(x in event_url for x in ['tennis-streaming', 'wwe-streaming', 'rugby-streaming', 'pugilato-boxe-streaming', 'ufc-streaming', 'hockey-streaming', 'freccette-streaming']):
                print(f"Ignoro pagina con probabile 404: {event_url}")
                continue
            print(f"Analizzo: {event_url}")
            stream_url, element, channel_name = get_video_stream_and_description(event_url)
            if stream_url:
                video_streams.append((event_url, stream_url, element, channel_name))

        if video_streams:
            update_m3u_file(video_streams)
        else:
            print("Nessun flusso video trovato in tutte le pagine evento.")
            update_m3u_file([])
