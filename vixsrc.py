import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
import re
import os
import time
import urllib.parse
import pickle

# Configurazioni
TMDB_API_KEY = "eff30813a2950a33e36b51ff09c71f97"  # Chiave API TMDb
BASE_URL = "https://api.themoviedb.org/3"
NUMERO_FILM_PER_GRUPPO = 10  # Film per categoria e per "Film al Cinema"
OUTPUT_FILE = "film.m3u8"  # Nome del file M3U8
VIX_ORIGIN = "https://vixsrc.to/"  # Origin e Referrer
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"  # Base URL per le immagini
MAX_RETRIES = 3  # Numero massimo di tentativi per richiesta
RETRY_DELAY = 5  # Secondi di attesa tra i tentativi
DEBUG_DIR = "debug_pages"  # Directory per salvare le pagine di debug
CACHE_FILE = "movie_cache.pkl"  # File per la cache
PROCESSED_IDS_FILE = "processed_ids.pkl"  # File per tracciare gli ID processati

# Crea la directory di debug se non esiste
if not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR)

# Funzione per ottenere i film più recenti
def get_recent_movies(limit, processed_ids):
    print("Recupero dei film più recenti...")
    movies = []
    page = 1
    while len(movies) < limit:
        url = f"{BASE_URL}/movie/now_playing?api_key={TMDB_API_KEY}&language=it-IT&sort_by=release_date.desc&page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Errore nella richiesta dei film (pagina {page}): {response.status_code}")
            break
        results = response.json().get("results", [])
        if not results:
            break
        for movie in results:
            if movie["id"] not in processed_ids and len(movies) < limit:
                movies.append(movie)
                processed_ids.add(movie["id"])
        page += 1
        time.sleep(0.5)  # Evita ban da TMDb
    print(f"Trovati {len(movies)} film recenti")
    return movies

# Funzione per ottenere i film per genere
def get_movies_by_genre(genre_id, limit, processed_ids):
    print(f"Recupero dei film per il genere ID {genre_id}...")
    movies = []
    page = 1
    while len(movies) < limit:
        url = f"{BASE_URL}/discover/movie?api_key={TMDB_API_KEY}&language=it-IT&sort_by=popularity.desc&with_genres={genre_id}&page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Errore nella richiesta dei film per il genere {genre_id} (pagina {page}): {response.status_code}")
            break
        results = response.json().get("results", [])
        if not results:
            break
        for movie in results:
            if movie["id"] not in processed_ids and len(movies) < limit:
                movies.append(movie)
                processed_ids.add(movie["id"])
        page += 1
        time.sleep(0.5)  # Evita ban da TMDb
    print(f"Trovati {len(movies)} film per il genere ID {genre_id}")
    return movies

# Funzione per ottenere l'elenco dei generi
def get_genres():
    print("Recupero dell'elenco dei generi...")
    url = f"{BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language=it-IT"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Errore nel recupero dei generi: {response.status_code}")
        return []
    genres = response.json().get("genres", [])
    print(f"Trovati {len(genres)} generi")
    return genres

# Funzione per preprocessare la stringa JSON
def preprocess_json(json_str):
    json_str = json_str.strip()
    json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
    json_str = re.sub(r'\bparams\b:', '"params":', json_str)
    json_str = re.sub(r'\burl\b:', '"url":', json_str)
    json_str = re.sub(r'\btoken\b:', '"token":', json_str)
    json_str = re.sub(r'\bexpires\b:', '"expires":', json_str)
    json_str = re.sub(r'\basn\b:', '"asn":', json_str)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r'[\x00-\x1F\x7F]', '', json_str)
    return json_str

# Funzione per validare token ed expires
def validate_token_and_expires(token, expires):
    if not token or not expires:
        return False
    if not re.match(r'^[a-f0-9]{32}$', token):
        return False
    try:
        expires_int = int(expires)
        current_time = int(time.time())
        if expires_int <= current_time:
            return False
    except ValueError:
        return False
    return True

# Funzione per cercare un film su vixsrc.to
def search_vixsrc(title, scraper):
    print(f"Ricerco '{title}' su vixsrc.to...")
    search_url = f"{VIX_ORIGIN}search?query={urllib.parse.quote(title)}"
    try:
        response = scraper.get(search_url)
        if response.status_code != 200:
            print(f"Errore nella ricerca per '{title}': {response.status_code}")
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('a', class_='film-poster')
        for result in results:
            href = result.get('href', '')
            if '/movie/' in href:
                movie_id = href.split('/')[-1]
                return movie_id
        print(f"Nessun risultato trovato per '{title}'")
        return None
    except Exception as e:
        print(f"Errore nella ricerca per '{title}': {str(e)}")
        return None

# Funzione per testare il flusso
def test_stream_url(stream_url, scraper):
    try:
        response = scraper.get(stream_url, timeout=10, headers={
            'Referer': VIX_ORIGIN,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Origin': VIX_ORIGIN
        })
        return response.status_code == 200
    except Exception as e:
        print(f"Errore nel test del flusso {stream_url}: {str(e)}")
        return False

# Funzione per estrarre il flusso finale
def get_stream_url(tmdb_id, title, cache, scraper):
    if tmdb_id in cache:
        return cache[tmdb_id]

    url = f"{VIX_ORIGIN}movie/{tmdb_id}"
    print(f"Accesso alla pagina {url} con Cloudscraper per {title}...")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = scraper.get(url, headers={
                'Referer': VIX_ORIGIN,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Origin': VIX_ORIGIN
            })
            if response.status_code != 200:
                print(f"Errore nell'accesso alla pagina {url}: {response.status_code}")
                if response.status_code == 404:
                    vix_id = search_vixsrc(title, scraper)
                    if vix_id:
                        url = f"{VIX_ORIGIN}movie/{vix_id}"
                        print(f"Tentativo con ID interno {vix_id}: {url}")
                        response = scraper.get(url)
                        if response.status_code != 200:
                            debug_file = os.path.join(DEBUG_DIR, f"movie_{tmdb_id}_error.html")
                            with open(debug_file, "w", encoding="utf-8") as f:
                                f.write(response.text)
                            print(f"Pagina di errore salvata: {debug_file}")
                            cache[tmdb_id] = (None, f"Errore: pagina non trovata (HTTP 404)")
                            return None, f"Errore: pagina non trovata (HTTP 404)"
                    else:
                        cache[tmdb_id] = (None, f"Errore: pagina non trovata (HTTP 404)")
                        return None, f"Errore: pagina non trovata (HTTP 404)"
                time.sleep(RETRY_DELAY)
                continue

            debug_file = os.path.join(DEBUG_DIR, f"movie_{tmdb_id}.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Pagina salvata in {debug_file}")

            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')

            video_id = None
            stream_params = None
            for script in scripts:
                script_content = script.string
                if script_content:
                    video_match = re.search(r'window\.video\s*=\s*({.*?});', script_content, re.DOTALL)
                    if video_match:
                        try:
                            video_data = json.loads(video_match.group(1))
                            video_id = video_data.get('id')
                            print(f"Trovato ID interno: {video_id}")
                        except json.JSONDecodeError as e:
                            print(f"Errore nel decodificare window.video per {url}: {str(e)}")

                    streams_match = re.search(r'window\.streams\s*=\s*(\[.*?\]);', script_content, re.DOTALL)
                    if streams_match:
                        try:
                            streams_data = json.loads(streams_match.group(1))
                            for stream in streams_data:
                                if stream.get('active', False):
                                    stream_params = stream.get('url', '')
                                    print(f"Trovato stream attivo: {stream_params}")
                                    break
                        except json.JSONDecodeError as e:
                            print(f"Errore nel decodificare window.streams per {url}: {str(e)}")

                    if 'window.masterPlaylist' in script_content:
                        print(f"Trovato script con window.masterPlaylist:\n{script_content}")
                        match = re.search(r'window\.masterPlaylist\s*=\s*(\{.*?\}(?=\s*window\.canPlayFHD|\s*<\/script>))', script_content, re.DOTALL)
                        if match:
                            try:
                                json_str = match.group(1)
                                print(f"Stringa JSON grezza:\n{json_str}")
                                json_str = preprocess_json(json_str)
                                print(f"Stringa JSON preprocessata:\n{json_str}")
                                json_debug_file = os.path.join(DEBUG_DIR, f"movie_{tmdb_id}_json.txt")
                                with open(json_debug_file, "w", encoding="utf-8") as f:
                                    f.write(json_str)
                                print(f"Stringa JSON preprocessata salvata in {json_debug_file}")
                                master_playlist = json.loads(json_str)
                                params = master_playlist.get('params', {})
                                base_url = master_playlist.get('url', '')
                                token = params.get('token', '')
                                expires = params.get('expires', '')

                                if validate_token_and_expires(token, expires):
                                    if stream_params:
                                        base_url = stream_params
                                    elif 'b=1' not in base_url:
                                        base_url = base_url + ('?b=1' if '?' not in base_url else '&b=1')
                                    stream_url = f"{base_url}&token={token}&expires={expires}&h=1&lang=it"
                                    if test_stream_url(stream_url, scraper):
                                        print(f"Flusso finale creato: {stream_url}")
                                        cache[tmdb_id] = (stream_url, None)
                                        return stream_url, None
                                    else:
                                        print(f"Flusso non accessibile: {stream_url}")
                                        cache[tmdb_id] = (None, "Errore: flusso non accessibile")
                                        return None, "Errore: flusso non accessibile"
                                else:
                                    print(f"Token o expires non validi per {url}: token={token}, expires={expires}")
                                    cache[tmdb_id] = (None, "Errore: token o expires non validi")
                                    return None, "Errore: token o expires non validi"
                            except json.JSONDecodeError as e:
                                print(f"Errore nel decodificare il JSON per {url}: {str(e)}")
                                cache[tmdb_id] = (None, f"Errore: JSON non valido ({str(e)})")
                                return None, f"Errore: JSON non valido ({str(e)})"
                        else:
                            print(f"Regex non ha trovato window.masterPlaylist per {url}")
                            cache[tmdb_id] = (None, "Errore: window.masterPlaylist non trovato")
                            return None, "Errore: window.masterPlaylist non trovato"
            
            print(f"window.masterPlaylist non trovato per {url}")
            cache[tmdb_id] = (None, "Errore: window.masterPlaylist non trovato")
            return None, "Errore: window.masterPlaylist non trovato"
        
        except Exception as e:
            print(f"Errore durante l'accesso a {url} (tentativo {attempt + 1}/{MAX_RETRIES}): {str(e)}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                cache[tmdb_id] = (None, f"Errore: {str(e)}")
                return None, f"Errore: {str(e)}"
    
    cache[tmdb_id] = (None, "Errore: tentativi massimi raggiunti")
    return None, "Errore: tentativi massimi raggiunti"

# Funzione per creare il file M3U8
def create_m3u8_playlist(movies_by_group):
    print(f"Creazione del file M3U8: {OUTPUT_FILE}")
    cache = load_cache()
    scraper = cloudscraper.create_scraper(
        delay=20,
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for group_name, movies in movies_by_group.items():
            print(f"Aggiunta dei film al gruppo '{group_name}'...")
            for movie in movies:
                title = movie.get("title", "Senza Titolo")
                tmdb_id = movie.get("id", "")
                poster_path = movie.get("poster_path", "")
                stream_url, error_message = get_stream_url(tmdb_id, title, cache, scraper)
                img_url = f"{IMG_BASE_URL}{poster_path}" if poster_path else ""

                if stream_url:
                    f.write(f'#EXTINF:-1 tvg-id="{tmdb_id}" tvg-name="{title}" tvg-logo="{img_url}" group-title="{group_name}",{title}\n')
                    f.write(f'#EXTVLCOPT:http-referrer={VIX_ORIGIN}\n')
                    f.write(f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n')
                    f.write(f'#EXTVLCOPT:http-origin={VIX_ORIGIN}\n')
                    f.write(f'{stream_url}\n')
                    print(f"Aggiunto film: {title}")
                else:
                    print(f"Salta film: {title} ({error_message})")
                    f.write(f'#EXTINF:0 tvg-name="Errore" group-title="Debug",Errore per {title}\n')
                    f.write(f'# {error_message}\n')
                
                save_cache(cache)  # Salva la cache dopo ogni film

    print(f"Playlist M3U8 creata con successo: {OUTPUT_FILE}")

# Funzioni per gestire la cache e gli ID processati
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

def load_processed_ids():
    if os.path.exists(PROCESSED_IDS_FILE):
        with open(PROCESSED_IDS_FILE, 'rb') as f:
            return pickle.load(f)
    return set()

def save_processed_ids(processed_ids):
    with open(PROCESSED_IDS_FILE, 'wb') as f:
        pickle.dump(processed_ids, f)

# Funzione principale
def main():
    print("Avvio dello script per la creazione della playlist M3U8...")
    processed_ids = load_processed_ids()
    movies_by_group = {}

    # Ottieni i film recenti
    recent_movies = get_recent_movies(NUMERO_FILM_PER_GRUPPO, processed_ids)
    movies_by_group["Film al Cinema"] = recent_movies

    # Ottieni i generi e i film per ogni genere
    genres = get_genres()
    for genre in genres:
        genre_name = genre["name"]
        genre_id = genre["id"]
        genre_movies = get_movies_by_genre(genre_id, NUMERO_FILM_PER_GRUPPO, processed_ids)
        movies_by_group[genre_name] = genre_movies

    save_processed_ids(processed_ids)
    create_m3u8_playlist(movies_by_group)

if __name__ == "__main__":
    main()
