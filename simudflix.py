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

m3u_entries = []

# Funzione per ottenere l'URL del flusso M3U8 dalla pagina di watch
def get_m3u8_url(movie_id):
    watch_url = f"https://streamingcommunity.spa/watch/{movie_id}"
    try:
        # Richiesta per ottenere il contenuto della pagina di watch
        response = requests.get(watch_url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Cerca l'URL del flusso M3U8 nel contenuto della pagina
            # (L'URL m3u8 potrebbe essere trovato in un oggetto JSON o come parte di un iframe)
            # Qui bisogna cercare nel contenuto per un tag <script>, <iframe> o simili
            scripts = soup.find_all('script')
            
            for script in scripts:
                if 'm3u8' in script.text:
                    # Estrai il link m3u8 dal contenuto del tag script (se presente)
                    # Questo è un esempio generico e potrebbe dover essere raffinato a seconda della struttura della pagina
                    start_index = script.text.find("m3u8")
                    end_index = script.text.find(".m3u8", start_index) + len(".m3u8")
                    m3u8_url = script.text[start_index:end_index]
                    return m3u8_url

            print(f"Flusso M3U8 non trovato per l'ID {movie_id} nella pagina.")
        else:
            print(f"Errore nel caricare la pagina per l'ID {movie_id}: {response.status_code}")
    
    except Exception as e:
        print(f"Errore durante l'elaborazione di {movie_id}: {e}")
    
    return None

# Itera sulla lista dei film e cerca i flussi M3U8
for title, movie_id in marvel_movies.items():
    m3u8_url = get_m3u8_url(movie_id)
    if m3u8_url:
        m3u_entries.append(f"#EXTINF:-1,{title}\n{m3u8_url}")

# Scrittura del file .m3u8
with open("streaming.m3u8", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    f.write("\n".join(m3u_entries))

print("File streaming.m3u8 creato con successo.")