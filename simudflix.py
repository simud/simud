import os
import time
from scuapi import API
import requests
import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

# Dominio corrente
BASE_DOMAIN = os.getenv("BASE_DOMAIN", "streamingcommunity.spa")
BASE_URL = f"https://{BASE_DOMAIN}"
sc = API(BASE_DOMAIN)

# Funzione per ottenere URL M3U8 con cloudscraper e gestione cookie
def get_valid_m3u_url(movie_id, sc, base_url):
    try:
        # Inizializza una sessione con cloudscraper
        scraper = cloudscraper.create_scraper()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": base_url,
            "Origin": base_url,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }
        
        # Effettua una richiesta preliminare per ottenere cookie
        print(f"Caricamento pagina iniziale per cookie: {base_url}/watch/{movie_id}")
        response = scraper.get(f"{base_url}/watch/{movie_id}", headers=headers)
        if response.status_code != 200:
            print(f"Errore caricamento pagina iniziale: Status {response.status_code}")
            return None
        
        # Estrai l'URL M3U8
        _, m3u_url, _ = sc.get_links(movie_id, get_m3u=True)
        print(f"URL M3U8 generato: {m3u_url}")
        
        # Verifica la validità dell'URL
        response = scraper.head(m3u_url, headers=headers, allow_redirects=True)
        if response.status_code == 200:
            print(f"URL valido (cloudscraper): {m3u_url}")
            return m3u_url
        else:
            print(f"URL non valido per movie_id {movie_id}: {m3u_url} (Status: {response.status_code})")
            return None
    except Exception as e:
        print(f"Errore con cloudscraper per movie_id {movie_id}: {e}")
        return None

# Funzione per ottenere URL M3U8 con Selenium (fallback)
def get_m3u_url_selenium(movie_id, base_url):
    try:
        print(f"Tentativo con Selenium per movie_id {movie_id}")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        driver = uc.Chrome(options=options)
        
        # Naviga alla pagina del film
        watch_url = f"{base_url}/watch/{movie_id}"
        print(f"Navigazione a: {watch_url}")
        driver.get(watch_url)
        time.sleep(8)  # Attendi caricamento completo
        
        # Cerca l'elemento video
        video_elements = driver.find_elements(By.TAG_NAME, "video")
        for video in video_elements:
            src = video.get_attribute("src")
            if src and ".m3u8" in src:
                print(f"URL M3U8 trovato nel tag video: {src}")
                driver.quit()
                return src
        
        # Cerca nelle richieste di rete
        for request in driver.requests:
            if ".m3u8" in request.url:
                print(f"URL M3U8 trovato nelle richieste di rete: {request.url}")
                driver.quit()
                return request.url
        
        print("Nessun URL M3U8 trovato con Selenium")
        driver.quit()
        return None
    except Exception as e:
        print(f"Errore con Selenium per movie_id {movie_id}: {e}")
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

playlist_entries = []

for film in film_lista:
    results = sc.search(film)
    match = next((k for k in results if film.lower() in k.lower()), None)
    if not match:
        print(f"Film non trovato: {film}")
        continue

    movie_id = results[match]["id"]

    try:
        # Prova prima con cloudscraper
        m3u_url = get_valid_m3u_url(movie_id, sc, BASE_URL)
        # Se cloudscraper fallisce, usa Selenium
        if not m3u_url:
            m3u_url = get_m3u_url_selenium(movie_id, BASE_URL)
        
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