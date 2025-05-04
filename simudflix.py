import cloudscraper
from bs4 import BeautifulSoup
import re
import json
import os

# Configurazioni
BASE_URL = "https://streamingcommunity.spa"
SEARCH_URL = f"{BASE_URL}/search"
OUTPUT_FILE = "streaming.m3u8"
DEBUG_DIR = "debug"
NETWORK_LOG = "network_requests.log"

# Lista dei 10 film Marvel
MARVEL_MOVIES = [
    {"title": "Iron Man", "year": 2008},
    {"title": "The Avengers", "year": 2012},
    {"title": "Captain America: The Winter Soldier", "year": 2014},
    {"title": "Guardians of the Galaxy", "year": 2014},
    {"title": "Avengers: Age of Ultron", "year": 2015},
    {"title": "Captain America: Civil War", "year": 2016},
    {"title": "Doctor Strange", "year": 2016},
    {"title": "Spider-Man: Homecoming", "year": 2017},
    {"title": "Black Panther", "year": 2018},
    {"title": "Avengers: Endgame", "year": 2019}
]

# Intestazioni per simulare un browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Referer": BASE_URL,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def setup_debug_dir():
    """Crea la directory di debug se non esiste."""
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR)

def log_network_request(url, status, content_length):
    """Registra le richieste di rete nel file di log."""
    with open(NETWORK_LOG, "a", encoding="utf-8") as f:
        f.write(f"URL: {url}, Status: {status}, Content-Length: {content_length}\n")

def fetch_title_url(title, year):
    """Cerca un film e restituisce l'URL della pagina del contenuto."""
    scraper = cloudscraper.create_scraper()
    query = f"{title} {year}"
    try:
        response = scraper.get(SEARCH_URL, params={"q": query}, headers=HEADERS)
        log_network_request(response.url, response.status_code, len(response.text))
        
        # Salva la pagina di ricerca per debug
        debug_file = os.path.join(DEBUG_DIR, f"search_{title.replace(' ', '_')}.html")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Prova diversi selettori per i risultati di ricerca
        selectors = [
            ".card a[href*='/watch/']",  # Esempio basato su struttura comune
            ".media a[href*='/watch/']",
            "a[href*='/watch/']",
            ".title a"  # Fallback generico
        ]
        for selector in selectors:
            result = soup.select_one(selector)
            if result and result["href"]:
                link = result["href"]
                if not link.startswith("http"):
                    link = BASE_URL + link
                print(f"Trovato URL per '{title}': {link}")
                return link
        
        print(f"Nessun risultato trovato per '{title}' con i selettori provati")
        return None
    except Exception as e:
        print(f"Errore nella ricerca di '{title} ({year})': {e}")
        return None

def extract_stream_url(page_url):
    """Estrae l'URL M3U8 dalla pagina del film."""
    scraper = cloudscraper.create_scraper()
    try:
        response = scraper.get(page_url, headers=HEADERS)
        log_network_request(response.url, response.status_code, len(response.text))
        
        # Salva la pagina del contenuto per debug
        debug_file = os.path.join(DEBUG_DIR, f"content_{page_url.split('/')[-1]}.html")
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Cerca negli script
        scripts = soup.select("script")
        for script in scripts:
            if script.string and "m3u8" in script.string:
                match = re.search(r'"(https?://[^"]+\.m3u8)"', script.string)
                if match:
                    print(f"Trovato M3U8 in script: {match.group(1)}")
                    return match.group(1)
        
        # Cerca un iframe del player
        iframe = soup.select_one("iframe[src*='player']")
        if iframe:
            iframe_url = iframe["src"]
            if not iframe_url.startswith("http"):
                iframe_url = BASE_URL + iframe_url
            iframe_response = scraper.get(iframe_url, headers=HEADERS)
            log_network_request(iframe_url, iframe_response.status_code, len(iframe_response.text))
            
            # Salva l'iframe per debug
            debug_file = os.path.join(DEBUG_DIR, f"iframe_{page_url.split('/')[-1]}.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(iframe_response.text)
            
            match = re.search(r'"(https?://[^"]+\.m3u8)"', iframe_response.text)
            if match:
                print(f"Trovato M3U8 in iframe: {match.group(1)}")
                return match.group(1)
        
        # Cerca un'API del player
        api_match = re.search(r'"playerApi":"(https?://[^"]+)"', response.text)
        if api_match:
            api_url = api_match.group(1)
            api_response = scraper.get(api_url, headers=HEADERS)
            log_network_request(api_url, api_response.status_code, len(api_response.text))
            try:
                api_data = api_response.json()
                m3u8_url = api_data.get("m3u8_url") or api_data.get("url")
                if m3u8_url and m3u8_url.endswith(".m3u8"):
                    print(f"Trovato M3U8 in API: {m3u8_url}")
                    return m3u8_url
            except json.JSONDecodeError:
                print(f"Risposta API non valida per {api_url}")
        
        print(f"Nessun M3U8 trovato per {page_url}")
        return None
    except Exception as e:
        print(f"Errore nell'estrazione del flusso per {page_url}: {e}")
        return None

def generate_m3u8():
    """Genera il file M3U8 con i flussi dei film Marvel."""
    setup_debug_dir()
    streams = []
    for movie in MARVEL_MOVIES:
        title = movie["title"]
        year = movie["year"]
        print(f"Cercando '{title} ({year})'...")
        page_url = fetch_title_url(title, year)
        if page_url:
            stream_url = extract_stream_url(page_url)
            if stream_url:
                streams.append((title, stream_url))
                print(f"Flusso trovato per '{title}'")
            else:
                print(f"Nessun flusso trovato per '{title}'")
        else:
            print(f"Film '{title}' non trovato")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, url in streams:
            f.write(f"#EXTINF:-1,{title}\n{url}\n")
    print(f"File {OUTPUT_FILE} generato con {len(streams)} flussi.")

def main():
    # Inizializza il file di log delle richieste
    if os.path.exists(NETWORK_LOG):
        os.remove(NETWORK_LOG)
    generate_m3u8()

if __name__ == "__main__":
    main()