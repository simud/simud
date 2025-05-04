import requests
from bs4 import BeautifulSoup

# Lista di film Marvel con i rispettivi ID
marvel_movies = {
    "Iron Man": 312,
    "Iron Man 2": 313,
    "Iron Man 3": 314,
    "Thor": 317,
    "Captain America: The First Avenger": 316,
    "The Avengers": 315,
    "Guardians of the Galaxy": 320,
    "Doctor Strange": 322,
    "Black Panther": 325,
    "Avengers: Endgame": 328
}

# Lista per memorizzare le voci M3U
m3u_entries = []

# Funzione per estrarre l'URL M3U8 dalla pagina di visione
def get_m3u8_url(movie_id):
    url = f"https://streamingcommunity.spa/watch/{movie_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Troviamo il flusso M3U8 nella pagina, supponendo che sia nel tag <video> o simile
        video_tag = soup.find('video')
        if video_tag and 'src' in video_tag.attrs:
            return video_tag.attrs['src']
    return None

# Elaboriamo i film
for title, movie_id in marvel_movies.items():
    try:
        # Ottieni l'URL M3U8 dalla pagina di visione
        m3u8_url = get_m3u8_url(movie_id)
        if m3u8_url:
            m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u8_url}")
        else:
            print(f"Nessun flusso M3U8 trovato per {title}")
    except Exception as e:
        print(f"Errore durante l'elaborazione di {title}: {e}")

# Scrittura del file .m3u8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(m3u_entries))

print("File streaming.m3u8 creato con successo.")