import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
}

m3u_entries = []
base_url = "https://streamingcommunity.spa"

def get_movie_id(title):
    """Cerca l'ID del film/serie tramite il motore di ricerca."""
    try:
        # Codifica il titolo per l'URL
        encoded_title = urllib.parse.quote(title)
        search_url = f"{base_url}/search?q={encoded_title}"
        res = requests.get(search_url, headers=headers, timeout=10)
        
        if res.status_code != 200:
            print(f"Errore nella ricerca per '{title}': Stato HTTP {res.status_code}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        # Trova il primo risultato della ricerca
        result = soup.select_one("a.title[href*='/watch/']")
        if not result:
            print(f"Nessun risultato trovato per '{title}'")
            return None

        # Estrai l'ID dall'URL (es. /watch/123)
        href = result['href']
        movie_id = href.split('/')[-1]
        if movie_id.isdigit():
            return movie_id
        else:
            print(f"ID non valido per '{title}'")
            return None

    except Exception as e:
        print(f"Errore nella ricerca per '{title}': {e}")
        return None

def get_m3u8_url(movie_id, title):
    """Estrae il link M3U8 dalla pagina del film/serie."""
    try:
        url = f"{base_url}/watch/{movie_id}"
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code != 200:
            print(f"Errore nel caricare la pagina per '{title}' (ID: {movie_id}): Stato HTTP {res.status_code}")
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        scripts = soup.find_all("script")

        for script in scripts:
            if script.string and ".m3u8" in script.string:
                start = script.string.find("https")
                end = script.string.find(".m3u8", start)
                if start != -1 and end != -1:
                    m3u_url = script.string[start:end + 5]
                    return m3u_url
        print(f"Flusso M3U8 non trovato per '{title}' (ID: {movie_id})")
        return None

    except Exception as e:
        print(f"Errore nel recuperare M3U8 per '{title}' (ID: {movie_id}): {e}")
        return None

# Iterazione sui titoli
for title in movies:
    print(f"Elaborazione: {title}")
    movie_id = get_movie_id(title)
    if movie_id:
        m3u_url = get_m3u8_url(movie_id, title)
        if m3u_url:
            m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u_url}")
    # Pausa per evitare sovraccarico al server
    time.sleep(1)

# Scrittura del file M3U8
if m3u_entries:
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(m3u_entries))
    print("File streaming.m3u8 creato con successo.")
else:
    print("Nessun flusso M3U8 trovato. File non creato.")