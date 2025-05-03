import os
from scuapi import API
import requests
import cloudscraper
import time

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "streamingcommunity.spa")
BASE_URL = f"https://{BASE_DOMAIN}"
sc = API(BASE_DOMAIN)

def get_valid_m3u_url(movie_id, sc, base_url):
    try:
        # Richiedi un nuovo link M3U8 per ogni film
        _, m3u_url, _ = sc.get_links(movie_id, get_m3u=True)
        
        if not m3u_url:
            print(f"Nessun flusso M3U8 trovato per {movie_id}")
            return None
        
        # Estrai i parametri dalla URL M3U8 per analizzare expires e token
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(m3u_url)
        query_params = parse_qs(parsed_url.query)
        
        expires = int(query_params.get('expires', [0])[0])
        current_time = int(time.time())  # Ottieni l'ora attuale in secondi
        
        # Verifica se il flusso è scaduto
        if expires <= current_time:
            print(f"Flusso scaduto per {movie_id}. Genera un nuovo flusso.")
            return None  # Il flusso è scaduto, quindi non restituirlo
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": base_url,
            "Origin": base_url,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
        
        # Scraping del flusso con cloudscraper
        scraper = cloudscraper.create_scraper()
        response = scraper.head(m3u_url, headers=headers, allow_redirects=True)
        
        if response.status_code == 200:
            print(f"URL valido per {movie_id}: {m3u_url}")
            return m3u_url
        else:
            print(f"URL non valido per {movie_id}: {m3u_url} (Status: {response.status_code})")
            return None
        
    except Exception as e:
        print(f"Errore per {movie_id}: {e}")
        return None

# Lista dei film da cercare
film_lista = [
    "Thunderbolts", "Iron Man 3", "Thor: Ragnarok", "Captain America: Civil War",
    "Black Panther: Wakanda Forever", "Spider-Man: No Way Home",
    "Doctor Strange nel Multiverso della Follia", "Avengers: Endgame",
    "Guardiani della Galassia Vol. 3", "The Marvels"
]

playlist_entries = []

for film in film_lista:
    results = sc.search(film)
    match = next((k for k in results if film.lower() in k.lower()), None)
    
    if not match:
        print(f"Film non trovato: {film}")
        continue
    
    movie_id = results[match]["id"]
    
    try:
        m3u_url = get_valid_m3u_url(movie_id, sc, BASE_URL)
        
        if not m3u_url:
            print(f"Impossibile ottenere un URL valido per {film}")
            continue
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ref_and_origin = BASE_URL
        
        playlist_entries.append(
            f'#EXTINF:-1,{match}\n'
            f'#EXTVLCOPT:http-referrer={ref_and_origin}\n'
            f'#EXTVLCOPT:http-origin={ref_and_origin}\n'
            f'#EXTVLCOPT:http-user-agent={user_agent}\n'
            f'{m3u_url}\n'
        )
        print(f"Aggiunto: {match}")
    
    except Exception as e:
        print(f"Errore per {film}: {e}")

# Scrive l'intera playlist in un unico file .m3u8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(playlist_entries))

print("File streaming.m3u8 generato correttamente.")