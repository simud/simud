import os
import time
from scuapi import API
import cloudscraper
import requests

# Dominio corrente
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "streamingcommunity.spa")
BASE_URL = f"https://{BASE_DOMAIN}"

# Crea un'istanza dell'API
sc = API(BASE_DOMAIN)

# Funzione per verificare e ottenere un URL M3U8 valido
def get_valid_m3u_url(movie_id, sc, base_url):
    try:
        # Recupera i link M3U8
        _, m3u_url, _ = sc.get_links(movie_id, get_m3u=True)

        # Calcola il tempo di scadenza (1 ora)
        expires = int(time.time()) + 3600  # Imposta expires a 1 ora nel futuro

        # Modifica l'URL con un expires più lungo
        m3u_url = m3u_url.split('?')[0] + f"?expires={expires}&" + m3u_url.split('?')[1]

        # Headers per la richiesta
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": base_url,
            "Origin": base_url,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

        # Verifica la validità dell'URL
        scraper = cloudscraper.create_scraper()
        response = scraper.head(m3u_url, headers=headers, allow_redirects=True)

        if response.status_code == 200:
            print(f"URL valido: {m3u_url}")
            return m3u_url
        else:
            print(f"URL non valido per movie_id {movie_id}: {m3u_url} (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Errore nella verifica dell'URL per movie_id {movie_id}: {e}")
        return None

# Lista dei film da cercare
film_lista = [
    "Thunderbolts",
    "Iron Man 3",
    "Thor: Ragnarok",
    "Captain America: Civil War",
    "Black Panther: Wakanda Forever",
    "Spider-Man: No Way Home",
    "Doctor Strange nel Multiverso della Follia",
    "Avengers: Endgame",
    "Guardiani della Galassia Vol. 3",
    "The Marvels"
]

# Lista per le voci della playlist
playlist_entries = []

# Ciclo sui film
for film in film_lista:
    results = sc.search(film)
    match = next((k for k in results if film.lower() in k.lower()), None)
    if not match:
        print(f"Film non trovato: {film}")
        continue
    
    movie_id = results[match]["id"]
    
    try:
        # Ottieni il flusso valido per ogni film
        m3u_url = get_valid_m3u_url(movie_id, sc, BASE_URL)
        if not m3u_url:
            print(f"Impossibile ottenere un URL valido per {film}")
            continue
        
        # Definisce gli headers per la playlist M3U8
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ref_and_origin = BASE_URL
        
        # Aggiungi la voce alla playlist M3U8
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