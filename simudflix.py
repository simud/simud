import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import logging
import random

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lista dei titoli di film/serie
movies = [
    "Iron Man",
    "Iron Man 2",
    "Iron Man 3",
    "The Avengers",
    "Captain America: The First Avenger",
    "Thor",
    "Guardians of the Galaxy",
    "Doctor Strange",
    "Black Panther",
    "Avengers: Endgame"
]

# Dizionario per titoli alternativi (in italiano)
alternative_titles = {
    "Iron Man": "Uomo di Ferro",
    "Iron Man 2": "Uomo di Ferro 2",
    "Iron Man 3": "Uomo di Ferro 3",
    "The Avengers": "I Vendicatori",
    "Captain America: The First Avenger": "Capitan America: Il primo Vendicatore",
    "Thor": "Thor",
    "Guardians of the Galaxy": "Guardiani della Galassia",
    "Doctor Strange": "Dottor Strange",
    "Black Panther": "Black Panther",
    "Avengers: Endgame": "Avengers: Fine del gioco"
}

# Lista di User-Agent per rotazione
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
]

headers = {
    "User-Agent": random.choice(user_agents),
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

m3u_entries = []
base_url = "https://streamingcommunity.spa"
MAX_RETRIES = 3
TIMEOUT = 10
REQUEST_DELAY = 1

def get_movie_id(title):
    """Cerca l'ID del film/serie tramite il motore di ricerca."""
    titles_to_try = [title, alternative_titles.get(title, title)]
    
    for search_title in titles_to_try:
        for attempt in range(MAX_RETRIES):
            try:
                headers["User-Agent"] = random.choice(user_agents)  # Ruota User-Agent
                encoded_title = urllib.parse.quote(search_title)
                search_url = f"{base_url}/search?q={encoded_title}"
                logging.info(f"Ricerco: {search_url}")
                res = requests.get(search_url, headers=headers, timeout=TIMEOUT)
                
                if res.status_code != 200:
                    logging.error(f"Errore HTTP per '{search_title}': Stato {res.status_code}")
                    time.sleep(REQUEST_DELAY)
                    continue

                # Controlla se la risposta è una pagina di verifica Cloudflare
                if "cf-browser-verification" in res.text or "Checking your browser" in res.text:
                    logging.error(f"Pagina di verifica Cloudflare rilevata per '{search_title}'")
                    return None

                soup = BeautifulSoup(res.text, "html.parser")
                # Cerca un link che contenga '/watch/'
                result = soup.select_one("a[href*='/watch/']")
                if not result:
                    logging.warning(f"Nessun risultato trovato per '{search_title}'. HTML: {res.text[:1000]}...")
                    break

                # Estrai l'ID dall'URL (es. /watch/10002)
                href = result['href']
                movie_id = href.split('/')[-1]
                if movie_id.isdigit():
                    logging.info(f"Trovato ID {movie_id} per '{title}' (cercato come '{search_title}')")
                    return movie_id
                else:
                    logging.error(f"ID non valido per '{search_title}': {movie_id}")
                    break

            except Exception as e:
                logging.error(f"Errore nella ricerca per '{search_title}' (tentativo {attempt + 1}/{MAX_RETRIES}): {e}")
                time.sleep(REQUEST_DELAY)
    
    logging.error(f"Impossibile trovare ID per '{title}' dopo {MAX_RETRIES} tentativi")
    return None

def get_m3u8_url(movie_id, title):
    """Estrae il link M3U8 dalla pagina del film/serie."""
    for attempt in range(MAX_RETRIES):
        try:
            headers["User-Agent"] = random.choice(user_agents)
            url = f"{base_url}/watch/{movie_id}"
            logging.info(f"Recupero M3U8 da: {url}")
            res = requests.get(url, headers=headers, timeout=TIMEOUT)
            
            if res.status_code != 200:
                logging.error(f"Errore nel caricare la pagina per '{title}' (ID: {movie_id}): Stato HTTP {res.status_code}")
                time.sleep(REQUEST_DELAY)
                continue

            if "cf-browser-verification" in res.text or "Checking your browser" in res.text:
                logging.error(f"Pagina di verifica Cloudflare rilevata per '{title}' (ID: {movie_id})")
                return None

            soup = BeautifulSoup(res.text, "html.parser")
            scripts = soup.find_all("script")

            for script in scripts:
                if script.string and ".m3u8" in script.string:
                    start = script.string.find("https")
                    end = script.string.find(".m3u8", start)
                    if start != -1 and end != -1:
                        m3u_url = script.string[start:end + 5]
                        logging.info(f"Trovato M3U8 per '{title}' (ID: {movie_id})")
                        return m3u_url
            logging.warning(f"Flusso M3U8 non trovato per '{title}' (ID: {movie_id})")
            return None

        except Exception as e:
            logging.error(f"Errore nel recuperare M3U8 per '{title}' (ID: {movie_id}, tentativo {attempt + 1}/{MAX_RETRIES}): {e}")
            time.sleep(REQUEST_DELAY)
    
    logging.error(f"Impossibile trovare M3U8 per '{title}' (ID: {movie_id}) dopo {MAX_RETRIES} tentativi")
    return None

# Iterazione sui titoli
for title in movies:
    logging.info(f"Elaborazione: {title}")
    movie_id = get_movie_id(title)
    if movie_id:
        m3u_url = get_m3u8_url(movie_id, title)
        if m3u_url:
            m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u_url}")
    time.sleep(REQUEST_DELAY)

# Scrittura del file M3U8
if m3u_entries:
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(m3u_entries))
    logging.info("File streaming.m3u8 creato con successo.")
else:
    logging.warning("Nessun flusso M3U8 trovato. File non creato.")